#! /bin/bash

pyinstaller \
    --hidden-import=requests \
    --hidden-import=openai \
    --hidden-import=docx \
    --hidden-import=cv2 \
    --hidden-import=fitz \
    --hidden-import=logging.config \
    --hidden-import=pdf2image \
    --hidden-import=PyPDF2 \
    --hidden-import=sqlalchemy \
    --hidden-import=sqlalchemy.ext.declarative \
    --hidden-import=sqlalchemy.orm.sessionmaker \
    --add-data "../../config/config.json:config/" \
    --add-data "../../config/setting.py:config/" \
    --add-data "../../config/log_settings.py:config/" \
    --add-data "../../config/nginx/data_extration.conf:config/" \
    --add-data "../../data/download/templates:templates" \
    --add-data "../../data/logs/dataextraction.log:logs" \
    --add-data "../../data/uploads/templates:uploads/templates" \
    --add-data "../../services/ocr.py:services/" \
    --add-data "../../services/llm.py:services/" \
    --add-data "../../utils:utils" \
    http_server.py

