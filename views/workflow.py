from flask_restx import marshal_with, fields

# 定义 API 模型
# 自定义响应结构
def create_response(code, message, data):
    return {
        'code': code,
        'message': message,
        'data': data
    }


def format_workflows(workflows):
    """ 格式化返回的 workflows 列表 """
    results = create_response(0, "success",workflows)
    return results


def format_workflow(workflow):
    """ 格式化返回的单个 workflow """
    results = create_response(0, "success",workflow)
    return results

def handle_error(error_code, error_message):
    """ 统一错误处理，返回指定格式的错误 """
    return {'error': error_message}, error_code

def format_workflow_delete():
    """ 格式化返回的单个 workflow """
    return {"code": 0, "message": "success"}