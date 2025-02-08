import threading
import utils.word_to_images as doc_tool
import utils.pdf_find_text as pos_tool
import utils.utils as utils
from config.log_settings import LoggingCls
from config.setting import CONFIG
import os
import json
import traceback
import sys
import re
from services.ocr import OcrEngine
from utils.code_executor import CodeExecutor
import cv2

logger = LoggingCls.get_logger()

class LLMEngine:
    def __init__(self):
        pass

    def procsss_data(self,template_info):
        #数据预处理
        entites_list = [] #实体抽取
        entites = template_info["entities_info"]
        if type(entites) == str:
            entites = eval(entites)
        for entity in entites:
            entity_prompt_config = entity["prompt_config"]
            entity_name = entity["entity_name"]
            entity_attr_id = entity["entity_attr_id"]
            exrtact_data = {"entity_name":entity_name,"entity_key":entity["entity_key"],"entity_attr_id":entity_attr_id,"prompt_configs":[entity_prompt_config]}
            entites_list.append(exrtact_data)

        
        rules_list = [] #规则抽取
        rules = template_info["rule_info"]
      
        if rules is not None:
            if type(rules) == str:
                rules = eval(rules)
            for rule in rules:
                # rule_prompt_config = rule["prompt_config"]
                # if rule_prompt_config is not None:
                #     exrtact_data = {"prompt_config":rule_prompt_config,"attr_id":rule["attr_id"]}
                rules_list.append(rule)
                
        return entites_list,rules_list  



    def get_prompt(self,voice_prompt, origin_text):
        #获取提示词
        # 实体抽取 
        prompt = (
            "我希望你充当文本抽取工具。您的角色是在给定的原文中，根据提示词，抽取想要的信息，并给出抽取内容在原文中的位置。"
            "原文内容我会用原文:开头来提醒，提示词我会用提示词:来提醒。对于每一个抽取的结果，请用一行来表示，一行内依次展示以下信息："
            "提示词、抽取结果、结果所在的短句。格式如：{提示词｜抽取结果｜结果所在的短句}。"
            "如果某一个提示词没有任何结果请返回{提示词｜None｜None}。 抽取结果必须来自于原文，结果所在的短句必须来自于原文，"
            "抽取的内容要在结果所在的短句里出现。如果抽取的内容位置不同也算是不同的抽取内容。同一个提示词抽出多个结果，请用不同的行展示。"
            "尽量抽取更多的内容，不要回答除了抽取内容以外的信息。\n"
            "原文: %s \n"
            "提示词: %s"
        )
        return prompt % (origin_text, voice_prompt)
    
    def get_rule_prompt(self,voice_prompt, origin_text):
        #获取提示词
        # 规则抽取
        prompt = "现在你是信息审核机器人，你的任务是按审核要求审核如下内容。\n"+"这是审核内容：%s \n。这是审核要求：%s \n 如果审核内容中未出现审核要求的字段，则审核失败，审核不满足要求\n 输出要求（请严格按json输出{}内字段，不可输出其他内容，任何注解都不要输出）:" + "\n" \
                +'{ "output":  // true为字段内容满足审核要求，false为字段内容不满足审核要求, ' + '"reason": //此字段输出你判断是否满足审核要求的原因}'
        return prompt % (origin_text, voice_prompt)

    def postProcess(self,responses,pdf_path,is_ocr=0):
        #数据后处理
        results = []
        # 实体抽取
        for data in responses["entity_extract"]:
            new_response_list = []
            if len(data["response"]) > 1:
                new_response_list = utils.filter_list(data["response"])
            else:
                new_response_list = data["response"]
            for res in new_response_list:
                if is_ocr == 1:
                    results.append({"entity_name":data["entity_name"],"prompt":data["prompt"],"extract_type":1,"extract_content":res["extract_content"],"origin_text":res["origin_text"],"position":res["position"],"check_status":0,"review_level":1})
                else:
                    position = pos_tool.pdf_find_text(pdf_path,res["extract_content"],res["origin_text"])
                    results.append({"entity_name":data["entity_name"],"prompt":data["prompt"],"extract_type":1,"extract_content":res["extract_content"],"origin_text":res["origin_text"],"position":position,"check_status":0,"review_level":1})
        return results
    
    # OCR 获取定位信息
    def post_process_ocr(self,ocr_data,page_number,extract_data):
        """
        ocr 获取定位信息
        """
        print("extract_data:",extract_data)
        
        if extract_data["extract_content"] == "":
            extract_data["position"] = []
            return extract_data
        
        found_positions = []
        text_list = ocr_data[0]["ocr"]["text"]
        print("text_list：",text_list)
        print("span:", ocr_data[0]["ocr"]["span"])
        pattern = r'\b{}\b'.format(re.escape(extract_data["extract_content"]))

        for k, text in enumerate(text_list):
            if re.search(pattern, text):   
            # if extract_data["extract_content"] == text:
                span = ocr_data[0]["ocr"]["span"][k]
                x_coords = [point[0] for point in span]
                y_coords = [point[1] for point in span]
                start_pixel = (min(x_coords), min(y_coords))
                end_pixel = (max(x_coords), max(y_coords))
                found_positions.append({
                                    "page": page_number,
                                    "text": text,
                                    "start_pixel": start_pixel,
                                    "end_pixel": end_pixel   
                                })
        
        extract_data["position"] = found_positions
        return extract_data

    #模型预测
    def predict(self, template_info,file_path,callback,filename,template_id,id,llm_config=None):
        try:
            print("开始抽取数据")
            utils.ServiceLogger.info(id,"大模型模板配置","开始抽取数据")
            logger.info("开始抽取数据")
            callback(None,1,template_id,id)
            images_path = "%s/%d/%d/" % (CONFIG["export_file_path"],template_id,id)
            
            utils.ServiceLogger.info(id,"大模型模板配置","开始文档解析")

             # 获取当前可执行文件的目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
            else:
                # 如果是开发环境
                base_path = utils.get_project_root()
            out_file_path = os.path.join(base_path, CONFIG["import_file_path"])
            images_path = os.path.join(base_path, images_path)
            print(images_path)
            if not os.path.exists(images_path):
                os.makedirs(images_path)

            logger.info("images_path:%s"%images_path)
            logger.info("out_file_path:%s"%out_file_path)

                      #读取文件扩展名
            ext_name = filename.rsplit('.', 1)[1]
            text_name = filename.rsplit('.', 1)[0]

            input_file_path = None
           
            path_info = doc_tool.word_to_images(out_file_path,filename,images_path)
            if path_info is None:
                utils.ServiceLogger.error(id,"大模型模板配置","文档解析失败")   
                logger.error("文档解析失败")
                callback(None,3,template_id,id)
                return 
            if ext_name in ["pdf"]:
                pdf_path = os.path.join(os.path.abspath(os.path.dirname(file_path)),"out",f"{text_name}.pdf")
                input_file_path = pdf_path

            #如果存在数据前处理配置
            print("file_path",file_path)
            is_ocr_success = False
            data = None
            ocr_data = []
            ocr_data.append(0)
            print("ext_name:",ext_name)
            if ext_name in ['jpeg','jpg','png','gif','bmp','tif','tiff','webp']:
                input_file_path = file_path
                print("llm_config:",llm_config)
                if  llm_config is not None and len(llm_config["preprocess_infos"]) > 0:
                    data = OcrEngine.pre_process(id,llm_config["preprocess_infos"],{"img_path":input_file_path})
                    print("data:",data)
                    if data and isinstance(data,list):
                        is_ocr_success = True
                        ocr_data.append(data)
                
            if ext_name in ["pdf"]:
                data = []
                for image_file in os.listdir(images_path):
                    image_path = os.path.join(images_path, image_file)
                    if  llm_config is not None and len(llm_config["preprocess_infos"]) > 0:
                        page_data = OcrEngine.pre_process(id,llm_config["preprocess_infos"],{"img_path":image_path})
                        print("data:",data)
                        #将base64转图片，压缩图片尺度为1600
                        # utils.save_base64_to_file(page_data[0]["img"],image_path)
                        # print("pdf_path:",image_path)
                        # img = cv2.imread(image_path)
                        # resized_img, resize_ratio = pos_tool.fix_min_len_resize(img, 1600)
                        # cv2.imwrite(image_path,resized_img)
                        ocr_data.append(page_data)
                        if page_data and isinstance(page_data,list):
                            data.append("".join(page_data[0]["ocr"]["raw_text"]))
                if len(data) > 0:
                    is_ocr_success = True

            if ext_name in ['jpeg','jpg','png','gif','bmp','tif','tiff','webp']  and is_ocr_success == True:
                data = data[0]["ocr"]["raw_text"]
                print("data：",data)
            if ext_name in ["docx","doc"]:
                data = utils.read_docx_by_page(file_path,2000)
            if data is None:
                callback(None,3,template_id,id)
                logger.error(" data is None 读取文件内容失败，文档解析失败")
                utils.ServiceLogger.error(id,"大模型模板配置","读取文件内容失败，文档解析失败")
                return
            utils.ServiceLogger.info(id,"大模型模板配置","开始文档预处理")
            #数据预处理
            entites_list,rules_list = self.procsss_data(template_info)
            responses = {"entity_extract":[],"rule_extract":[]}
            utils.ServiceLogger.info(id,"大模型模板配置","数据抽取中...")
            #提示词+抽取规则
            #实体抽取
            origin_data = {}
            for entites in entites_list:
                all_response = []
                prompt = entites["prompt_configs"][0]
                print("实体抽取prompt:",prompt)

                prompt_filter = utils.clean_and_replace(prompt)
                prompt_filter = utils.filter_operators(prompt_filter)
                entity_key = entites["entity_key"]
                utils.ServiceLogger.info(id,"大模型模板配置","实体抽取prompt:%s"%prompt)
                logger.info("实体抽取prompt:{}".format(prompt))
                origin_data["entity_name"] = entites["entity_name"]
                origin_data["response"] = []
                page = 1
                for origin_text in data:
                    prompt_sentence = self.get_prompt(prompt_filter, origin_text)
                    response = None
                    if llm_config is None:
                        response = utils.get_llm_response(prompt_sentence)
                    else:
                        response = LLMEngine.ask_llm(llm_config,prompt_sentence)
                    if response is None:
                        page += 1
                        continue
                    response_list = response.split("\n")
                    print(response_list)

                    for item in response_list:
                        origin_data["response"].append(item)
                        parse_data = utils.parse_llm_info(entity_key,item)
                        if parse_data is not None:
                            if ext_name in ['jpeg','jpg','png','gif','bmp','tif','tiff','webp','pdf']:
                                parse_data = self.post_process_ocr(ocr_data[page],page,parse_data)
                                # parse_data = pos_tool.locate_text(page,ocr_data[page],parse_data)
                                
                            all_response.append(parse_data)
                    page += 1
                           
                responses["entity_extract"].append({"entity_name":entites["entity_name"],"entity_key":entity_key,"entity_attr_id":entites["entity_attr_id"],"prompt":prompt,"response":utils.remove_duplicate_dicts(all_response)})

            print("*"*20)
            for res in responses["entity_extract"]:
                entity_name = res["entity_name"]
                print(f"*************{entity_name}******************")
                for item in res["response"]:
                    print(item)
            print("*"*20)
               
            result = None
            if ext_name in ['jpeg','jpg','png','gif','bmp','tif','tiff','webp','pdf']:
                result = self.postProcess(responses,path_info["pdf_path"],1)
            else:
                result = self.postProcess(responses,path_info["pdf_path"])

            entites_contents = []
            for res in result:
                rule_contents = {}
                rule_contents["entity_name"] = res["entity_name"]
                rule_contents["prompt"] = res["prompt"]
                rule_contents["extract_content"] = res["extract_content"]
                entites_contents.append(rule_contents)

            origin_text = json.dumps(entites_contents)

            #规则抽取
            all_response = []
            for rules in rules_list:
                prompt_config = rules["prompt_config"]
                rule_name = "XXX规则名称"
                if "rule_name" in rules:
                    rule_name = rules["rule_name"]       
                print("规则抽取prompt:",prompt_config)
                utils.ServiceLogger.info(id,"大模型模板配置","规则抽取prompt:%s"%prompt_config)
                logger.info("规则抽取prompt:{}".format(prompt_config))   
                prompt_sentence = self.get_rule_prompt(prompt_config, origin_text)
                response = None
                if llm_config is None:
                    response = utils.get_llm_response(prompt_sentence)
                else:
                    response = LLMEngine.ask_llm(llm_config,prompt_sentence)
                
                if response is not None:
                    print(response)
                    result.append({"rule_name":rule_name,"prompt":prompt_config,"extract_type":2,"extract_content":json.loads(response)})
                else:
                    result.append({"rule_name":rule_name,"prompt":prompt_config,"extract_type":2,"extract_content":{}})

          
            review_infos = json.dumps(result,ensure_ascii=False,indent=4)
            print("模型预测结果:",review_infos)
           
            logger.info("模型预测结果:{}".format(result))
            logmsg = json.dumps(result,ensure_ascii=False,indent=4)
            utils.ServiceLogger.info(id,"大模型模板配置","模型预测结果:%s"%logmsg)
            callback(result,2,template_id,id)
            utils.ServiceLogger.info(id,"大模型模板配置","数据抽取完成")   
        except Exception as e:
            traceback.print_exc()
            print(str(e))
            callback(None,4,template_id,id)
            utils.ServiceLogger.error(id,"大模型模板配置","数据抽取失败：%s"%str(e))   
            return str(e)
    
    @classmethod
    def run(cls,callback,template_info,file_path,filename,template_id,id,llm_config=None):
        # 使用 lambda 函数，并正确传递 template_info 和 data
        thread = threading.Thread(target=lambda: cls().predict(template_info, file_path,callback,filename,template_id,id,llm_config))
        print("模型预测线程开启")
        thread.start()
        print("模型预测线程进行中")


    @classmethod
    def ask_llm(cls,api_info, prompt_sentence):
        if "pre_process_code" not in api_info["api_info"]:
            raise Exception("缺少前处理代码参数 pre_process_code")
        if "post_process_code" not in api_info["api_info"]:
            raise Exception("缺少后处理代码参数 post_process_code")
        #数据前处理
        id = api_info["id"]
        full_code = CodeExecutor.build_code(api_info["api_info"]["pre_process_code"],prompt_sentence,1)
        pre_process_data = CodeExecutor.execute(full_code)
        print("前处理结果：",pre_process_data)
        utils.ServiceLogger.debug(id,"算法基座",f"id为{id}的算法基座测试,前处理代码执行结果：{pre_process_data}")
        if "stdout" in pre_process_data and pre_process_data["stdout"]:
            prompt_sentence = eval(pre_process_data)
        result = utils.workflow_llm_response(api_info,prompt_sentence)
        #数据后处理
        full_code = CodeExecutor.build_code(api_info["api_info"]["post_process_code"],result,2)
        post_process_data = CodeExecutor.execute(full_code)
        print("后处理结果：",post_process_data)
        utils.ServiceLogger.debug(id,"算法基座",f"id为{id}的算法基座测试,后处理代码执行结果：{post_process_data}")
        if "stdout" not in post_process_data or not post_process_data["stdout"]:
            return result
        return post_process_data


    @classmethod
    def test(cls,id,name,api_info, data):
        try:
            print("api_info:",api_info)
            if "path" in data and data["path"]  is not None:
                content = utils.read_file_content(data["path"])
                content_text = "".join(content)
                prompt = f"%s。这是上传文件中的内容:%s"%(data["text"],content_text)
                print(prompt)
                res = utils.test_llm_response(name,api_info, prompt)
                res = {"result": "success","data":res} 
                utils.ServiceLogger.debug(id,"算法基座","算法基座执行结果:%s"%json.dumps(res,ensure_ascii=False))  
                return res  
            else:
                print(data["text"])
                print("name:",name)
                res = utils.test_llm_response(name,api_info, data["text"])
                res = {"result": "success","data":res}
                utils.ServiceLogger.debug(id,"算法基座","算法基座执行结果:%s"%json.dumps(res,ensure_ascii=False))  
                return res       
        except Exception as e:
            logger.error(e)
            res = {"result": "error"}
            utils.ServiceLogger.error(id,"算法基座","算法基座执行出错:%s"%str(e))  
            return res
    
    @classmethod
    def process(cls,id,name,api_info,data):
        if "pre_process_code" not in api_info:
            raise Exception("缺少前处理代码参数 pre_process_code")
        if "post_process_code" not in api_info:
            raise Exception("缺少后处理代码参数 post_process_code")
        #数据前处理
        full_code = CodeExecutor.build_code(api_info["pre_process_code"],data,1)
        pre_process_data = CodeExecutor.execute(full_code)
        print("前处理结果：",pre_process_data)
        utils.ServiceLogger.debug(id,"算法基座",f"id为{id}的算法基座测试,前处理代码执行结果：{pre_process_data}")
        if "stdout" in pre_process_data and pre_process_data["stdout"]:
            data = eval(pre_process_data)
        result = cls.test(id,name,api_info, data)
        #数据后处理
        full_code = CodeExecutor.build_code(api_info["post_process_code"],result,2)
        post_process_data = CodeExecutor.execute(full_code)
        print("后处理结果：",post_process_data)
        utils.ServiceLogger.debug(id,"算法基座",f"id为{id}的算法基座测试,后处理代码执行结果：{post_process_data}")
        print("post_process_data:",post_process_data)
        if "stdout" not in post_process_data or not post_process_data["stdout"]:
            return result
        return post_process_data
    
       
if __name__ == "__main__":

    # template = {
    #     "id": 32,
    #     "name": "合同抽取-测试",
    #     "description": "",
    #     "workflow_id": 1,
    #     "entities_info": [
    #         {
    #             "entity_key": "1",
    #             "entity_name": "出租方",
    #             "prompt_config": "出租方名称|甲方名称",
    #             "entity_attr_id": 1
    #         },
    #         {
    #             "entity_key": "2",
    #             "entity_name": "身份证号",
    #             "prompt_config": "身份证号",
    #             "entity_attr_id": 2
    #         },
    #         {
    #             "entity_key": "3",
    #             "entity_name": "甲方法定代表人",
    #             "prompt_config": "甲方法定代表人|甲方主要负责人",
    #             "entity_attr_id": 1
    #         },
    #         {
    #             "entity_key": "4",
    #             "entity_name": "地址",
    #             "prompt_config": "法定地址",
    #             "entity_attr_id": 1
    #         },
    #         {
    #             "entity_key": "5",
    #             "entity_name": "联系人",
    #             "prompt_config": "联系人",
    #             "entity_attr_id": 1
    #         },
    #         {
    #             "entity_key": "6",
    #             "entity_name": "联系电话",
    #             "prompt_config": "联系电话",
    #             "entity_attr_id": 2
    #         },
    #         {
    #             "entity_key": "7",
    #             "entity_name": "承租方",
    #             "prompt_config": "承租方名称|乙方名称",
    #             "entity_attr_id": 1
    #         },
    #         {
    #             "entity_key": "8",
    #             "entity_name": "合同编号",
    #             "prompt_config": "合同编号",
    #             "entity_attr_id": 1
    #         },
    #         {
    #             "entity_key": "9",
    #             "entity_name": "乙方法定代表人|乙方主要负责人",
    #             "prompt_config": "乙方法定代表人|乙方主要负责人",
    #             "entity_attr_id": 1
    #         }
    #     ],
    #     "rule_info": [
    #         {
    #             "prompt_config": "身份证号为空，则不通过。"
    #         },
    #         {
    #             "prompt_config": "联系电话是11位电话号码，则通过审核。"
    #         }
    #     ],
    #     "last_update_time": 1734575911,
    #     "delete_status": True,
    #     "create_time": 1734575911,
    #     "user": "disifanshi",
    #     "enable": True
    # }
    template = {
        "id": 43,
        "name": "监测报告-测试",
        "description": "测试",
        "workflow_id": 1,
        "entities_info": [
            {
                "entity_key": "1",
                "entity_name": "监测机构名称",
                "prompt_config": "监测单位名称",
                "entity_attr_id": 1
            },
            {
                "entity_key": "2",
                "entity_name": "委托单位名称",
                "prompt_config": "委托单位名称",
                "entity_attr_id": 1
            },
            {
                "entity_key": "3",
                "entity_name": "监测报告编号",
                "prompt_config": "监测报告编号",
                "entity_attr_id": 1
            },
            {
                "entity_key": "4",
                "entity_name": "监测地点",
                "prompt_config": "基站地址|建设地点|监测地点",
                "entity_attr_id": 1
            },
            {
                "entity_key": "5",
                "entity_name": "站址经度和纬度",
                "prompt_config": "经纬度",
                "entity_attr_id": 2
            },
            {
                "entity_key": "6",
                "entity_name": "铁塔站址编码",
                "prompt_config": "铁塔站址编码",
                "entity_attr_id": 1
            },
            {
                "entity_key": "7",
                "entity_name": "网络制式",
                "prompt_config": "网络制式|网络系统",
                "entity_attr_id": 1
            },
            {
                "entity_key": "8",
                "entity_name": "频率范围",
                "prompt_config": "发射频率范围",
                "entity_attr_id": 2
            },
            {
                "entity_key": "9",
                "entity_name": "天线数量",
                "prompt_config": "天线数量",
                "entity_attr_id": 2
            },
            {
                "entity_key": "12",
                "entity_name": "监测日期",
                "prompt_config": "监测日期",
                "entity_attr_id": 1
            },
            {
                "entity_key": "13",
                "entity_name": "监测时间",
                "prompt_config": "监测时间",
                "entity_attr_id": 1
            },
            {
                "entity_key": "14",
                "entity_name": "天气情况",
                "prompt_config": "天气",
                "entity_attr_id": 1
            },
            {
                "entity_key": "15",
                "entity_name": "环境温度",
                "prompt_config": "环境温度",
                "entity_attr_id": 1
            },
            {
                "entity_key": "16",
                "entity_name": "相对湿度",
                "prompt_config": "相对湿度",
                "entity_attr_id": 1
            },
            {
                "entity_key": "17",
                "entity_name": "监测所依据的技术文件名称及代号",
                "prompt_config": "监测所依据的技术文件名称及代号",
                "entity_attr_id": 1
            },
            {
                "entity_key": "18",
                "entity_name": "监测使用辐射检测仪器的设备名称、型号规格及编号",
                "prompt_config": "仪器名称|型号规格|探头型号|探头编号|生产厂家",
                "entity_attr_id": 1
            },
            {
                "entity_key": "19",
                "entity_name": "辐射检测仪器的频率范围、量程、校准证书及有效期",
                "prompt_config": "辐射检测仪器的频率范围、量程、校准证书及有效期",
                "entity_attr_id": 1
            }
        ],
        "rule_info": None,
        "enable": True,
        "last_update_time": 1733730691,
        "delete_status": True,
        "create_time": 1733730691,
        "user": "disifanshi"
    }
    # template =  TemplatesModel.get(22)
    docx_path = "data/uploads/templates/智能审核6.docx"
    data_list = utils.read_docx_by_page(docx_path,2000)
    for i, page_content in enumerate(data_list):
        print(f"Page {i + 1} content:")
        print(page_content)
        print("-" * 20)
    def callback(result,status,template_id,id):
        print("callback:",status)
    LLMEngine.run(callback, template,data_list,"智能审核6.docx",3,8)
