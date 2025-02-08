from pdf2image import convert_from_path
import os
import subprocess
import PyPDF2
import time
from config.log_settings import LoggingCls
import traceback
import sys

logger = LoggingCls.get_logger()

def pdf_to_images(pdf_path, images_path, dpi=300,batch_size=10):
     # 获取PDF页数
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        num_pages = len(reader.pages)


    logger.info("num_pages=%s"%num_pages)
    # 分批处理页面
    for start_page in range(0, num_pages, batch_size):
        end_page = min(start_page + batch_size, num_pages)
        print(f"Processing pages {start_page + 1} to {end_page}")
        logger.info(f"Processing pages {start_page + 1} to {end_page}")
        
        # 转换指定页面范围
        logger.info("pdf_path=%s"%pdf_path)
        images = convert_from_path(pdf_path, dpi=dpi, first_page=start_page + 1, last_page=end_page)

        # 保存每一页为单独的图片到 images 目录
        for i, image in enumerate(images, start=start_page):
            image_path = os.path.join(images_path, f'page{i + 1}.png')
            image.save(image_path, 'PNG')



def convert_to_pdf(word_file_path, word_file_name, retries=3):
    word_name = word_file_name.rsplit('.', 1)[0]
    word_file_out_path  = os.path.join(word_file_path, "out")
    print(word_file_out_path)
 
    if not os.path.exists(word_file_out_path):
        os.makedirs(word_file_out_path)
    
    pdf_path = None
    command = [
        'docker', 'run', '--rm',
        '-v', f'{word_file_path}:/app/data',
        'headless-wps:v1.0',
        '--format', 'pdf',
        f'/app/data/{word_file_name}'
    ]
    print(command)
    logger.info("命令执行：%s"% (",".join(command)))
    for attempt in range(retries):
        try:
            # 执行 Docker 命令
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info("命令执行成功：%s"%result.stdout)
            
            # 检查 PDF 文件是否生成
            pdf_path = os.path.join(word_file_out_path, f'{word_name}.pdf')
            if os.path.exists(pdf_path):
                logger.info(f"PDF 文件生成成功：{pdf_path}")
                break
            else:
                raise FileNotFoundError(f"PDF 文件未生成，检查路径：{pdf_path}")
        
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败：{e.stderr}")
            traceback.print_exc()
        
        except FileNotFoundError as e:
            print(e)
            traceback.print_exc()
        
        if attempt < retries - 1:
            print(f"重试第 {attempt + 1} 次...")
            time.sleep(1)  # 等待一段时间后重试

    else:
        raise RuntimeError(f"多次尝试后仍未成功转换文件：{word_file_name}")

    return pdf_path

def word_to_images(word_file_path, word_file_name, images_path):
    try:
        print("开始执行 Docker 命令: word_file_path=%s,word_file_name=%s,images_path=%s" % (word_file_path, word_file_name, images_path))
        logger.info("开始执行 Docker 命令: word_file_path=%s,word_file_name=%s,images_path=%s" % (word_file_path, word_file_name, images_path))
        # Docker 命令和参数
        ext_name = word_file_name.rsplit('.', 1)[1]
        word_file_out_path  = f'{word_file_path}/out/'
        print(word_file_out_path)
        if not os.path.exists(word_file_out_path):
            os.makedirs(word_file_out_path)
        pdf_path = None
        if ext_name in ["docx","doc","txt"]:
           pdf_path = convert_to_pdf(word_file_path, word_file_name)
        elif ext_name == "pdf":
            pdf_file_out_path = os.path.join(word_file_path, word_file_name)
            os.chmod(pdf_file_out_path, 0o777)
            os.system(f"cp {pdf_file_out_path} {word_file_out_path}")
            pdf_path = os.path.join(word_file_out_path, word_file_name)
        elif ext_name in ['jpeg','jpg','png','gif','bmp','tif','tiff','webp','pdf']:
            img_path = os.path.join(word_file_path, word_file_name)
            image_path = os.path.join(images_path, word_file_name)
            os.system("cp %s %s"%(img_path,image_path))
            return {
                "pdf_path": img_path,
                "images_path": images_path
            }
        else:
            raise Exception("不支持的文件格式：%s" % ext_name)
        
        if pdf_path is None:
            raise Exception("PDF 文件未生成，检查路径：%s" % pdf_path)
        # 转换 PDF 为图像
        pdf_to_images(pdf_path, images_path)
        return {
            "pdf_path": pdf_path,
            "images_path": images_path
        }
    except subprocess.CalledProcessError as e:
        print("Docker 命令执行失败：", e.stderr)
        logger.error("Docker 命令执行失败：", e.stderr)
        traceback.print_exc()
        return None
    except FileNotFoundError as e:
        print("文件未找到错误：", e)
        logger.error("文件未找到错误：", e)
        traceback.print_exc()
        return None
    except Exception as e:
        print("发生异常：", e)
        logger.error("发生异常：", e)
        traceback.print_exc()
        return None

if __name__ == '__main__':
    word_file_path = "/home/senscape/lhk/custom_template/"
    word_file_name = "docx_test.docx"
    images_path = "/home/senscape/lhk/custom_template/images/test/"
    word_to_images(word_file_path, word_file_name, images_path)
