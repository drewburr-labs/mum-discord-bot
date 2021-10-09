#!/bin/bash

NAME='discord_bot_local'

echo 'Cleaning up existing container(s)...'
docker rm $NAME

echo 'Sourcing local env...'
source .env

echo 'Building Dockerfile...'
docker build -t $NAME .

echo 'Starting container...'
docker run --rm --name $NAME -e DISCORD_TOKEN=$DISCORD_TOKEN $NAME
