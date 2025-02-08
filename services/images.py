import os
import sys
import json
import requests
from config.log_settings import LoggingCls
from config.setting import CONFIG
import traceback
import subprocess
import utils.utils as utils
import uuid
import re

logger = LoggingCls.get_logger()


def natural_sort_key(filename):
    """提取文件名中的数字部分并返回整数值"""
    match = re.search(r'part_(\d+)', filename)
    return int(match.group(1)) if match else float('inf')  # 以防没有匹配项
def gen_token():
    return "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJkaXNpZmFuc2hpIiwiaWF0IjoxNzM4OTc4OTY4LCJ1c2VySWQiOiIxMDIzNCIsIm5hbWUiOiLnrKzlm5vojIPlvI8ifQ.YGevws3FO7PxqgrEfv2soNorPrO57M6VWnlx1bYX-WriOAAMEiMd-W8unyxVA6fw-SF_XHVfzE-pCxheQcxjcqd9YttvXjsFXOahgKRyS4TxRr1lsSQnvZqttx82vzNKWmnWC8WtTxt2_VuIOqMCgpotVIMoWV_7NE6_QygwqL0"


#镜像推送类的实现
class ImagesPushImpl:
    @classmethod
    def push(cls,push_id):
        try:
            #生成镜像
            generate_images_command = f"cd package/images_push/ && chmod +x generate.sh && ./generate.sh"
            logger.info("开始生成镜像..")
            subprocess.run(generate_images_command, shell=True, check=True, capture_output=True, text=True)

            #导出镜像
            image_name = "template_v1.0"
            output_path = f"{CONFIG['export_file_path']}/images/{push_id}"
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
                output_path = os.path.join(base_path, output_path)
            
            os.makedirs(output_path, exist_ok=True)
            output_file = f"{output_path}/{image_name}.tar"
            result = subprocess.run(
                ["docker", "images", "-q", image_name], 
                capture_output=True, text=True, check=True
            )
            if result.stdout.strip():
                print(f"镜像 {image_name} 存在，ID: {result.stdout.strip()}")
                subprocess.run(
                    ["docker", "save", "-o", output_file, image_name], 
                    check=True
                )
                print(f"镜像 {image_name} 已成功导出为 {output_file}")
            else:
                print(f"镜像 {image_name} 不存在")

            output_dir = f"{output_path}_chunks"  # 输出文件夹
            os.makedirs(output_dir, exist_ok=True)  # 创建存放分片的目录
            if os.path.exists(output_dir):
                os.system(f"rm -rf {output_dir}/*")
            #文件切片
            fs_split_msg = cls.file_split(output_file,output_dir)
            if fs_split_msg is None:
                raise Exception("文件切片失败！")
            #上传分片
            chunk_info = cls.upload_chunk(output_dir,fs_split_msg,push_id)  
            if chunk_info is None:
                raise Exception("上传分片失败！")
            business_name = os.path.basename(output_file)
            import_image = cls.import_image(business_name,chunk_info,push_id) 
            if import_image is None:
                raise Exception("导入镜像失败！")
            #更新镜像推送状态
            logger.info("更新镜像推送状态..")
            cls.update_push_status(push_id,1)

        except Exception as e:     
            logger.error(f"镜像推送失败，错误信息：{str(e)}")
            cls.update_push_status(push_id,0)
            return
        
    @classmethod
    def update_push_status(cls,push_id,status):
        try:
            #更新镜像推送状态
            logger.info("更新镜像推送状态..")
            data = {
                "template_id":push_id,
                "status":status
            }
            res = requests.post(url=CONFIG["images_push_url"],data=json.dumps(data))
            if res.status_code != 200:
                raise Exception(f"请求接口时出错，code:{res.status_code}")
            
            logger.info("更新镜像推送状态成功..")
        except Exception as e:     
            logger.error(f"更新镜像推送状态失败，错误信息：{str(e)}")
            return
        
    @classmethod    
    def file_split(cls,file_path,output_dir,chunk_size=10 * 1024 * 1024):
        try:
            """ 将大文件拆分为多个小文件，每片大小为 chunk_size 字节 """
            if not os.path.exists(file_path):
                print(f"文件 {file_path} 不存在！")
                return None
            #获取文件名
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)  # 获取文件大小
            part_num = 1  # 分片编号
            logger.info("开始文件分割..")
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)  # 读取 chunk_size 大小的数据
                    if not chunk:
                        break  # 读完文件退出
                    
                    part_file = os.path.join(output_dir, f"chunk_file_part_{part_num}.tar")
                    with open(part_file, "wb") as part:
                        part.write(chunk)
                    logger.info(f"生成分片: {part_file} (大小: {len(chunk)} bytes)")
                    part_num += 1

            logger.info(f"文件切片完成，共 {part_num-1} 片，存放于: {output_dir}")
            fs_split_msg = {}
            fs_split_msg["identifier"] = utils.get_md5(file_path)
            fs_split_msg["totalSize"] = file_size
            fs_split_msg["originalName"] = file_name
            fs_split_msg["fileSystem"] = "0"
            fs_split_msg["relativePath"] = file_name
            fs_split_msg["totalChunks"] = part_num-1
            fs_split_msg["chunkSize"] = 10
            fs_split_msg["uuid"] = uuid.uuid4()
            fs_split_msg["fileCategory"] = ".tar"
            return fs_split_msg
        except Exception as e:     
            logger.error(f"文件分割失败，错误信息：{str(e)}")
            return None
        
    @classmethod
    def upload_chunk(cls,output_dir,fs_split_msg,push_id):
        try:
            fs_chunk_upload_url = "http://10.180.24.238:9555/fs/manager/chunk-upload"
            #上传分片
            result = None
            logger.info("开始上传分片..")
            part_num = 1
            files = os.listdir(output_dir)
            sorted_files = sorted(files, key=natural_sort_key)
            header = {"token":gen_token()}
            for file in sorted_files:
                file_path = os.path.join(output_dir, file)
                file_size = os.path.getsize(file_path) 
                fs_split_msg["currentChunkSize"] = file_size
                fs_split_msg["chunkNumber"] = part_num
                with open(file_path, "rb") as f:
                    files = {"fileChunk": (file_path, f, "application/octet-stream")}  # 文件部分
                    res = requests.post(url=fs_chunk_upload_url,headers=header,files=files,data=fs_split_msg)  # 发送 POST 请求
                    if res.status_code != 200:      
                        raise Exception(f"请求接口时出错，code:{res.status_code}")
                    result = res.json()["object"]
                part_num += 1
            logger.info("上传分片完成..")
            return result
        except Exception as e:     
            logger.error(f"上传分片失败，错误信息：{str(e)}")
            return None
        
    @classmethod
    def  import_image(cls,business_name,upload_info,push_id):
        export_images_url = "http://10.180.24.238:9055/resource/container/mirrorImgManager/importMirror"
        data = {
            "businessName": business_name,
            "mrDescription": f"推送大模型模板{business_name}镜像，镜像暴露端口为8000，日志映射目录，/app/logs/",
            "mrFileName": upload_info["mergeFile"],
            "mrProjectId": 494,
            "mrVersion": "v1.0.0"
            }
        header = {"token":gen_token()}
        result = requests.post(url=export_images_url,headers=header,data=data)
        if result.status_code == 200:
            print(result.text)
            resp = json.loads(result.text)
            return resp["object"]
        else:
            print(result.text)
            return None
        

if __name__ == "__main__":
    ImagesPushImpl.push(1)