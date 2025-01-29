#!/bin/bash -e

containers=$(docker ps -aq)
images=$(docker images -q)
volumes=$(docker volume ls | grep -v DRIVER)

if [ "$containers" != "" ]
then
    docker stop $containers
    docker rm -v $containers
fi

if [ "$images" != "" ]
then
    docker rmi -f $images
fi

if [ "$volumes" != "" ]
then
    docker volume rm -f $volumes
fi
