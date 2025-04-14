#!/bin/bash

IMG="registry.gitlab.com/roxautomation/components/odrive-can"

mkdir -p /var/tmp/container-extensions

docker pull $IMG

# build image
#docker build -t $IMG -f ./docker/Dockerfile ./docker
