from typing import Any
from flask import request,send_from_directory,abort
from flask_restx import Resource, Namespace, abort
from services.templates import TemplatesModelImpl,TemplatesTestModelImpl
from services.workflow import WorkflowModelImpl
from views.templates import format_templates, format_template, handle_error,format_template_delete
import json
import os
import threading
from config.log_settings import LoggingCls
from config.setting import CONFIG
import sys

logger = LoggingCls.get_logger()

ns = Namespace('api/v1/templates/llm', description='Tempalte operations')
template_params = ns.model('Template', {})
upload_parser = ns.parser()
upload_parser.add_argument('file', location='files', type='FileStorage', required=True, help='File to be uploaded')


#定时清除测试任务
def contrable_clear_test_tasks():
    """ 定时清除测试任务 """
    th = threading.Thread(target=TemplatesTestModelImpl.contrable_clear_tasks)
    th.start()
    logger.info("定时清除测试任务线程开启")


@ns.route('/')
class TemplatesList(Resource):
    """ Shows a list of all Tempaltes, and lets you POST to add new tasks """
    @ns.doc('list_todos')
    @ns.param('page', '当前页数',required=False, type='int',default=1)
    @ns.param('count', '展示条数',required=False, type='int',default=20)
    @ns.param('stime', '开始时间',required=False, type='int')
    @ns.param('etime', '结束时间',required=False, type='int')
    @ns.param('name',  '文档名称',required=False, type='string')
    @ns.param('user',  '用户',required=False, type='string')
    # @ns.marshal_list_with(template_params)
    def get(self):
        """ 模板配置列表页 """
        logger.info("模板配置列表页")
        params = request.args
        templates = TemplatesModelImpl.get_all(params)
        if not templates:
            return handle_error(404, "No Tempaltes found")  # 如果没有任务，返回错误
        
        result = format_templates(templates)  # 使用视图层格式化数据
        # print("result2: %s"%result)
        return result
    
    @ns.doc('create_template/import_template')
    # @ns.expect(upload_parser)
    @ns.expect(template_params)
    def post(self):
        """ 新建模板/导入模板 """
        logger.info("新建模板/导入模板")
        # 判断请求体中是否包含文件
        if 'file' in request.files:
            # 读取并解析文件中的JSON数据
            uploaded_file = request.files['file']  # 获取上传的文件
            if uploaded_file and uploaded_file.filename.endswith('.json'):
                file_content = uploaded_file.read()
                try:
                    json_data = json.loads(file_content)
                except json.JSONDecodeError:
                    return {'message': 'Invalid JSON file content'}, 400
                
                # 使用从文件中解析的内容创建模板
                template = TemplatesModelImpl.create(json_data)
                return format_template(template.to_dict()), 201  # 返回新创建的模板
            else:
                return {'message': 'Please upload a valid JSON file'}, 415
        
        else:
            # 如果没有上传文件，则尝试解析请求体中的JSON数据
            data = request.get_json()
            if not data:
                return {'message': 'No template data provided'}, 400

            # 使用请求体中的JSON数据创建模板
            template = TemplatesModelImpl.create(data)
            return format_template(template.to_dict()), 201  # 返回新创建的模板
    

@ns.route('/<int:id>')
@ns.response(404, 'templates not found')
@ns.param('id', 'The task identifier')
class TemplatesResource(Resource):
    """ Show a single templates item and lets you delete them """

    def get(self, id):
        """ 查看模板详情 """
        logger.info("查看模板详情")
        template = TemplatesModelImpl.get(id)
        if not template:
            return handle_error(404, f'templates with id {id} not found')
        return format_template(template.to_dict())  # 使用视图层格式化返回

    def delete(self, id):
        try:
            """ 删除模板 """
            logger.info("删除模板")
            template = TemplatesModelImpl.get(id)
            if not template:
                return handle_error(404, f'templates with id {id} not found')
            TemplatesModelImpl.delete(id)
            return format_template_delete(), 200  # 返回 204 响应，表示删除成功
        except Exception as e:
            return {'message': str(e)}, 500
    
    @ns.doc('update_template')
    @ns.expect(template_params)
    def put(self, id):
        try:
            """ 修改模板 """
            logger.info("修改模板")
            data = request.get_json()
            template = TemplatesModelImpl.update(id, data)
            if not template:
                return handle_error(404, f'Template with id {id} not found')
            return format_template(template.to_dict())  # 使用视图层格式化更新后的任务
        except Exception as e:
            return {'message': str(e)}, 500
        

@ns.route('/<int:id>/export')
@ns.response(404, 'templates not found')
class TemplatesExportResource(Resource):
    def get(self, id):
        """ 导出模板 """
        logger.info("导出模板")
        template = TemplatesModelImpl.get(id)
        if not template:
            return handle_error(404, f'templates with id {id} not found')
        export_data = TemplatesModelImpl.export_template(template.to_dict())
        return format_template(export_data)
        
       
    
@ns.route('/entities')    
class  TemplatesEntitesResource(Resource):

    def get(self):
        """ 实体列表 """
        logger.info("实体列表")
        entites = TemplatesModelImpl.get_entites()
        if len(entites) == 0:
            return handle_error(404, "No entites found")  # 如果没有任务，返回错误
        
        result = format_template(entites)  # 使用视图层格式化数据
        # print("result2: %s"%result)
        return result

@ns.route('/workflows')   
class GetWorkFlowListResource(Resource):
    def get(self):
        """ 工作流列表 """
        logger.info("工作流列表")
        params = request.args
        if len(params) == 0 or "user" not in params:
            return handle_error(400, "缺少user参数")  # 如果没有任务，返回错误 
        workflows = WorkflowModelImpl.get_workflow_list(params)
        if len(workflows) == 0:
            return handle_error(404, "No Workflows found")  # 如果没有任务，返回错误 
        result = format_template(workflows)  # 使用视图层格式化数据
        return result
    
@ns.route('/<int:template_id>/tests', defaults={'task_id': None})
@ns.route('/<int:template_id>/tests/<int:task_id>')
class  TemplatesTestsResource(Resource):
    @ns.doc('list_tests')
    @ns.param('page', '当前页数',required=False, type='int',default=1)
    @ns.param('count', '展示条数',required=False, type='int',default=20)
    @ns.param('name', '测试文档名称',required=False, type='string')
    @ns.param('filename', '测试文件名称',required=False, type='string')
    @ns.param('user',  '用户',required=False, type='string')
    def get(self,template_id,task_id):
        """ 测试任务列表/单个测试任务 """
        logger.info("测试任务列表/单个测试任务")
        if task_id is not None:
            template = TemplatesModelImpl.get(template_id)
            if not template:
                return handle_error(404, f'templates with id {template_id} not found')
            tests = TemplatesTestModelImpl.get_test(template_id,task_id)
            if not tests:
                return handle_error(404, f'tests with id {task_id} not found')
            return format_template(tests.to_dict())
        else:
            params = request.args
            templates = TemplatesTestModelImpl.get_all(template_id,params)
            if not templates:
                return handle_error(404, "No Tempaltes found")  # 如果没有任务，返回错误
            
            result = format_templates(templates)  # 使用视图层格式化数据
            # print("result2: %s"%result)
            return result
    

@ns.route('/<int:template_id>/tests/<int:task_id>/results')
class TemplatesTestResultResource(Resource):
    def get(self,template_id,task_id):   
        """ 查看测试任务结果 """
        logger.info("查看测试任务结果")
        tests = TemplatesTestModelImpl.get_tests(template_id,task_id)
        if not tests:
            return handle_error(404, f'tests with id {task_id} not found')
        result = format_template(tests)
        return result

@ns.route('/<int:template_id>/tests/<int:task_id>/images')
class TemplatesTestGetImageList(Resource):
    def get(self,template_id,task_id):
        """ 获取文档分页列表 """
        logger.info("获取文档分页列表")
        image_list = TemplatesTestModelImpl.get_image_list(template_id,task_id)
        return format_template(image_list)


@ns.route('/<int:id>/test')    
class  TemplatesTestResource(Resource):
    def get(self,id):
        """ 查看测试任务状态 """
        logger.info("查看测试任务状态")
        testinfo = TemplatesTestModelImpl.get(id)
        if not testinfo:
            return handle_error(404, f'test with id {id} not found')
        result = format_template(testinfo)
        return result
        
    @ns.doc('create_test')
    def post(self,id):
        """ 新建测试任务 """
        logger.info("新建测试任务")
        template_info = TemplatesModelImpl.get(id)
        if not template_info:
            return handle_error(404, f'template with id {id} not found')
        if template_info.enable == False:
            # return Exception("模板未启用，无法创建测试任务")
            return handle_error(500, "模板未启用，无法创建测试任务")
        
        if 'file' not in request.files:
            return {'message': 'No file part'}, 400
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return {'message': 'No selected file'}, 400
        name = request.form.get('name')
        description = request.form.get('description')

        if not name or not description:
            return {'message': 'Name and description are required'}, 400

        # 确保文件类型正确
        filename = uploaded_file.filename
        allowed_extensions = {'.pdf', '.doc','.docx', '.csv', '.xlsx','.txt','.jpeg','.jpg','.png','.gif','.bmp','.tif','.tiff','.webp'}
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
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        uploaded_file.save(file_path)
        logger.info("文件保存成功: %s"%file_path)


        # 读取文件内容
        # file_content = read_file_content(file_path)
        # file_content = read_docx_by_page(file_path,2000)
        # if file_content is None:
        #     return {'message': 'Failed to read file content'}, 500

        # 将文件内容与其他参数结合
        data = {
            'template_id': id,
            'name': name,
            'description': description,
            'test_file':filename
        }
        try:
            resp = TemplatesTestModelImpl.create(data,file_path)
        except Exception as e:
            return {"status": 500,"message": str(e)}
        return format_template(resp.to_dict()), 201
    
    @ns.doc('delete_test')
    def delete(self,id):
        """ 删除测试任务 """
        logger.info("删除测试任务")
        test_task = TemplatesTestModelImpl.get(id)
        if not test_task:
            return handle_error(404, f'test_task with id {id} not found')
        TemplatesTestModelImpl.delete(id)
        return format_template_delete(), 200
    
# 定义资源类
@ns.route('/downloads/<path:filename>')
class DownloadFile(Resource):
    def get(self, filename):
        try:
            download_file_path = CONFIG["export_file_path"]
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
                download_file_path = os.path.join(base_path, CONFIG["export_file_path"])
            return send_from_directory(download_file_path, filename, as_attachment=True)
        except FileNotFoundError:
            abort(404)  # 文件未找到时返回 404 错误@app.route('/downloads/<filename>')


# 定义资源类
@ns.route('/uploads/<path:filename>')
class UploadsloadFile(Resource):
    def get(self, filename):
        try:
            upload_file_path = CONFIG["import_file_path"]
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
                upload_file_path = os.path.join(base_path, CONFIG["import_file_path"])
            return send_from_directory(upload_file_path, filename, as_attachment=True)
        except FileNotFoundError:
            abort(404)  # 文件未找到时返回 404 错误@app.route('/downloads/<filename>')


@ns.route('/images/push')
class ImagesPushInfo(Resource):
    def post(self):
        try:
            """ 选择推送模板 """
            data = request.get_json()
            TemplatesModelImpl.images_push(data)
            return {
                'code': 0,
                'message': "success"   
            },200

        except Exception as e:
            return {"status": 500,"message": str(e)}