from flask_restx import marshal_with, fields
import json


# 自定义响应结构
def create_response(code, message, data):
    return {
        'code': code,
        'message': message,
        'data': data
    }


def format_template_delete():
    """ 格式化返回的 template 删除请求的响应 """
    return {
        'code': 0,
        'message': "success"   
    }

def format_templates(templates):
    """ 格式化返回的 template 列表 """
    results = create_response(0, "success",templates)
    return results

def format_template(template):
    """ 格式化返回的单个 template """
    # print('template:',template)
    results = create_response(0, "success",template)
    return results

def handle_error(error_code, error_message):
    """ 统一错误处理，返回指定格式的错误 """
    return {'error': error_message}, error_code
