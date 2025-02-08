#!/bin/bash

export DOCKER_CLI_EXPERIMENTAL=enabled
export DOCKER_CONTENT_TRUST=1

docker rmi ubuntu-22.04

docker stop postgres_db
docker rm -f postgres_db

docker stop nginx
docker rm -f nginx

docker stop data_extraction_app
docker rm -f data_extraction_app

docker build -t ubuntu-22.04 -f package/Dockerfile .

# 使用docker-compose构建镜像
echo "构建Docker镜像..."
docker-compose -f package/docker-compose.yml  build --no-cache
docker-compose -f package/docker-compose.yml up --force-recreate -d

# # 启动Docker容器
# echo "启动Docker容器..."
# docker-compose up -d
