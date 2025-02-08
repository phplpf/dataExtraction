import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler
import os
from config.setting import CONFIG
import sys

LOG_DIR = None
LOG_FILE = None

def init_log():
    global LOG_DIR
    global LOG_FILE
    log_path = CONFIG["log"]["path"]
    if getattr(sys, 'frozen', False):
        # 如果是打包后的应用程序
        base_path = sys._MEIPASS
        log_path = os.path.join(base_path, CONFIG["log"]["path"])
    LOG_DIR = os.path.join(os.path.dirname(__file__), log_path)
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    LOG_FILE = os.path.join(LOG_DIR, 'dataextraction.log')

def get_handler():
    handler = TimedRotatingFileHandler(LOG_FILE, when='midnight', backupCount=7)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    return handler

def get_logging_config():
    if CONFIG["log"]["enable"]:
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                },
            },
            'handlers': {
                'console': {
                    'level': CONFIG["log"]["level"],
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                },
                # 在配置字典中移除 'file' 处理程序
            },
            'loggers': {
                '': {  # root logger
                    'handlers': ['console'],
                    'level': CONFIG["log"]["level"],
                    'propagate': True,
                },
                'app': {  # app logger
                    'handlers': ['console'],
                    'level': CONFIG["log"]["level"],
                    'propagate': False,
                },
                'watchdog': {  # watchdog logger
                    'handlers': ['console'],
                    'level': 'WARNING',  # 设置为 WARNING 级别
                    'propagate': False,
                },
                'sqlalchemy.engine': {  # Suppress SQLAlchemy engine logs at INFO level
                    'handlers': ['console'],
                    'level': 'WARNING',  # Only show WARNING or higher level
                    'propagate': False,
                },
            }
        }
    else:
        # 如果禁用日志记录，返回一个最小化的日志配置
        return {
            'version': 1,
            'disable_existing_loggers': True,
        }
    
class LoggingCls(object):
    logger = None

    def __init__(self):
        pass

    @classmethod
    def get_logger(cls):
        if cls.logger:
            return cls.logger
        init_log()
        logging_config = get_logging_config()
        logging.config.dictConfig(logging_config)
        cls.logger = logging.getLogger('app')
        handler = get_handler() 
        cls.logger.addHandler(handler)
        return cls.logger

if __name__ == '__main__':
    # 示例：获取 logger 实例并记录信息
    logger = LoggingCls.get_logger()
    logger.info("Logger initialized successfully")
