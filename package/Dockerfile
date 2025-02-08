# 使用Ubuntu latest作为基础镜像
FROM ubuntu:22.04

# 安装必要的依赖
RUN apt-get update && \
    apt-get install -y \
    python3-pip \
    python3-dev \
    libffi-dev \
    build-essential \
    wget \
    curl \
    nginx \
    ca-certificates \
    gnupg \
    lsb-release \
    poppler-utils \
    qtbase5-dev \
    libqt5core5a \
    libqt5gui5 \ 
    libqt5widgets5 \ 
    && rm -rf /var/lib/apt/lists/*


# 复制本地下载的 Docker GPG 密钥
COPY ./config/keys/docker.gpg /etc/apt/keyrings/docker.gpg

# 设置 Docker 仓库
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 复制并安装 Docker CLI 的 deb 包
COPY ./config/docker/docker-ce-cli.deb /tmp/docker-ce-cli.deb
RUN dpkg -i /tmp/docker-ce-cli.deb && rm /tmp/docker-ce-cli.deb

# 安装PyInstaller和其他必要的Python库
RUN pip3 install pyinstaller

# 设置工作目录
WORKDIR /app


# 安装 Python 依赖
# RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install Flask==3.0.3\
    flask-restx==1.3.0\
    sqlalchemy==2.0.34\
    sqlmodel==0.0.18\
    psycopg==3.1.9\
    psycopg2-binary==2.9.9\
    postgrest==0.16.11\
    PyPDF2==3.0.1\
    pypdf==4.3.1\
    pypandoc==1.14\
    pypdfium2==4.30.0\
    openai==1.45.0\
    openpyxl==3.1.4\
    numpy==1.24.4\
    pandas==1.5.3\
    docx2txt==0.8\
    python-docx==1.1.2\
    Werkzeug==3.0.4\
    pdf2image==1.17.0\
    PyMuPDF==1.23.26\
    fitz==0.0.1.dev2

# 复制应用代码和配置文件
COPY ../dist/app /app/
# COPY ../dist/app/_internal /app/

# 确保可执行文件具有执行权限
RUN chmod +x /app/app

# 设置容器启动时的执行入口
ENTRYPOINT ["/app/app"]

