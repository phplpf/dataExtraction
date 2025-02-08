#! /bin/bash

docker build -t template_v1.0 -f ./dockerfile .

docker-compose -f ./docker-compose.yml up -d --build
