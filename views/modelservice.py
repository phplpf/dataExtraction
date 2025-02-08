from flask_restx import marshal_with, fields


# 自定义响应结构
def create_response(code, message, data):
    return {
        'code': code,
        'message': message,
        'data': data
    }

def format_modelservices(modelservices):
    """ 格式化返回的 modelservice 列表 """
    return create_response(0, "success",modelservices) 


def format_modelservice(modelservice):
    """ 格式化返回的单个 modelservice """
    return create_response(0, "success",modelservice) 

def handle_error(error_code, error_message):
    """ 统一错误处理，返回指定格式的错误 """
    return {'error': error_message}, error_code

def format_modelservice_delete():
    """ 格式化返回的 template 删除请求的响应 """
    return {
        'code': 0,
        'message': "success"   
    }
