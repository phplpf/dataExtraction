from sqlalchemy import Column, Integer,Boolean,String,func
from models.databases import session
from models.databases import WorkflowModel
import time
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from config.log_settings import LoggingCls
import json
from config.setting import CONFIG
import os
import sys

logger = LoggingCls.get_logger()

class WorkflowModelImpl(WorkflowModel):

    @classmethod
    def init_default_workflow(cls):
        workflow_1 = session.query(cls).filter(cls.id == 1).first()
        workflow_2 = session.query(cls).filter(cls.id == 2).first()
        session.close()
        if workflow_1 and workflow_1.is_default != 1:
            #更新为默认配置
            data = {}
            data["is_default"] = 1
            cls.update(1, data)

        if workflow_2 and workflow_2.is_default != 1:
            #更新为默认配置
            data = {}
            data["is_default"] = 1
            data["setup_process"] =  {
                "llm_info": {
                    "name": "Qwen2.5-32B-Instruct-GPTQ-Int8",
                    "llm_id": 3
                }, 
                "pre_process_info":None
            }
            cls.update(2, data)
        if workflow_1 is None:
            #新增默认配置
            data_1 = {}
            data_1["id"] = 1
            data_1["name"] = "默认工作流_包含OCR"
            data_1["description"] = "内置默认工作流,包含OCR数据前处理"
            data_1["setup_process"] =  {
                    "llm_info": {
                        "name": "Qwen2.5-32B-Instruct-GPTQ-Int8",
                        "llm_id": 3
                    }, 
                    "pre_process_info":[ {
                        "name": "OCR识别",
                        "ocr_id": 1
                    }]
                }
            data_1["enable"] = False
            data_1["is_default"] = 1
            data_1["user"] = None
            cls.create(data_1)
        if workflow_2 is None:
             #新增默认配置
            data_2 = {}
            data_2["id"] = 2
            data_2["name"] = "默认工作流"
            data_2["description"] = "内置默认工作流,不包含OCR数据前处理,只有大模型"
            data_2["setup_process"] =  {
                    "llm_info": {
                        "name": "Qwen2.5-32B-Instruct-GPTQ-Int8",
                        "llm_id": 3
                    }, 
                    "pre_process_info":None
                }
            data_2["enable"] = False
            data_2["is_default"] = 1
            data_2["user"] = None
            cls.create(data_2)

    @classmethod
    def get_all(cls,params):
        logger.debug("params: {}".format(params))
        cls.init_default_workflow() #检查并更新默认配置
        query = session.query(cls)
        total = 0
        page = 1
        count = 20
        user = None
        if len(params) > 0:
            page = int(params.get('page'))
            count = int(params.get('count'))
            stime = params.get('stime')
            etime = params.get('etime')
            name = params.get('name')
            if params.get('user'):
                user = params.get('user')

            
            query = query.filter(cls.user == user)
            if name:
                query = query.filter(cls.name.like(f"%{name}%"))
            if stime and etime:
                query = query.filter(cls.create_time.between(stime, etime))
            elif stime and not etime:
                query = query.filter(cls.create_time >= stime)
            elif etime and not stime:
                query = query.filter(cls.create_time <= etime)
            total = query.count()
            query = query.order_by(cls.create_time.desc()).limit(count).offset((page - 1) * count)
        else:
            total = query.count()
            query = query.order_by(cls.create_time.desc()).limit(count).offset((page - 1) * count)

       
        results = query.all()   
        session.close()

        workflow_list = session.query(cls).filter(cls.is_default == 1).all()
        session.close()

        workflows = []
        for workflow in workflow_list:
            if workflow:
                workflows.append(workflow.to_dict())  

        for result in results:
            if result.is_default == 1:
                continue
            workflows.append(result.to_dict())  
        
        resp = {
        'total': total,
        'page': page,
        'count': count,
        'results': workflows
        }

        return resp

    @classmethod
    def get(cls, id):
        logger.debug("id: %d",id)
        workflow = session.query(cls).filter(cls.id == id).first()
        session.close()
        return workflow

    @classmethod
    def create(cls, data):
        workflow = cls(**data)
        #查询任务名称是否重复
        workflow_name = session.query(cls).filter(cls.name == data['name']).first()
        if workflow_name:
            raise Exception("工作流名称重复")
        
        session.add(workflow)
        session.commit()
        session.refresh(workflow)
        session.close()
        return workflow

    @classmethod
    def update(cls, id, data):
        workflow = session.query(cls).filter(cls.id == id).first()
        for key, value in data.items():
            setattr(workflow, key, value)
        session.commit()
        session.refresh(workflow)
        session.close()
        return workflow

    @classmethod
    def delete(cls, id):
        workflow = session.query(cls).filter(cls.id == id).first()
        if workflow is None:
            raise Exception(f"您要删除的id为{id}的记录不存在")
        if workflow.enable == True:
            raise Exception("工作流已启用，无法删除")
        if workflow.is_default == 1:
            raise Exception("内置工作流，不可删除")
        session.delete(workflow)
        session.commit()
        session.close()
        return workflow

    @classmethod
    def export_workflow(cls,data):
        DOWNLOAD_FOLDER = CONFIG["export_file_path"]
        if getattr(sys, 'frozen', False):
            # 如果是打包后的应用程序
            base_path = sys._MEIPASS
            DOWNLOAD_FOLDER = os.path.join(base_path, CONFIG["export_file_path"])
        if not os.path.exists(DOWNLOAD_FOLDER):
            os.makedirs(DOWNLOAD_FOLDER)

        os.system(f"rm -rf {DOWNLOAD_FOLDER}/*.json")
        doc_name = data["name"]
        file_name = f"{doc_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
        # 将数据写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        proxy_path ="/api/v1/workflows/llm/downloads/"+file_name
        export_data = {
            "name": file_name,
            "path": proxy_path
        }
        return export_data
    
    @classmethod
    def get_workflow_list(cls,params):
        user = None
        if params.get("user"):
            user = params.get("user")
        logger.info(f"user:{user}")

        if user is None:
            raise Exception("user 为必填字段") 
        workflow_list = session.query(cls).filter(cls.user == user).all()
        session.close()
        default_workflow_list = session.query(cls).filter(cls.is_default == 1).all()
        session.close()
        workflowlist = []
      
        for default_workflow in default_workflow_list:
            if default_workflow:
                workflowlist.append({"id":default_workflow.id,"name":default_workflow.name,"is_default":1})

        for workflow in workflow_list:
            if workflow.is_default == 1:
                continue
            workflowlist.append({"id":workflow.id,"name":workflow.name,"is_default":workflow.is_default})

        return workflowlist
    

    @classmethod
    def clone(cls,id,params):
        name = params.get("name")
        if name is None:
            raise Exception("工作流名称不能为空")
        origin_workflow = session.query(cls).filter(cls.id == id).filter(cls.name == name).first()
        if origin_workflow is None:
            raise Exception("未查询到该工作流信息")
        
        if origin_workflow.is_default == 1:
            raise Exception("内置工作流不可创建副本")
        
        data = origin_workflow.to_dict()
        del data["id"]
        origin_name = origin_workflow.name
        user = origin_workflow.user

        v1 = 1
        while True:
            new_name = f"{origin_name}_副本({v1})"
            workflow = session.query(cls).filter(cls.name == new_name).filter(cls.user == user).first()
            v1 += 1
            if workflow:
                session.close()
                continue
            else:
                data["name"] = new_name
                clone_workflow = cls(**data)
                session.add(clone_workflow)
                session.commit()
                session.refresh(clone_workflow)
                session.close() 
                break
        return   clone_workflow                