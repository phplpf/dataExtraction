from flask import request,send_from_directory,abort
from flask_restx import Resource, Namespace, fields, abort
from services.workflow import WorkflowModelImpl
from views.workflow import  format_workflows, format_workflow, handle_error,format_workflow_delete
from config.log_settings import LoggingCls
from config.setting import CONFIG
import json
import sys
import os

logger = LoggingCls.get_logger()

ns = Namespace('api/v1/workflows/llm', description='Workflows operations')

@ns.route('/')
class WorkflowsList(Resource):
    @ns.doc('list_workflows')
    @ns.param('page', '当前页数',required=False, type='int',default=1)
    @ns.param('count', '展示条数',required=False, type='int',default=20)
    @ns.param('stime', '开始时间',required=False, type='int')
    @ns.param('etime', '结束时间',required=False, type='int')
    @ns.param('name',  '工作流名称',required=False, type='string')
    @ns.param('user',  '用户',required=False, type='string')
    def get(self):
        try:
            logger.info("工作流列表页")
            """ 工作流列表页 """
            params = request.args
            workflows = WorkflowModelImpl.get_all(params)
            if not workflows:
                return handle_error(404, "No workflows found")  # 如果没有任务，返回错误
            return format_workflows(workflows)  # 使用视图层格式化数据
        except Exception as e:
            return {'message': str(e)}, 500

    def post(self):
        try:
            logger.info("新建工作流")
            """ 新建工作流/导入工作流 """
            if 'file' in request.files:
                uploaded_file = request.files['file']  # 获取上传的文件
                if uploaded_file and uploaded_file.filename.endswith('.json'):
                    file_content = uploaded_file.read()
                    try:
                        json_data = json.loads(file_content)
                    except json.JSONDecodeError:
                        return {'message': 'Invalid JSON file content'}, 400
                    
                    # 使用从文件中解析的内容创建工作流
                    workflow = WorkflowModelImpl.create(json_data)
                    return format_workflow(workflow.to_dict()), 201  # 返回新创建的模板
                else:
                    return {'message': 'Please upload a valid JSON file'}, 415
            else:
                data = request.get_json()
                if not data:
                    return {'message': 'No template data provided'}, 400
                workflow = WorkflowModelImpl.create(data)
            return format_workflow(workflow.to_dict()), 201  # 使用视图层格式化并返回新创建的任务
        except Exception as e:
            return {'message': str(e)}, 500

@ns.route('/<int:id>')
@ns.param('id', 'The Workflows identifier')
class WorkflowsResource(Resource):

    def get(self, id):
        try:
            logger.info("工作流详情页")
            """ 工作流详情页 """
            workflows = WorkflowModelImpl.get(id)
            if not workflows:
                return handle_error(404, f'workflows with id {id} not found')
            return format_workflow(workflows.to_dict())  # 使用视图层格式化返回
        except Exception as e:
            return {'message': str(e)}, 500

    def delete(self, id):
        try:
            logger.info("删除工作流")
            """ 删除工作流 """
            workflow = WorkflowModelImpl.delete(id)
            if not workflow:
                return handle_error(404, f'workflow with id {id} not found')
            return format_workflow_delete(), 200
        except Exception as e:
            return {'message': str(e)}, 500

    def put(self, id):
        try:
            logger.info("更新工作流")
            """更新工作流 """
            data = request.get_json()
            workflow = WorkflowModelImpl.update(id, data)
            if not workflow:
                return handle_error(404, f'workflow with id {id} not found')
            return format_workflow(workflow.to_dict())  # 使用视图层格式化更新后的任务
        except Exception as e:
            return {'message': str(e)}, 500
        
@ns.route('/<int:id>/export')
class WorkflowsExportResource(Resource):
    def get(self, id):
        try:
            logger.info("导出工作流")
            """ 导出工作流 """
            workflow = WorkflowModelImpl.get(id)
            if not workflow:
                return handle_error(404, f'workflow with id {id} not found')
            data = WorkflowModelImpl.export_workflow(workflow.to_dict())
            return format_workflow(data)  # 使用视图层格式化更新后的任务
        except Exception as e:
            return {'message': str(e)}, 500
        
        
@ns.route('/downloads/<path:filename>')
class DownloadFile(Resource):
    def get(self, filename):
        try:
            logger.info("下载工作流")
            """ 下载工作流 """
            download_file_path = CONFIG["export_file_path"] 
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序
                base_path = sys._MEIPASS
                download_file_path = os.path.join(base_path, CONFIG["export_file_path"])
            return send_from_directory(download_file_path, filename, as_attachment=True)
        except FileNotFoundError:
            abort(404)  # 文件未找到时返回 404 错误@app.route('/downloads/<filename>')
    
        
@ns.route('/<int:id>/clone')
class CloneWorkflow(Resource):
    def get(self,id):
        try:
            logger.info("创建副本")
            """ 创建副本  """
            params = request.args
            workflow_clone = WorkflowModelImpl.clone(id,params)
            if not workflow_clone:
                return handle_error(404, f'创建副本失败,你要创建副本的原文件不存在或存在异常')
            return format_workflow(workflow_clone.to_dict())  # 使用视图层格式化返回
        except Exception as e:
            return {'message': str(e)}, 500


        