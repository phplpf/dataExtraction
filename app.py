from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_restx import Api
from controllers.templates import ns as tempaltes_ns,contrable_clear_test_tasks
from controllers.workflow import ns as workflows_ns
from controllers.modeservice import ns as modelservices_ns
from models.databases import init_db
from config.setting import CONFIG
from config.log_settings import LoggingCls


#配置日志
logger = LoggingCls.get_logger()

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

api = Api(app, version='1.0', title='API Documentation', description='A multi-business API with tempaltes, workflows, and modelservices')

# Register namespaces
api.add_namespace(tempaltes_ns)
api.add_namespace(workflows_ns)
api.add_namespace(modelservices_ns)

# 初始化数据库
init_db()
# 定时清除测试任务
contrable_clear_test_tasks()

if __name__ == '__main__':
    logger.info("启动服务")
    app.run(debug=CONFIG["debug"], host='0.0.0.0', port=CONFIG['port'])

    
