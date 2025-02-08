#! /bin/bash

docker load -i ./docker_images/ubuntu-22.04.tar

docker load -i ./docker_images/postgres_11.tar

docker load -i ./docker_images/nginx_stable-perl.tar

docker image ls

# 检查并创建挂载目录
if [ ! -d "/app/_internal/data/uploads/templates" ]; then
    mkdir -p /app/_internal/data/uploads/templates
fi

echo "构建Docker镜像..."
docker-compose -f ./docker-compose.yml  build --no-cache
docker-compose -f ./docker-compose.yml up --force-recreate -d




docker run --rm  -v /app/_internal/data/uploads/templates:/app/data headless-wps-test --format pdf /app/data/智能审核6.docx

docker run --rm  -v /home/senscape:/app/data headless-wps:v1.0 --format pdf /app/data/智能审核6.docx

docker run --rm  -v /root/docker_test:/app/data headless-wps-test --format pdf /app/data/测试合同_8.docx