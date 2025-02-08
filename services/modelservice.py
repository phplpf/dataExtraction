from sqlalchemy import Column, Integer, String,Boolean,func
from models.databases import session
from models.databases import ModelServiceModel,ModelServiceTypeModel
from sqlalchemy.dialects.postgresql import JSONB
from config.log_settings import LoggingCls
import json
from config.setting import CONFIG,update_config
import os
from services.ocr import OcrEngine
from services.llm import LLMEngine
import utils.utils as utils
from utils.code_executor import CodeExecutor

logger = LoggingCls.get_logger()

class ModelServiceModelImpl(ModelServiceModel):


    @classmethod
    def init_default_data(cls):
        ocr_preprocess_1 = session.query(cls).filter(cls.id == 1).first()
        ocr_preprocess_2 = session.query(cls).filter(cls.id == 2).first()
        llmbase_data_3 = session.query(cls).filter(cls.id == 3).first()
        llmbase_data_4 = session.query(cls).filter(cls.id == 4).first()
        session.close()
    
        if ocr_preprocess_1 and ocr_preprocess_1.is_default != 1:
            ocr1 = {}
            ocr1["name"] = "OCR1"
            ocr1["description"] = "OCR1"
            ocr1["service_type"] = 1
            ocr1["is_default"] = 1
            ocr1["model_type_id"] = 1
            ocr1["img_path"] = utils.get_default_ocr_config(None)[0]["img_path"]
            ocr1["api_info"] = utils.get_default_ocr_config(None)[0]["api_info"]
            ocr1["user"] = None
            ocr1["enable"] = False
            cls.update(1,ocr1)
            #更新数据前处理
        else:
            if ocr_preprocess_1 is None:
                ocr1 = {}
                ocr1["id"] = 1
                ocr1["name"] = "OCR1"
                ocr1["description"] = "OCR1"
                ocr1["service_type"] = 1
                ocr1["is_default"] = 1
                ocr1["model_type_id"] = 1
                ocr1["img_path"] = utils.get_default_ocr_config(None)[0]["img_path"]
                ocr1["api_info"] = utils.get_default_ocr_config(None)[0]["api_info"]
                ocr1["user"] = None
                ocr1["enable"] = False
                cls.create(ocr1)
                #插入数据前处理
        if ocr_preprocess_2 and ocr_preprocess_2.is_default != 1:
            paddle_ocr = {}
            paddle_ocr["name"] = "Paddle OCR"
            paddle_ocr["description"] = "Paddle OCR"
            paddle_ocr["service_type"] = 1
            paddle_ocr["is_default"] = 1
            paddle_ocr["model_type_id"] = 1
            paddle_ocr["img_path"] = utils.get_default_ocr_config(None)[1]["img_path"]
            paddle_ocr["api_info"] = utils.get_default_ocr_config(None)[1]["api_info"]
            paddle_ocr["user"] = None
            paddle_ocr["enable"] = False
            cls.update(2,paddle_ocr)
            #更新数据前处理
        else:
            if ocr_preprocess_2 is None:
                paddle_ocr = {}
                paddle_ocr["id"] = 2
                paddle_ocr["name"] = "Paddle OCR"
                paddle_ocr["description"] = "Paddle OCR"
                paddle_ocr["service_type"] = 1
                paddle_ocr["is_default"] = 1
                paddle_ocr["model_type_id"] = 1
                paddle_ocr["img_path"] = utils.get_default_ocr_config(None)[1]["img_path"]
                paddle_ocr["api_info"] = utils.get_default_ocr_config(None)[1]["api_info"]
                paddle_ocr["user"] = None
                paddle_ocr["enable"] = False
                cls.create(paddle_ocr)
                #插入数据前处理
        if llmbase_data_3 and llmbase_data_3.is_default != 1:
            qwen32 = {}
            qwen32["name"] = "Qwen32"
            qwen32["description"] = "Qwen32"
            qwen32["service_type"] = 2
            qwen32["is_default"] = 1
            qwen32["model_type_id"] = 2
            qwen32["img_path"] = utils.get_default_llm_config(None)[0]["img_path"]
            qwen32["api_info"] = utils.get_default_llm_config(None)[0]["api_info"]
            qwen32["user"] = None
            qwen32["enable"] = False
            cls.update(3,qwen32)
            #更新数据前处理
        else:
            if llmbase_data_3 is None:
                qwen32 = {}
                qwen32["id"] = 3
                qwen32["name"] = "Qwen32"
                qwen32["description"] = "Qwen32"
                qwen32["service_type"] = 2
                qwen32["is_default"] = 1
                qwen32["model_type_id"] = 2
                qwen32["img_path"] = utils.get_default_llm_config(None)[0]["img_path"]
                qwen32["api_info"] = utils.get_default_llm_config(None)[0]["api_info"]
                qwen32["user"] = None
                qwen32["enable"] = True
                cls.create(qwen32)
                #插入数据前处理
        if llmbase_data_4 and  llmbase_data_4.is_default != 1:
            qwen72 = {}
            qwen72["name"] = "Qwen72"
            qwen72["description"] = "Qwen72"
            qwen72["service_type"] = 2
            qwen72["is_default"] = 1
            qwen72["model_type_id"] = 2
            qwen72["img_path"] = utils.get_default_llm_config(None)[1]["img_path"]
            qwen72["api_info"] = utils.get_default_llm_config(None)[1]["api_info"]
            qwen72["user"] = None
            qwen72["enable"] = True
            cls.update(4,qwen72)
            #更新数据前处理
        else:
            if llmbase_data_4 is None:
                qwen72 = {}
                qwen72["id"] = 4
                qwen72["name"] = "Qwen72"
                qwen72["description"] = "Qwen72"
                qwen72["service_type"] = 2
                qwen72["is_default"] = 1
                qwen72["model_type_id"] = 2
                qwen72["img_path"] = utils.get_default_llm_config(None)[1]["img_path"]
                qwen72["api_info"] = utils.get_default_llm_config(None)[1]["api_info"]
                qwen72["user"] = None
                qwen72["enable"] = True
                cls.create(qwen72)
                #插入数据前处理

    @classmethod
    def get_all(cls,params,type):
        cls.init_default_data()
        logger.debug("params: {}".format(params))
        query = session.query(cls)
        total = 0
        page = 1
        count = 20
        user = None
        model_type_id = None
        name = None

        if params.get('page'):
            page = int(params.get('page'))
        if params.get('count'):
            count = int(params.get('count'))      
        if params.get('user'):
            user = params.get('user')
        if params.get('model_type_id'):
            model_type_id = params.get('model_type_id')
        if params.get('name'):
            name = params.get('name')

        query = query.filter(cls.user == user).filter(cls.service_type == type)
        if name:
            query = query.filter(cls.name.like(f"%{name}%"))
        if model_type_id:
            query = query.filter(cls.model_type_id == model_type_id)
            # 获取总条数
            total = query.count()
        # 分页
        query = query.order_by(cls.create_time.desc())
        results = query.limit(count).offset((page - 1) * count).all()
        session.close()
        results_list = []
        if type == 1:
            if name:
                ocr_default_list = session.query(cls).filter(cls.name.like(f"%{name}%")).filter(cls.is_default == 1).filter(cls.service_type == 1).all()
            else:
                ocr_default_list = session.query(cls).filter(cls.is_default == 1).filter(cls.service_type == 1).all()

            session.close()
            for ocr in ocr_default_list:
                ocr_data = ocr.to_dict()
                # print(ocr_data)
                if isinstance(ocr_data["api_info"], tuple):
                    ocr_data["api_info"] = ocr_data["api_info"][0]
                if ocr_data["api_info"]["pre_process_code"] == "":
                    ocr_data["api_info"]["pre_process_code"] = utils.get_pre_process_default_format()
                if ocr_data["api_info"]["post_process_code"] == "":
                    ocr_data["api_info"]["post_process_code"] = utils.get_pre_process_default_format()
                results_list.append(ocr_data)
          
        elif type == 2:
            if name:
                llm_datault_list = session.query(cls).filter(cls.name.like(f"%{name}%")).filter(cls.is_default == 1).filter(cls.service_type == 2).all()
            else:
                llm_datault_list = session.query(cls).filter(cls.is_default == 1).filter(cls.service_type == 2).all()
            session.close()
            for llmbase in llm_datault_list:
                llmbase_data = llmbase.to_dict()
                if isinstance(llmbase_data["api_info"], tuple):
                    llmbase_data["api_info"] = llmbase_data["api_info"][0]
                if llmbase_data["api_info"]["pre_process_code"] == "":
                    llmbase_data["api_info"]["pre_process_code"] = utils.get_pre_process_default_format()
                if llmbase_data["api_info"]["post_process_code"] == "":
                    llmbase_data["api_info"]["post_process_code"] = utils.get_pre_process_default_format()
                results_list.append(llmbase_data)

        for result in results:
            if result.is_default == 1:
                continue
            data = result.to_dict()
            if isinstance(data["api_info"], tuple):
                data["api_info"] = data["api_info"][0]
            if data["api_info"]["pre_process_code"] == "":
                data["api_info"]["pre_process_code"] = utils.get_pre_process_default_format()
            if data["api_info"]["post_process_code"] == "":
                data["api_info"]["post_process_code"] = utils.get_post_process_default_format()
            results_list.append(data)
    
        resp = {
            "total": total,
            "page": page,
            "count": count,
            "results": results_list
        }

        return resp

    @classmethod
    def get(cls, id,type):
        logger.debug("id: %d,type: %d",id,type)
        modelservice = session.query(cls).filter(cls.id == id).filter(cls.service_type == type).first()
        session.close()
        if modelservice is None:
            raise  Exception(f"id为{id}的记录不存在！")
        
        result = modelservice.to_dict()
        if isinstance(result["api_info"], tuple):
            result["api_info"] = result["api_info"][0]
        if result["api_info"]["pre_process_code"] == "":
            result["api_info"]["pre_process_code"] = utils.get_pre_process_default_format()
        if result["api_info"]["post_process_code"] == "":
            result["api_info"]["post_process_code"] = utils.get_post_process_default_format()
        return result

    @classmethod
    def create(cls, data):
        modelservice = cls(**data)
        print("modelservice:",modelservice)
        #查询任务名称是否重复
        modelservice_name = session.query(cls).filter(cls.name == data['name']).filter(cls.service_type == data['service_type']).first()
        if modelservice_name:
            raise Exception("任务名称重复")
        session.add(modelservice)
        session.commit()
        session.refresh(modelservice)
        session.close()
        return modelservice

    @classmethod
    def update(cls, id, data):  
        modelservice = session.query(cls).filter(cls.service_type == data['service_type']).filter(cls.id == id).first()
        if modelservice is None:
            raise Exception(f"id为{id}的记录不存在")
        
        if "service_type" in data and int(modelservice.service_type) != int(data['service_type']):
            raise Exception("服务类型不可修改")
        for key, value in data.items():
            setattr(modelservice, key, value)
        session.commit()
        session.refresh(modelservice)
        session.close()
        return modelservice.to_dict()

    @classmethod
    def delete(cls, id,type):
        modelservice = session.query(cls).filter(cls.service_type == type).filter(cls.id == id).first()
        if modelservice is None:
            raise Exception(f"id为{id}的记录不存在！")
        if modelservice.enable == True:
            raise Exception("服务已被关联，无法删除")
        if modelservice.is_default == 1:
            raise Exception("默认服务无法删除")
        session.delete(modelservice)
        session.commit()
        session.close()
        return modelservice

    @classmethod
    def ocr_test(cls,id,data):
        modelservice = session.query(cls).filter(cls.id == id).first()
        session.close()
        if modelservice is None:
            raise Exception(f"id为{id}的前处理模型记录不存在！")
        #执行ocr推理测试并返回结果
        if modelservice.api_info == None:
            raise Exception("OCR模型服务信息为空")
        
        api_info = modelservice.api_info
        if isinstance(api_info,str):
            try:
                clean_data = api_info.replace('\n', '\\n').replace('\r','\\r').replace('\t','\\t')  # 转义换行符
                api_info = json.loads(clean_data)
            except:
                api_info = eval(api_info)   

        base64_img_path = utils.file_to_base64(data["img_path"])          
        ocr_data = {
            "file": base64_img_path,
            "pre_code": "",
            "post_code": "",
            "ocr_base": "paddleocr"
        }
        result = OcrEngine.process(id,api_info,ocr_data)

        return result
    
    @classmethod
    def llm_test(cls,id,data):  
        modelservice = session.query(cls).filter(cls.id == id).first()
        session.close()
        #执行llm推理测试并返回结果
        if modelservice is None:
            raise Exception(f"id为{id}的大模型记录不存在！")
        api_info = modelservice.api_info
        if isinstance(api_info,str):
            try:
                clean_data = api_info.replace('\n', '\\n').replace('\r','\\r').replace('\t','\\t')  # 转义换行符
                api_info = json.loads(clean_data)
            except:
                api_info = eval(api_info)     

        result = LLMEngine.process(id,modelservice.name,api_info, data)
        return result
    
    @classmethod
    def get_ocr_infos(cls,params):
        user = None
        if params.get('user'):
            user = params.get('user')
        modelservice = session.query(cls).filter(cls.user == user).filter(cls.service_type == 1).all()
        session.close()
        #查询默认的
        default_modelservice = session.query(cls).filter(cls.is_default == 1).filter(cls.service_type == 1).all()
        session.close()

        if not modelservice or user is None:
            category = {}
            for result in default_modelservice:
                try:
                    modeltypeinfo = ModelServiceTypeModelImpl.get(result.model_type_id)
                    name = modeltypeinfo["name"]                      
                except Exception as e:
                    print(str(e))
                    continue
                if name not in category:
                    category[name] = []
                    category[name].append({"id":result.id,"name":result.name})   
                else:
                    category[name].append({"id":result.id,"name":result.name})   
            return category
        
        category = {}
        for result in default_modelservice:
            try:
                modeltypeinfo = ModelServiceTypeModelImpl.get(result.model_type_id)
                name = modeltypeinfo["name"]                      
            except Exception as e:
                print(str(e))
                continue
            if name not in category:
                category[name] = []
                category[name].append({"id":result.id,"name":result.name})   
            else:
                category[name].append({"id":result.id,"name":result.name})   
        for result in modelservice:
            try:
                modeltypeinfo = ModelServiceTypeModelImpl.get(result.model_type_id)
                name = modeltypeinfo["name"]
            except Exception as e:
                print(str(e))
                continue
            if name not in category:
                category[name] = []
                category[name].append({"id":result.id,"name":result.name})   
            else:
                category[name].append({"id":result.id,"name":result.name})   
        
        return category
    
    @classmethod
    def get_llm_infos(cls,params):
        user = None
        if params.get('user'):
            user = params.get('user')  
        modelservice = session.query(cls).filter(cls.user == user).filter(cls.service_type == 2).all()
        session.close()

        #查询默认的
        default_modelservice = session.query(cls).filter(cls.is_default == 1).filter(cls.service_type == 2).all()
        session.close()
        if not modelservice or user is None:
            category = {}
            for result in default_modelservice:    
                try:
                    modeltypeinfo = ModelServiceTypeModelImpl.get(result.model_type_id)
                    name = modeltypeinfo["name"]
                except Exception as e:
                    print(str(e))
                    continue
                if name not in category:
                    category[name] = []
                    category[name].append({"id":result.id,"name":result.name})   
                else:
                    category[name].append({"id":result.id,"name":result.name})   
            return category
        
        category = {}
        for result in default_modelservice:   
            try:
                modeltypeinfo = ModelServiceTypeModelImpl.get(result.model_type_id)
                name = modeltypeinfo["name"]
            except Exception as e:
                print(str(e))
                continue
            if name not in category:
                category[name] = []
                category[name].append({"id":result.id,"name":result.name})   
            else:
                category[name].append({"id":result.id,"name":result.name})   
        for result in modelservice: 
            try:
                modeltypeinfo = ModelServiceTypeModelImpl.get(result.model_type_id)
                name = modeltypeinfo["name"]
            except Exception as e:
                print(str(e))
                continue
            if name not in category:
                category[name] = []   
                category[name].append({"id":result.id,"name":result.name})
            else:
                category[name].append({"id":result.id,"name":result.name})
        
        return category
    

class ModelServiceTypeModelImpl(ModelServiceTypeModel):
    @classmethod
    def get_all(cls,params,type=1):
        logger.debug("params: {}".format(params))
        query = session.query(cls)
        total = 0
        user = None   
        if params.get('user'):
            user = params.get('user')

        query = query.filter(cls.type == type).filter(cls.user == user).filter(cls.enable == True)
            # 获取总条数
        total = query.count()
        qurey = query.order_by(cls.create_time.desc())
        results = qurey.all()
        session.close()
        results_list = []
        is_default_pre = False
        is_llm_flag = False
        for result in results:
            res = result.to_dict()
            is_default = 0
            if res["id"] == 1:  
                is_default_pre = True
                is_default = 1
            if res["id"] == 2:
                is_llm_flag = True
                is_default = 1
            results_list.append({"id":res["id"],"name":res["name"],"is_default":is_default})

        ocr_pre_data = session.query(cls).filter(cls.id == 1).first()
        llm_type_data = session.query(cls).filter(cls.id == 2).first()
        if ocr_pre_data is None or llm_type_data is None:
            #向数据库中插入两条默认数据 id为1,2
            pre_process  = {}
            pre_process["id"] = 1
            pre_process["user"] = user
            pre_process["type"] = 1  
            pre_process["is_default"] = 1  
            pre_process["name"] = "OCR识别"
            ocr_pre_data = session.query(cls).filter(cls.id == 1).first()
            session.close()
            if ocr_pre_data == None: 
                cls.create(pre_process,1)
            else:
                cls.update(1,pre_process)
        
            llm_type_info = {}
            llm_type_info["id"] = 2
            llm_type_info["user"] = user
            llm_type_info["type"] = 2
            llm_type_info["is_default"] = 1
            llm_type_info["name"] = "OpenAI API"
            llm_type_data = session.query(cls).filter(cls.id == 2).first()
            session.close() 
            if llm_type_data == None:
                cls.create(llm_type_info,2)
            else:
                cls.update(2,llm_type_info)

        if is_default_pre == False and is_llm_flag == False:
            if type == 1:
                results_list = [{"id":1,"name":"OCR识别","is_default":1}]
            if type == 2:
                results_list = [{"id":2,"name":"OpenAI API","is_default":1}] 

        resp = {
            "total": total,
            "results": results_list
        }

        return resp
    
    @classmethod
    def get(cls,id):
        modelservice = session.query(cls).filter(cls.id == id).first()
        session.close()
        if modelservice == None and id == 1:
            return {"id":1,"name":"OCR识别","is_default":1}
        if modelservice == None and id == 2:
            return {"id":2,"name":"OpenAI API","is_default":1}
        
        if modelservice is None:
            raise  Exception(f"id为{id}的记录不存在！")
        
        return modelservice.to_dict()

    @classmethod
    def create(cls,data,type=1):
        modelservice_type = cls(**data)
        #查询任务名称是否重复
        modelservice_name = session.query(cls).filter(cls.type == type).filter(cls.user == data['user']).filter(cls.name == data['name']).first()
        if modelservice_name:
            raise Exception("名称重复")
        session.add(modelservice_type)
        session.commit()
        session.refresh(modelservice_type)
        session.close()
        return modelservice_type
    
    @classmethod
    def update(cls, id, data,type=1):
        modelservice_type = session.query(cls).filter(cls.id == id).first()
        for key, value in data.items():
            setattr(modelservice_type, key, value)
        session.commit()
        session.refresh(modelservice_type)
        session.close()
        return modelservice_type

    @classmethod
    def delete(cls, id,type=1):
        if id == 1 or id == 2:
            raise Exception("不可删除")
        modelservice_type = session.query(cls).filter(cls.id == id).first()
        session.delete(modelservice_type)
        session.commit()
        session.close()
        return modelservice_type