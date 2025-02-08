import datetime
from sqlalchemy import Column, Integer, String,Boolean,func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine, exc, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from config.setting import CONFIG
import json
import os
import ast

class DAO:
    def __init__(self):
        # 定义连接到默认数据库的引擎
        self.default_engine = create_engine(f'postgresql+psycopg2://{CONFIG["db"]["user"]}:{CONFIG["db"]["password"]}@{CONFIG["db"]["host"]}:{CONFIG["db"]["port"]}/postgres')
        # 检查并创建数据库
        self.create_database(self.default_engine, CONFIG["db"]["database"])
        # 基础类
        self.Base = declarative_base()
        # 连接到新创建的数据库
        self.engine = create_engine(
            'postgresql+psycopg2://senscape:senscape@%s:%s/%s'%(CONFIG["db"]["host"],CONFIG["db"]["port"],CONFIG["db"]["database"]),
            max_overflow=0,
            pool_size=50,
            pool_timeout=10,
            pool_recycle=1,
            echo=False
        )

    # 检查数据库是否存在
    def database_exists(self, engine, database_name):
        with engine.connect() as connection:
            query = text(f"SELECT 1 FROM pg_database WHERE datname='{database_name}'")
            result = connection.execute(query)
            return result.scalar() is not None

    # 创建数据库
    def create_database(self, engine, database_name):
        if not self.database_exists(engine, database_name):
            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
                connection.execute(text(f"CREATE DATABASE {database_name}"))
                print(f"Database '{database_name}' created successfully.")
        else:
            print(f"Database '{database_name}' already exists.")

    def get_engine(self):
        return self.engine

dao = DAO()
Base = dao.Base
engine = dao.get_engine()
Session = sessionmaker(bind=engine)
session = scoped_session(Session)

# 大模型模板配置表
class TemplatesModel(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(32), index=True, nullable=False, comment="任务")
    description = Column(String(64), nullable=True, comment="任务描述")
    workflow_id = Column(Integer, default=0, comment="工作流id")
    entities_info = Column(JSONB, nullable=False, comment="实体信息")
    rule_info = Column(JSONB, nullable=False, comment="规则信息")
    enable = Column(Boolean(), default=False, comment="是否启用")
    create_time = Column(Integer, default=func.extract('epoch', func.now()), comment="创建时间")
    last_update_time = Column(Integer, default=func.extract('epoch', func.now()),comment="最后更新时间")
    user = Column(String(32), nullable=True, comment="用户")
    delete_status = Column(Boolean(), default=False, comment="是否删除")

    def __repr__(self):
        # 返回字符串表示，便于调试
        return f"<TemplatesModel(id={self.id}, name={self.name}, description={self.description}, " \
               f"workflow_id={self.workflow_id}, entities_info={self.entities_info}, " \
               f"rule_info={self.rule_info}, enable={self.enable}, " \
               f"create_time={self.create_time}, last_update_time={self.last_update_time}, " \
               f"user={self.user}, delete_status={self.delete_status})>"
    
    def to_dict(self):
        # 返回字典表示，用于序列化或接口返回
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'workflow_id': self.workflow_id,
            'entities_info': self.entities_info,
            'rule_info': self.rule_info,
            'enable': self.enable,
            'last_update_time': self.last_update_time,
            'delete_status': self.delete_status,
            'create_time': self.create_time,
            'user': self.user
        }


#模板测试任务
class TemplatesTestModel(Base):
    __tablename__ = "templates_test"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    template_id = Column(Integer, nullable=False, comment="模板id")
    name = Column(String(64), nullable=False, comment="测试名称")
    description = Column(String(64), nullable=True, comment="测试描述")
    test_file = Column(String(64), nullable=False, comment="测试文件")
    test_type = Column(Integer, nullable=True,default=0, comment="测试类型")
    test_type_name = Column(String(64), nullable=True, comment="测试类型名称")  
    status = Column(Integer, default=0, comment="状态")
    results = Column(JSONB, nullable=True, comment="测试结果")
    create_time = Column(Integer, default=func.extract('epoch', func.now()), comment="创建时间")
    last_update_time = Column(Integer, default=func.extract('epoch', func.now()),comment="最后更新时间")
    user = Column(String(32), nullable=True, comment="用户")
    delete_status = Column(Boolean(), default=False, comment="是否删除")

    def __repr__(self):
        # 返回字符串表示，便于调试
        return f"<TemplatesTestModel(id={self.id}, template_id={self.template_id}, name={self.name}, " \
               f"description={self.description}, test_file={self.test_file}, test_type={self.test_type}, " \
               f"status={self.status}, create_time={self.create_time}, last_update_time={self.last_update_time}, " \
               f"user={self.user}, delete_status={self.delete_status})>"
    
    def to_dict(self):
        # 返回字典表示，用于序列化或接口返回
        results = self.results
        if results:
            results = json.loads(results)
        else:
            results = []
        return {
            'id': self.id,
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'test_file': self.test_file,
            'test_type': self.test_type,
            'status': self.status,
            'results': results,
            'last_update_time': self.last_update_time,
            'delete_status': self.delete_status,
            'create_time': self.create_time,
            'user': self.user
        }
    
class ModelServiceModel(Base):
    __tablename__ = "modelservice"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(64), index=True, nullable=False, comment="任务名")
    description = Column(String(255), nullable=False, comment="任务描述")
    img_path = Column(String(255), nullable=True, comment="图片路径")
    is_default = Column(Integer, default=0, comment="是否为dafault")
    service_type = Column(Integer, nullable=False,default=1, comment="服务类型,1:OCR,2:LLM")
    model_type_id = Column(Integer, nullable=True, comment="模型类型id")
    api_info = Column(JSONB, nullable=False, comment="api信息")
    enable = Column(Boolean(), default=False, comment="是否启用")
    create_time = Column(Integer, default=func.extract('epoch', func.now()), comment="创建时间")
    last_update_time = Column(Integer, default=func.extract('epoch', func.now()),comment="最后更新时间")
    user = Column(String(32), nullable=True, comment="用户")
    delete_status = Column(Boolean(), default=False, comment="是否删除")

    def __repr__(self):
        # 返回字符串表示，便于调试
        return f"<ModelServiceModel(id={self.id}, name={self.name}, description={self.description}, " \
               f"img_path={self.img_path}, service_type={self.service_type},model_type_id={self.model_type_id}, api_info={self.api_info}, " \
               f"enable={self.enable}, create_time={self.create_time}, last_update_time={self.last_update_time}, " \
               f"user={self.user}, delete_status={self.delete_status})>"
    
    def to_dict(self):
        # 返回字典表示，用于序列化或接口返回
        orc_icon = None
        if self.img_path or self.img_path != '':
            img_name = os.path.basename(self.img_path)
            if "pre_ocr_card" in self.img_path:
                orc_icon = os.path.join("/api/v1/modelservices/downloads/pre_ocr_card/",img_name)
            elif "llm_card" in self.img_path:
                orc_icon = os.path.join("/api/v1/modelservices/downloads/llm_card/",img_name)
            else:
                orc_icon = os.path.join("/api/v1/modelservices/downloads/",img_name)
            
        api_info = self.api_info
        if isinstance(api_info, str):
            try:
                clean_data = api_info.replace('\n', '\\n').replace('\r','\\r').replace('\t','\\t')  # 转义换行符
                api_info = json.loads(clean_data)
            except:
                api_info = ast.literal_eval(api_info)

        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'img_path': orc_icon,
            'service_type': self.service_type,
            'model_type_id': self.model_type_id,
            'is_default': self.is_default,
            'api_info': api_info,
            'enable': self.enable,
            'last_update_time': self.last_update_time,
            'delete_status': self.delete_status,
            'create_time': self.create_time,
            'user': self.user
        }
    
class ModelServiceTypeModel(Base):
    __tablename__ = "model_type_table"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(32), index=True, nullable=False, comment="任务名")
    description = Column(String(255), nullable=True, comment="任务描述")
    is_default = Column(Integer, default=0, comment="是否为dafault")
    enable = Column(Boolean(), default=True, comment="是否启用")
    type = Column(Integer, default=1, comment="服务类型,1:OCR,2:LLM")
    format_info = Column(JSONB, nullable=True, comment="格式信息")
    create_time = Column(Integer, default=func.extract('epoch', func.now()), comment="创建时间")
    last_update_time = Column(Integer, default=func.extract('epoch', func.now()),comment="最后更新时间")
    user = Column(String(32), nullable=True, comment="用户")
    delete_status = Column(Boolean(), default=False, comment="是否删除")

    def __repr__(self):
        # 返回字符串表示，便于调试
        return f"<ModelServiceTypeModel(id={self.id}, name={self.name}, description={self.description}, " \
               f"create_time={self.create_time}, last_update_time={self.last_update_time}, " \
               f"user={self.user}, delete_status={self.delete_status})>"
    
    def to_dict(self):
        # 返回字典表示，用于序列化或接口返回
        return {
            'id': self.id,
            'name': self.name,
            'is_default': self.is_default,
            'create_time': self.create_time,
            'user': self.user
        }

    
class WorkflowModel(Base):
    __tablename__ = "workflow_table"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    name = Column(String(32), index=True, nullable=False, comment="任务名")
    description = Column(String(64), nullable=False, comment="任务描述")
    setup_process = Column(JSONB, nullable=False, comment="设置流程")
    enable = Column(Boolean(), default=False, comment="是否启用")
    is_default = Column(Integer,default=0,comment="是否为dafault")
    create_time = Column(Integer, default=func.extract('epoch', func.now()), comment="创建时间")
    last_update_time = Column(Integer, default=func.extract('epoch', func.now()),comment="最后更新时间")
    user = Column(String(32), nullable=True, comment="用户")
    delete_status = Column(Boolean(), default=False, comment="是否删除")

    def __repr__(self):
        # 返回字符串表示，便于调试
        return f"<WorkflowModel(id={self.id}, name={self.name}, description={self.description}, " \
               f"setup_process={self.setup_process}, enable={self.enable}, " \
               f"create_time={self.create_time}, last_update_time={self.last_update_time}, " \
               f"user={self.user}, delete_status={self.delete_status})>"
    

    def to_dict(self):
        # 返回字典表示，用于序列化或接口返回
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'setup_process': self.setup_process,
            'enable': self.enable,
            'is_default':self.is_default,
            'last_update_time': self.last_update_time,
            'delete_status': self.delete_status,
            'create_time': self.create_time,
            'user': self.user
        }


def init_db():
    global engine
    global Base
    dao.create_database(engine, CONFIG["db"]["database"])
    Base.metadata.create_all(bind=engine)
