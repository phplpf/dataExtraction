from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean, UniqueConstraint, Index,func
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from models.databases import session
from models.databases import TemplatesModel,TemplatesTestModel
import json
from config.setting import CONFIG
import os
from services.llm import LLMEngine
import time
from config.log_settings import LoggingCls
from utils.utils import natural_sort_key
from services.workflow import WorkflowModelImpl
from services.modelservice import ModelServiceModelImpl
from utils.utils import ServiceLogger
import sys
import sqlite3
import traceback
import threading
from services.images import ImagesPushImpl

logger = LoggingCls.get_logger()

class TemplatesModelImpl(TemplatesModel):
    @classmethod
    def get_all(cls,params):
        logger.debug("params: {}".format(params))
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
                query = query.filter(cls.name == name)
            if stime:  
                query = query.filter(cls.create_time >= stime)
            if etime:
                query = query.filter(cls.create_time <= etime)

            # 获取总条数
            total = query.count()
          # 分页
        query = query.order_by(cls.create_time.desc())
        results = query.limit(count).offset((page - 1) * count).all() 
        session.close()
        results_list = [
            {'id': table.id, 
             'name': table.name, 
             'description': table.description,
             'workflow_id': table.workflow_id,
             'entities_info': table.entities_info, 
             'rule_info':      table.rule_info,
             'last_update_time': table.last_update_time,
             'delete_status': table.delete_status,
             'create_time': table.create_time,
             'user': table.user,
             'enable': table.enable} for table in results]
        resp = {
            'total': total,
            'page': page,
            'count': count,
            'results': results_list
        }
        return resp

    @classmethod
    def get(cls, id):
        logger.debug("id: %d",id)
        template = session.query(cls).filter(cls.id == id).first()
        session.close()
        return template

    @classmethod
    def create(cls, data):
        data = dict(data)
        table_params = {}
        table_params['name'] = data.get('name')
        table_params['description'] = data.get('description')
        table_params['workflow_id'] = data.get('workflow_id')
        table_params['entities_info'] = data.get('entity_configs')
        table_params['rule_info'] = data.get('rule_prompt_config')
        table_params['enable'] = data.get('enable')
        table_params['user'] =  data.get('user') if data.get('user') != None else "admin"
        table_params["delete_status"] = False
        template = cls(**table_params)
        session.add(template)
        session.commit()
        session.refresh(template)
        session.close()
        return template

    @classmethod
    def update(cls, id, data):
        template = session.query(cls).filter(cls.id == id).first()
        # count = session.query(func.count(TemplatesTestModel.id)).filter(TemplatesTestModel.template_id == id,TemplatesTestModel.status.in_([0, 1])).scalar()
        # if count > 0:
        #     raise Exception("模板已启用，存在未完成的测试任务，无法修改")
        for key, value in data.items():
            setattr(template, key, value)
        session.commit()
        session.refresh(template)
        session.close()
        return template

    @classmethod
    def delete(cls, id):
        template = session.query(cls).filter(cls.id == id).first()
        if template.enable == True:
            raise Exception("模板已启用，无法删除")
        session.delete(template)
        session.commit()
        session.close()

    @classmethod
    def get_entites(cls):
        if len(CONFIG["entities"]) == 0:
            return []
        return CONFIG["entities"]

    @classmethod
    def export_template(cls,data):
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
        
        proxy_path ="/api/v1/templates/llm/downloads/"+file_name
        export_data = {
            "name": file_name,
            "path": proxy_path
        }
        return export_data
    
    @classmethod
    def images_push(cls,data):
        try:
            if data["data"] is None:
                return
            if len(data["data"]) > 0:
                # 初始化sqlite数据库创建三张表
                conn = sqlite3.connect(CONFIG["sqlite_db_config"]["db"])
                cursor = conn.cursor()

                # Drop all existing data
                cursor.execute("DROP TABLE IF EXISTS templates")
                cursor.execute("DROP TABLE IF EXISTS tasks")
                cursor.execute("DROP TABLE IF EXISTS workflows")
                cursor.execute("DROP TABLE IF EXISTS modeservice_table")
                # Create tables
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        content TEXT NOT NULL
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        status TEXT NOT NULL,
                        content TEXT NOT NULL
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workflows (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        content TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS modeservice_table (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        content TEXT NOT NULL
                    )
                """)

                for template_id in data["data"]:
                    print("template_id:",template_id)

                    #调用达模型处理测试任务
                    workflow_data = None
                    template_data = session.query(TemplatesModel).filter(TemplatesModel.id == template_id).first()
                    #查找出工作流信息
                    if template_data:
                        cursor.execute("SELECT * FROM templates WHERE id = ?", (template_data.id,))
                        row = cursor.fetchone()
                        if row:
                            cursor.execute("UPDATE templates SET name = ?,content=?  WHERE id = ?", (template_data.name, json.dumps(template_data.to_dict()),template_data.id))
                        else:
                            cursor.execute(f"INSERT INTO templates (name, content) VALUES (?, ?)", (template_data.name, json.dumps(template_data.to_dict())))

                        workflow_data = WorkflowModelImpl.get(template_data.workflow_id)
                        if workflow_data:
                            cursor.execute("SELECT * FROM workflows WHERE id = ?", (workflow_data.id,))
                            row = cursor.fetchone()
                            if row:
                                cursor.execute("UPDATE workflows SET name = ?,content= ? WHERE id = ?", (workflow_data.name, json.dumps(workflow_data.setup_process),workflow_data.id))
                            else:
                                cursor.execute(f"INSERT INTO workflows (name, content) VALUES (?, ?)", (workflow_data.name, json.dumps(workflow_data.setup_process)))

                    #数据前处理
                    if workflow_data is None:
                        conn.commit()
                        conn.close()
                        return 
                    pre_process_list = workflow_data.setup_process["pre_process_info"]
                    if pre_process_list is not None and len(pre_process_list) > 0:
                        for proc in pre_process_list:
                            ocr_id = proc["ocr_id"]
                            try:
                                ocr_data = ModelServiceModelImpl.get(ocr_id,1)
                                cursor.execute("SELECT * FROM modeservice_table WHERE id = ?", (ocr_id,))
                                row = cursor.fetchone()
                                if row:
                                    cursor.execute("UPDATE modeservice_table SET name = ?,content= ? WHERE id = ?", (ocr_data["name"],json.dumps(ocr_data["api_info"]) ,ocr_id))
                                else:
                                    cursor.execute(f"INSERT INTO modeservice_table (name, content) VALUES (?, ?)", (ocr_data["name"], json.dumps(ocr_data["api_info"])))

                            except Exception as e:
                                print(e)
                                continue
        
                    #算法基座
                    llm_info = workflow_data.setup_process["llm_info"]
                    llm_id = llm_info["llm_id"]
                    llm_data = ModelServiceModelImpl.get(llm_id,2)
                    if  llm_data:
                        cursor.execute("SELECT * FROM modeservice_table WHERE id = ?", (llm_id,))
                        row = cursor.fetchone()
                        if row:
                            cursor.execute("UPDATE modeservice_table SET name = ?,content=  WHERE id = ?", (llm_data["name"], json.dumps(llm_data["api_info"]),workflow_data.id))
                        else:
                            cursor.execute(f"INSERT INTO modeservice_table (name, content) VALUES (?, ?)", (llm_data["name"], json.dumps(llm_data["api_info"])))
                conn.commit()
                conn.close()

                #启动一个线程用来生成镜像并推送
                t = threading.Thread(target=ImagesPushImpl.push,args=(data["id"],))
                t.start()
        except Exception as e:
            traceback.print_exc()

            
#模板测试任务
class TemplatesTestModelImpl(TemplatesTestModel):
    @classmethod
    def contrable_clear_tasks(cls):
        """
        desc:定时清除测试任务
        当表中数据大于1000条时,只保留最新100条数据
        当表中数据创建时间大于7天时,删除7天前的数据
        两个条件满足任何一个都会执行
        """
        while CONFIG["crontab"]["enable"]:
            try:
                print("定时清除测试任务线程进行中")
                """ 定时清除测试任务 """
                total = session.query(cls).count()
                if total > CONFIG["crontab"]["max_count"]:
                    session.query(cls).order_by(cls.create_time.desc()).limit(total - 100).delete()
                    session.commit()
                    session.close()
                    time.sleep(60 * CONFIG["crontab"]["sleep_time"])
                    continue

                now_time = int(time.time())
                delete_time = now_time - CONFIG["crontab"]["keep_days"] * 24 * 60 * 60
                # 获取当前日期（2025-02-07）
                today = datetime.today().date()
                # 当天开始时间（00:00:00）
                start_time = datetime.combine(today, datetime.min.time())
                # 当天结束时间（23:59:59）
                end_time = datetime.combine(today, datetime.max.time())
                # 转换为时间戳
                start_timestamp = int(start_time.timestamp())
                end_timestamp = int(end_time.timestamp())
                result = session.query(cls).order_by(cls.create_time.desc()).first()
                if result:
                    if result.create_time >= start_timestamp and result.create_time <= end_timestamp:
                        session.query(cls).filter(cls.create_time < delete_time).delete()
                        session.commit()
                        session.close()
                time.sleep(60 * CONFIG["crontab"]["sleep_time"])
            except Exception as e:
                print(e)
                time.sleep(60 * CONFIG["crontab"]["sleep_time"])
    
    @classmethod
    def get_tests(cls,template_id,id):
        test = session.query(cls).filter(cls.template_id == template_id,cls.id == id).first()
        session.close()
        return {"content":json.loads(test.results)}
    
    @classmethod
    def get_test(cls,template_id,id):
        test = session.query(cls).filter(cls.template_id == template_id,cls.id == id).first()
        session.close()
        return test

    @classmethod
    def create(cls, data,file_path):
        test = cls(**data)
        #检查测试名称是否重复
        test_name = session.query(cls).filter(cls.name == data['name']).filter(cls.template_id == data['template_id']).first()
        if test_name:
            raise Exception("模板测试任务名称重复")

        session.add(test)
        session.commit()
        session.refresh(test)
        session.close()
              
        #调用达模型处理测试任务
        template_data = session.query(TemplatesModel).filter(TemplatesModel.id == data['template_id']).first()
        try:
            llm_config = None
            workflow_data = WorkflowModelImpl.get(template_data.workflow_id)
            if workflow_data == None:
                raise Exception("工作流不存在")
            
            setup_process = workflow_data.setup_process
            if "llm_info" not in setup_process:
                raise Exception("工作流未配置（算法基座）")
            if "pre_process_info" not in setup_process:
                raise Exception("工作流未配置（数据前处理）")
            
            #数据前处理
            pre_process_list = setup_process["pre_process_info"]
            preprocess_config_list = []
            if pre_process_list is not None and len(pre_process_list) > 0:
                for proc in pre_process_list:
                    ocr_id = proc["ocr_id"]
                    try:
                        ocr_data = ModelServiceModelImpl.get(ocr_id,1)
                    except Exception as e:
                        print(e)
                        continue
                    preprocess_config_list.append({"id":ocr_data["id"],"name":ocr_data["name"],"api_info":ocr_data["api_info"]})

            #算法基座
            llm_info = setup_process["llm_info"]
            llm_id = llm_info["llm_id"]
            llm_data = ModelServiceModelImpl.get(llm_id,2)
            if llm_data == None:
                raise Exception("模型服务信息不存在")

            if "api_info" not in llm_data:
                raise Exception("模型服务链接信息不存在")

            api_info = llm_data["api_info"]
            llm_config = {
                "id":llm_id,
                "model": llm_info["name"],
                "api_info": api_info,
                "preprocess_infos":preprocess_config_list
            }
            print("llm_config:",llm_config)
        except Exception as e:
            logger.error(e)
            print(f"大模型服务配置错误:{str(e)}")
            ServiceLogger.error(test.id,"大模型模板配置","大模型服务配置错误: %s"%str(e))
       

        LLMEngine.run(cls.callback_func,template_data.to_dict(), file_path,data["test_file"],data['template_id'],test.id,llm_config)

        return test

    @classmethod
    def update(cls, id, data):
        test = session.query(cls).filter(cls.id == id).first()
        for key, value in data.items():
            setattr(test, key, value)
        session.commit()
        session.refresh(test)
        session.close()
        return test

    @classmethod
    def delete(cls, id):
        test = session.query(cls).filter(cls.id == id).first()
        session.delete(test)
        session.commit()
        session.close()

    @classmethod
    def get_all(cls,id,params):
        query = session.query(cls)
        total = 0
        page = 1
        count = 20
        user = None
        if len(params) > 0: 
            if params.get('page'):  
                page = int(params.get('page'))
            if params.get('count'):
                count = int(params.get('count'))
            stime = params.get('stime') 
            etime = params.get('etime')
            name = params.get('name')
            filename = params.get('filename')
            if params.get('user'):
                user = params.get('user')
                
            query = query.filter(cls.template_id == id)
            if user:
                query = query.filter(cls.user == user)
            if name:
                query = query.filter(cls.name.like(f"%{name}%"))
            if stime:
                query = query.filter(cls.create_time >= stime)
            if etime:
                query = query.filter(cls.create_time <= etime)
            if filename:
                query = query.filter(cls.test_file.like(f"%{filename}%"))

            # 获取总条数
            total = query.count()
          # 分页
        query = query.order_by(cls.create_time.desc())
        results = query.limit(count).offset((page - 1) * count).all() 
        session.close()
        results_list = [
            {'id': table.id, 
             'template_id': table.template_id, 
             'name': table.name, 
             'description': table.description,
             'test_file': table.test_file,
             'test_type': table.test_type,
             'test_type_name': table.test_type_name,
             'status': table.status,
             'last_update_time': table.last_update_time,
             'delete_status': table.delete_status,
             'create_time': table.create_time,
             'user': table.user} for table in results
        ]
        resp = {
            'total': total,
            'page': page,
            'count': count,
            'results': results_list
        }
        return resp

    @classmethod
    def get(cls, id):
        test = session.query(cls).filter(cls.id == id).first()
        session.close()
        return {"id":test.id,"name":test.name,"status":test.status}
    

    @classmethod
    def callback_func(cls,results,status,template_id,id):
        """" 回调函数  更新抽取结果到数据库 """ 
        test = session.query(cls).filter(cls.id == id).filter(cls.template_id == template_id).first()
        if results != None:
            test.results = json.dumps(results, ensure_ascii=False)
        test.status = status
        session.commit()
        session.refresh(test)
        session.close()

    @classmethod
    def get_image_list(cls,template_id,task_id):
        #获取图片列表
        try:
            download_file_path = CONFIG["export_file_path"]
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
                download_file_path = os.path.join(base_path, CONFIG["export_file_path"])
            image_path = "%s/%d/%d" % (download_file_path,template_id,task_id)
            img_path_list = [os.path.join(f'/api/v1/templates/llm/downloads/{template_id}/{task_id}',image) for image in os.listdir(image_path)]
            img_path_list = sorted(img_path_list, key=natural_sort_key)
            return img_path_list
        except Exception as e:
            logger.error(e)
            return []    

    
