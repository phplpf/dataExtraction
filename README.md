## 框架描述

该框架采用MVC结构，分为模型层、视图层和控制器层。每一层各司其职，确保代码结构清晰、可维护性高。以下是框架目录和文件的详细说明：

| 目录/文件      | 描述                                              |
| --------------- | ------------------------------------------------- |
| **controllers** | 控制器层，主要用于任务调度                        |
| **models**      | 模型层，主要用于处理业务逻辑，以及与数据库之间的交互 |
| **views**       | 视图层，主要处理接口的输出格式、错误处理等        |
| **config**      | 存放配置文件的目录                                |
| **data**        | 临时存放导出文件的目录，该目录需配置nginx以支持下载 |
| **databases.py**| 处理数据库的连接等操作                            |
| **llm.py**      | 处理加载和调用大模型相关的逻辑                    |
| **app.py**      | 服务入口文件                                      |

### 目录结构

```plaintext
.
├── app.py
├── config
├── controllers
├── data
├── databases.py
├── llm.py
├── models
└── views

```


运行指令

```bash
python3 app.py

```

## 数据迁移操作指令

***步骤一***

1. 初始化migrations表迁移目录
2. 生成表更新的迁移脚本，历史记录等

```bash
#这一步只在未初始化migrations表迁移目录下时执行
alembic init migrations 
#新增表 workflow_table modelservice
alembic revision --autogenerate -m "Add workflow_table and modelservice"

```

***步骤二***

更新migrations目录下env.py

```python
#这一步是必须的。
from databases import Base
#这两步是你更新的表结构对应的模块
from models.workflow import WorkflowModel
from models.modelservice import ModelServiceModel
#这一步是文件中原有的。如果没有就加上
target_metadata = Base.metadata

```

***步骤三***

执行迁移：

```bash

alembic upgrade head 

```


```
dataExtraction
├─ README.md
├─ alembic.ini
├─ app.py
├─ config
│  ├─ data_extration.conf
│  ├─ log_settings.py
│  └─ setting.py
├─ controllers
│  ├─ modeservice.py
│  ├─ templates.py
│  └─ workflow.py
├─ migrations
│  ├─ README
│  ├─ env.py
│  ├─ script.py.mako
│  └─ versions
│     └─ f88287f8039f_add_workflow_table_and_modelservice.py
├─ models
│  └─ databases.py
├─ package
│  ├─ Dockerfile
│  ├─ build.sh
│  └─ docker-compose.yml
├─ requirements.txt
├─ services
│  ├─ __init__.py
│  ├─ llm.py
│  ├─ modelservice.py
│  ├─ ocr.py
│  ├─ templates.py
│  └─ workflow.py
├─ utils
│  ├─ __init__.py
│  ├─ pdf_find_text.py
│  ├─ utils.py
│  └─ word_to_images.py
└─ views
   ├─ modelservice.py
   ├─ templates.py
   └─ workflow.py

```

### 打包步骤

```sh

rm -rf build dist

pyinstaller --add-data "config/config.json:config/" --add-data "config/nginx/data_extration.conf:config/" --add-data "data/download/templates:templates" --add-data "data/logs/dataextraction.log:logs" --add-data "data/uploads/templates:uploads/templates" app.py

./package/build.sh  

docker logs -f data_extraction_app 

docker exec -it data_extraction_app /bin/bash

```