import json
import os
import time
import requests
from config.log_settings import LoggingCls
from config.setting import CONFIG
from utils.utils import ServiceLogger,file_to_base64
from utils.code_executor import CodeExecutor
import ast
import traceback

logger = LoggingCls.get_logger()

class OcrEngine():
    def __init__(self):
        pass

    @classmethod
    def run(cls,api_info,data):
        try:
            url = api_info['url']
            files = {'file': open(data["img_path"], 'rb')}
            res = requests.post(url=url,files=files)
            # print(res.text)
            res = res.json()
            ServiceLogger.debug(data["id"],"数据前处理","ocr结果:%s"%json.dumps(res,ensure_ascii=False))
            return res["data"] 
        except Exception as e:
            logger.error(e)
            res = {"error": str(e)}
            ServiceLogger.error(data["id"],"数据前处理","ocr执行出错:%s"%str(e))
        return res
    

    @classmethod
    def ocr_infer(cls,url,data):
        try:
            res = requests.post(url=url,data=json.dumps(data))
            if res.status_code != 200:
                raise Exception(f"请求接口时出错，code:{res.status_code}")
            res = res.json()
            return res["data"] 
        except Exception as e:
            logger.error(e)
            res = {"error": str(e)}
            return res
        

    @classmethod
    def check_data(cls,data):
        """
         data = {
            "file": base64_str,
            "pre_code": "", 
            "post_code": "",
            "ocr_base": "adocr"
        }
        """
        if "file" not in data:
            raise Exception("缺少file参数")
        if "pre_code" not in data:
            raise Exception("缺少pre_code参数")
        if "post_code" not in data:
            raise Exception("缺少post_code参数")
        if "ocr_base" not in data:
            raise Exception("缺少ocr_base参数")
        
    @classmethod
    def process(cls,id,api_info,data):
        if "pre_process_code" not in api_info:
            raise Exception("缺少前处理代码参数 pre_process_code")
        if "post_process_code" not in api_info:
            raise Exception("缺少后处理代码参数 post_process_code")
        #数据前处理 
        full_code = CodeExecutor.build_code(api_info["pre_process_code"],data,1)
        pre_process_data = CodeExecutor.execute(full_code)
        # if pre_process_data is None:
        #     raise Exception("前处理算法推理失败..")
        if full_code is None or pre_process_data is None:
            ServiceLogger.error(id,"数据前处理","前处理代码执行结果：None")
        print("前处理结果：",pre_process_data.keys())
        ServiceLogger.debug(id,"数据前处理",f"id为{id}的数据前处理测试,前处理代码执行结果：{pre_process_data}")
        result = None
        if "stdout" in pre_process_data and pre_process_data["stdout"]:
            if  "file" in pre_process_data["stdout"]:
                data["file"] = pre_process_data["stdout"]["file"]
               
        cls.check_data(data)
        result = cls.ocr_infer(api_info["url"], data)
        if result is None:
            raise Exception("前处理算法推理失败..")
        #数据后处理
        full_code = CodeExecutor.build_code(api_info["post_process_code"],result,2)
        post_process_data = CodeExecutor.execute(full_code)
        # print("后处理结果：",post_process_data)  
        if full_code is None or post_process_data is None:
            ServiceLogger.error(id,"数据前处理","后处理代码执行结果：None")
        ServiceLogger.debug(id,"数据前处理",f"id为{id}的数据前处理测试,后处理代码执行结果：{post_process_data}")
        if "stdout" not in post_process_data or  not post_process_data["stdout"]:
            return result 
        elif "error" in post_process_data["stdout"]:
            return result 
        
        try:
            result_data = json.loads(post_process_data["stdout"]) 
        except:
            # print(post_process_data["stdout"])
            result_data = ast.literal_eval(post_process_data["stdout"])
            # print(222)
        return  result_data


    @classmethod
    def pre_process(cls,id,api_info_list,data):
        try:
            input_params = {
                "file": "",
                "pre_code": "",
                "post_code": "",
                "ocr_base": "paddleocr"
            }
            if "img_path" in data:
                input_params["file"] = file_to_base64(data["img_path"]) 
    
            output_data = input_params
            api_info_list_back = len(api_info_list) - 1
            for k, api_info in enumerate(api_info_list):
                # 分别执行多个前处理 
                ocr_api_info = api_info["api_info"]
                if isinstance(api_info["api_info"],str):
                    ocr_api_info = json.loads(api_info["api_info"])
                output_data = cls.process(api_info["id"],ocr_api_info,output_data)
                if k != api_info_list_back:
                    # 将前处理结果传递给下一个前处理
                    if isinstance(output_data,list) and len(output_data) > 0 and "img" in output_data[0]:
                        new_input_data = {}
                        new_input_data["file"] = output_data[0]["img"]
                        new_input_data["pre_code"] = ""
                        new_input_data["post_code"] = ""
                        new_input_data["ocr_base"] = data["ocr_base"]
                        output_data.clear()
                        output_data = new_input_data
                    
            return output_data

        except Exception as e:
            logger.error(e)
            ServiceLogger.error(id,"数据前处理","数据前处理执行出错:%s"%str(e))
            traceback.print_exc()
        