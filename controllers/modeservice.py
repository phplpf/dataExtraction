from flask import request,send_from_directory
from flask_restx import Resource, Namespace, fields, abort
from services.modelservice import ModelServiceModelImpl,ModelServiceTypeModelImpl
from views.modelservice import  format_modelservices, format_modelservice, handle_error,format_modelservice_delete
from config.log_settings import LoggingCls
from config.setting import CONFIG
import json
import os
import traceback
import sys
import uuid
import utils.utils as utils

logger = LoggingCls.get_logger()

ns = Namespace('api/v1/modelservices', description='Task operations')

@ns.route('/ocr')
class ModelServiceList(Resource):
    @ns.doc('list_modelservices_ocr')
    @ns.param('page', '当前页数',required=False, type='int',default=1)
    @ns.param('count', '展示条数',required=False, type='int',default=20)
    @ns.param('user',  '用户',required=False, type='string')
    @ns.param('name', '名称',required=False, type='string')
    @ns.param('model_type_id',  '前处理类型',required=False, type='int')
    def get(self):
        try:
            """ ocr服务列表 """
            logger.info("ocr服务列表")
            params = request.args
            modelservices = ModelServiceModelImpl.get_all(params,1)
            if not modelservices:
                return handle_error(404, "No modelservices found")  # 如果没有任务，返回错误
            return format_modelservices(modelservices)  # 使用视图层格式化数据
        except Exception as e:
            return {'message': str(e)}, 500
        
    @ns.doc('create_modelservice_ocr')
    def post(self):
        try:
            """ 新建ocr服务 """
            logger.info("新建ocr服务")
            if 'img_path' not in request.files:
                return {'message': 'No file part'}, 400
            uploaded_file = request.files['img_path']
            if uploaded_file.filename == '':
                return {'message': 'No selected img_path'}, 400
            name = request.form.get('name')
            description = request.form.get('description')
            api_info = request.form.get('api_info')
            user = request.form.get('user')
            model_type_id = request.form.get('model_type_id')
            
            if not name :
                return {'message': 'Name are required'}, 400
            if not description:
                return {'message': 'Description are required'}, 400
            if not api_info:
                return {'message': 'Api info are required'}, 400
            if not user:                
                return {'message': 'User are required'}, 400
            
            # 确保文件类型正确
            filename = uploaded_file.filename
            allowed_extensions = {'.jpg', '.png','.jpeg','.icon' }
            if os.path.splitext(filename)[1].lower() not in allowed_extensions:
                return {'message': 'Unsupported file type'}, 400
            
            # 保存文件到指定目录
            UPLOAD_FOLDER = CONFIG["import_file_path"]
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
                UPLOAD_FOLDER = os.path.join(base_path, CONFIG["import_file_path"])
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            #将filename变量中文件名部分替换为uuid
            # 提取扩展名
            ext = os.path.splitext(filename)[1]
            filename = f"{uuid.uuid4()}{ext}"
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(image_path)

              # 将文件内容与其他参数结合
            data = {
                "name": name,
                "description": description,
                "img_path": image_path,
                "service_type": 1,
                "model_type_id": model_type_id,
                "api_info": api_info,
                "user": user
            }
            print("data:",data)
            modelservice = ModelServiceModelImpl.create(data)
            return format_modelservice(modelservice.to_dict()), 201  # 使用视图层格式化并返回新创建的任务
        except Exception as e:
            return {'message': str(e)}, 500

@ns.route('/ocr/<int:id>')
@ns.param('id', 'The modelservices identifier')
class ModelServiceResource(Resource):
    @ns.doc('get_modelservice_ocr')
    def get(self, id):
        try:
            """ 获取ocr服务 """
            logger.info("获取ocr服务")
            modelservice = ModelServiceModelImpl.get(id,1)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice(modelservice)  # 使用视图层格式化返回
        except Exception as e:
            return {'message': str(e)}, 500
        
    @ns.doc('delete_modelservice_ocr')    
    def delete(self, id):
        try:
            """ 删除ocr服务 """
            logger.info("删除ocr服务")
            modelservice = ModelServiceModelImpl.delete(id,1)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice_delete(), 200
        except Exception as e:
            return {'message': str(e)}, 500
        
    @ns.doc('update_modelservice_ocr')
    def put(self, id):
        try:
            """ 修改ocr服务 """
            logger.info("修改ocr服务")
            name = request.form.get('name')
            description = request.form.get('description')
            api_info = request.form.get('api_info')
            user = request.form.get('user')
            model_type_id = request.form.get('model_type_id')
            is_default = request.form.get('is_default')
            image_path = None

            if 'img_path' in request.files:      
                uploaded_file = request.files['img_path']
                if uploaded_file.filename: 
                    # 确保文件类型正确
                    filename = uploaded_file.filename
                    allowed_extensions = {'.jpg', '.png','.jpeg','.icon' }
                    if os.path.splitext(filename)[1].lower() not in allowed_extensions:
                        return {'message': 'Unsupported file type'}, 400
                
                    # 保存文件到指定目录
                    UPLOAD_FOLDER = CONFIG["import_file_path"]
                    if id in [1,2] or is_default == 1:
                       UPLOAD_FOLDER = os.path.join(CONFIG["import_file_path"],"pre_ocr_card") 
                    if getattr(sys, 'frozen', False):
                        # 如果是打包后的应用程序
                        base_path = sys._MEIPASS
                        if id in [1,2] or is_default == 1:
                            UPLOAD_FOLDER = os.path.join(base_path, UPLOAD_FOLDER)
                        else:
                            UPLOAD_FOLDER = os.path.join(base_path, CONFIG["import_file_path"])

                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)
                    # 提取扩展名
                    ext = os.path.splitext(filename)[1]
                    filename = f"{uuid.uuid4()}{ext}"
                    image_path = os.path.join(UPLOAD_FOLDER, filename)
                    uploaded_file.save(image_path)

            data = {}
            data["id"] = id
            data["service_type"] = 1
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if api_info:
                data["api_info"] = api_info
            if user:
                data["user"] = user
            if image_path:
                data["img_path"] = image_path
            if model_type_id:
                data["model_type_id"] = model_type_id

            if len(data) < 3:
                return handle_error(400, f'missing params')
            modelservice = ModelServiceModelImpl.update(id, data)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice(modelservice)  # 使用视图层格式化更新后的任务
        except Exception as e:
            return {'message': str(e)}, 500
        

@ns.route('/ocr/infos')
class ModelServiceInfos(Resource):
    @ns.doc('get_modelservice_infos')
    def get(self):
        try:
            """ 获取ocr服务信息 """
            logger.info("获取ocr服务信息")
            params = request.args
            modelservices = ModelServiceModelImpl.get_ocr_infos(params)
            if not modelservices:
                return handle_error(404, "No modelservices found")  # 如果没有任务，返回错误
            return format_modelservices(modelservices)  # 使用视图层格式化数据
        except Exception as e:
            return {'message': str(e)}, 500
        
    
@ns.route('/ocr/<int:id>/test')
@ns.param('id', 'The modelservices identifier')
class ModelServiceTestResource(Resource):
    @ns.doc('test_modelservice_ocr')
    def post(self, id):
        try:
            """ 测试ocr服务 """
            logger.info("测试ocr服务")
            utils.ServiceLogger.info(id,"数据前处理",f"id为{id}的前处理算法，开始数据前处理测试请求")
            if 'file' not in request.files:
                return {'message': 'No file part'}, 400
            uploaded_file = request.files['file']
            if uploaded_file.filename == '':
                return {'message': 'No selected file'}, 400
            
            filename = uploaded_file.filename
            content = request.form.get('content')

             # 保存文件到指定目录
            UPLOAD_FOLDER = CONFIG["import_file_path"]
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
                UPLOAD_FOLDER = os.path.join(base_path, CONFIG["import_file_path"])
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(image_path)

            data = {
                "id": id,
                "content": content,
                "img_path": image_path
            }
            utils.ServiceLogger.debug(id,"数据前处理",f"id为{id}的前处理算法,数据前处理入参格式：{data}")
            result = ModelServiceModelImpl.ocr_test(id, data)
            return format_modelservice(result)  # 使用视图层格式化返回
        except Exception as e:
            utils.ServiceLogger.error(id,"数据前处理",f"id为{id}的前处理算法执行出错：{str(e)}")
            return {'message': str(e)}, 500
        

@ns.route('/llm/base')
class ModelServiceList(Resource):
    @ns.doc('list_modelservices_llm_base')
    @ns.param('page', '当前页数',required=False, type='int',default=1)
    @ns.param('count', '展示条数',required=False, type='int',default=20)
    @ns.param('user',  '用户',required=False, type='string')
    @ns.param('name', '名称',required=False, type='string')
    @ns.param('model_type_id','模型类型',required=False,type='int')
    def get(self):
        try:
            """ 大模型基座服务列表 """
            logger.info("大模型基座服务列表")
            params = request.args
            modelservices = ModelServiceModelImpl.get_all(params,2)
            if not modelservices:
                return handle_error(404, "No modelservices found")  # 如果没有任务，返回错误
            return format_modelservices(modelservices),200  # 使用视图层格式化数据
        except Exception as e:
            traceback.print_exc()
            return {'message': str(e)}, 500
        
    @ns.doc('create_modelservice_llm_base')
    def post(self):
        try:
            """ 新建大模型基座服务 """
            logger.info("新建大模型基座服务")
            if 'img_path' not in request.files:
                return {'message': 'No file part'}, 400
            uploaded_file = request.files['img_path']
            if uploaded_file.filename == '':
                return {'message': 'No selected img_path'}, 400
            name = request.form.get('name')
            description = request.form.get('description')
            api_info = request.form.get('api_info')
            user = request.form.get('user')
            model_type_id = request.form.get('model_type_id')
            
            
            if not name :
                return {'message': 'Name are required'}, 400
            if not description:
                return {'message': 'Description are required'}, 400
            if not api_info:
                return {'message': 'Api info are required'}, 400
            if not user:                
                return {'message': 'User are required'}, 400
            
            # 确保文件类型正确
            filename = uploaded_file.filename
            allowed_extensions = {'.jpg', '.png','.jpeg','.icon' }
            if os.path.splitext(filename)[1].lower() not in allowed_extensions:
                return {'message': 'Unsupported file type'}, 400
            
            # 保存文件到指定目录
            UPLOAD_FOLDER = CONFIG["import_file_path"]
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
                UPLOAD_FOLDER = os.path.join(base_path, CONFIG["import_file_path"])
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
             # 提取扩展名
            ext = os.path.splitext(filename)[1]
            filename = f"{uuid.uuid4()}{ext}"
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(image_path)

              # 将文件内容与其他参数结合
            data = {
                "name": name,
                "description": description,
                "img_path": image_path,
                "service_type": 2,
                "model_type_id": model_type_id,
                "api_info": api_info,
                "user": user
            }
            modelservice = ModelServiceModelImpl.create(data)
            return format_modelservice(modelservice.to_dict()), 200  # 使用视图层格式化并返回新创建的任务
        except Exception as e:
            traceback.print_exc()
            return {'message': str(e)}, 500

@ns.route('/llm/base/<int:id>')
@ns.param('id', 'The modelservices identifier')
class ModelServiceResource(Resource):
    @ns.doc('get_modelservice_llm_base')
    def get(self, id):
        try:
            """ 获取大模型基座服务 """
            logger.info("获取大模型基座服务")
            modelservice = ModelServiceModelImpl.get(id,2)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice(modelservice)  # 使用视图层格式化返回
        except Exception as e:
            return {'message': str(e)}, 500
        
    @ns.doc('delete_modelservice_llm_base')    
    def delete(self, id):
        try:
            """ 删除大模型基座服务 """
            logger.info("删除大模型基座服务")
            modelservice = ModelServiceModelImpl.delete(id,2)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice_delete(), 200
        except Exception as e:
            return {'message': str(e)}, 500
        
    @ns.doc('update_modelservice_llm_base')
    def put(self, id):
        try:
            """ 修改大模型基座服务 """
            name = request.form.get('name')
            description = request.form.get('description')
            api_info = request.form.get('api_info')
            user = request.form.get('user')
            model_type_id = request.form.get('model_type_id')
            is_default = request.form.get('is_default')
            image_path = None
            print("id:",id)
            if 'img_path' in request.files:      
                uploaded_file = request.files['img_path']
                if uploaded_file.filename: 
                    # 确保文件类型正确
                    filename = uploaded_file.filename
                    allowed_extensions = {'.jpg', '.png','.jpeg','.icon' }
                    if os.path.splitext(filename)[1].lower() not in allowed_extensions:
                        return {'message': 'Unsupported file type'}, 400
                
                    # 保存文件到指定目录
                    UPLOAD_FOLDER = CONFIG["import_file_path"]
                    if id in [3,4] or is_default == 1:
                       UPLOAD_FOLDER = os.path.join(CONFIG["import_file_path"],"llm_card") 
                    if getattr(sys, 'frozen', False):
                        # 如果是打包后的应用程序
                        base_path = sys._MEIPASS
                        if id in [3,4] or is_default == 1:
                            UPLOAD_FOLDER = os.path.join(base_path, UPLOAD_FOLDER)
                        else:
                            UPLOAD_FOLDER = os.path.join(base_path, CONFIG["import_file_path"])
                    if not os.path.exists(UPLOAD_FOLDER):
                        os.makedirs(UPLOAD_FOLDER)

                     # 提取扩展名
                    ext = os.path.splitext(filename)[1]
                    filename = f"{uuid.uuid4()}{ext}"
                    image_path = os.path.join(UPLOAD_FOLDER, filename)
                    uploaded_file.save(image_path)

            data = {}
            data["id"] = id
            data["service_type"] = 2
            if name:
                data["name"] = name
            if description:
                data["description"] = description
            if api_info:
                data["api_info"] = api_info
            if user:
                data["user"] = user
            if image_path:
                data["img_path"] = image_path
            if model_type_id:
                data["model_type_id"] = model_type_id

            if len(data) < 3:
                return handle_error(400, f'missing params')
            modelservice = ModelServiceModelImpl.update(id, data)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice(modelservice)  # 使用视图层格式化更新后的任务
        except Exception as e:
            return {'message': str(e)}, 500
        
@ns.route('/llm/<int:id>/test')
class ModelServiceTestResource(Resource):
    @ns.doc('test_modelservice_llm')
    def post(self,id):
        try:
            """ 测试大模型服务 """
            logger.info("测试大模型服务")
            utils.ServiceLogger.info(id,"算法基座",f"id为{id}的大模型算法，开始数大模型测试请求")
            text = request.form.get('text')
            image_path = None
            file_content = None
            if 'file' in request.files:
                uploaded_file = request.files['file']
                if uploaded_file.filename == '':
                    return {'message': 'No selected file'}, 400
                filename = uploaded_file.filename
                # 保存文件到指定目录
                UPLOAD_FOLDER = CONFIG["import_file_path"]
                if getattr(sys, 'frozen', False):
                    # 如果是打包后的应用程序
                    base_path = sys._MEIPASS
                    UPLOAD_FOLDER = os.path.join(base_path, CONFIG["import_file_path"])
                if not os.path.exists(UPLOAD_FOLDER):
                    os.makedirs(UPLOAD_FOLDER)
                 # 提取扩展名
                ext = os.path.splitext(filename)[1]
                filename = f"{uuid.uuid4()}{ext}"
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                uploaded_file.save(image_path)

            data = {}
            data["id"] = id
            data["text"] = text
            if image_path:
                data["path"] = image_path

            utils.ServiceLogger.debug(id,"算法基座",f"id为{id}的大模型算法输入参数：{data}")
            result = ModelServiceModelImpl.llm_test(id, data)
            return format_modelservice(result)  # 使用视图层格式化返回
        except Exception as e:
            utils.ServiceLogger.error(id,"算法基座",f"id为{id}的大模型算法测试执行出错：{str(e)}")
            return {'message': str(e)}, 500

@ns.route('/llm/infos')
class ModelServiceInfos(Resource):
    @ns.doc('get_modelservice_infos')
    def get(self):
        try:
            """ 获取大模型服务信息 """
            logger.info("获取大模型服务信息")
            params = request.args
            modelservices = ModelServiceModelImpl.get_llm_infos(params)
            if not modelservices:
                return handle_error(404, "No modelservices found")  # 如果没有任务，返回错误
            return format_modelservices(modelservices)  # 使用视图层格式化数据
        except Exception as e:
            return {'message': str(e)}, 500
        

@ns.route('/downloads/<path:filename>')
class DownloadFile(Resource):
    def get(self, filename):
        try:
            upload_file_path =  CONFIG["import_file_path"]
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
                upload_file_path = os.path.join(base_path, CONFIG["import_file_path"])
                
            return send_from_directory(upload_file_path, filename, as_attachment=True)
        except FileNotFoundError:
            abort(404)  # 文件未找到时返回 404 错误@app.route('/downloads/<filename>')


@ns.route('/ocr/types')
class ModelServiceTypes(Resource):
    @ns.doc('get_modelservice_types')
    def get(self):
        try:
            """ 获取大模型服务类型 """
            logger.info("获取大模型服务类型")
            parms = request.args
            infos = ModelServiceTypeModelImpl.get_all(parms,1)
            if not infos:
                return handle_error(404, "No ModelServiceType found")  # 如果没有任务，返回错误
            return format_modelservices(infos)  # 使用视图层格式化数据
        except Exception as e:
            return {'message': str(e)}, 500
        
    @ns.doc('create_modelservice_type')
    def post(self):
        try:
            """ 新建大模型服务类型 """
            data = request.get_json()
            data["type"] = 1
            result = ModelServiceTypeModelImpl.create(data,1)
            return format_modelservice(result.to_dict()), 200  # 使用视图层格式化并返回新创建的任务
        except Exception as e:
            return {'message': str(e)}, 500
        
        
@ns.route('/ocr/<int:id>/type')
class ModelServiceType(Resource):
    @ns.doc('delete_modelservice_type')    
    def delete(self, id):
        try:
            """ 删除大模型服务类型 """
            logger.info("删除大模型服务类型")
            modelservice = ModelServiceTypeModelImpl.delete(id)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice_delete(), 200
        except Exception as e:
            return {'message': str(e)}, 500
        
    @ns.doc('update_modelservice_type')
    def put(self, id):
        try:
            """ 修改大模型服务类型 """
            print("id:",id)
            name = request.form.get('name')
            data = {}
            data["id"] = id
            if name:
                data["name"] = name
            modelservice = ModelServiceTypeModelImpl.update(id, data)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice(modelservice.to_dict())  # 使用视图层格式化更新后的任务
        except Exception as e:
            return {'message': str(e)}, 500

@ns.route('/llm/types')
class ModelServiceTypes(Resource):
    @ns.doc('get_modelservice_types')
    def get(self):
        try:
            """ 获取大模型服务类型 """
            logger.info("获取大模型服务类型")
            parms = request.args
            infos = ModelServiceTypeModelImpl.get_all(parms,2)
            if not infos:
                return handle_error(404, "No ModelServiceType found")  # 如果没有任务，返回错误
            return format_modelservices(infos)  # 使用视图层格式化数据
        except Exception as e:
            return {'message': str(e)}, 500
        
    @ns.doc('create_modelservice_type')
    def post(self):
        try:
            """ 新建大模型服务类型 """
            data = request.get_json()
            data["type"] = 2
            result = ModelServiceTypeModelImpl.create(data)
            return format_modelservice(result.to_dict()), 200  # 使用视图层格式化并返回新创建的任务
        except Exception as e:
            return {'message': str(e)}, 500
        
        
@ns.route('/llm/<int:id>/type')
class ModelServiceType(Resource):
    @ns.doc('delete_modelservice_type')    
    def delete(self, id):
        try:
            """ 删除大模型服务类型 """
            logger.info("删除大模型服务类型")
            modelservice = ModelServiceTypeModelImpl.delete(id)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice_delete(), 200
        except Exception as e:
            return {'message': str(e)}, 500
        
    @ns.doc('update_modelservice_type')
    def put(self, id):
        try:
            """ 修改大模型服务类型 """
            print("id:",id)
            name = request.form.get('name')
            data = {}
            data["id"] = id
            if name:
                data["name"] = name
            modelservice = ModelServiceTypeModelImpl.update(id, data)
            if not modelservice:
                return handle_error(404, f'Modelservice with id {id} not found')
            return format_modelservice(modelservice.to_dict())  # 使用视图层格式化更新后的任务
        except Exception as e:
            return {'message': str(e)}, 500