#!/bin/bash

NAME='discord_bot_local'

echo 'Building Dockerfile...'
docker build -t $NAME .

echo 'Starting container...'
docker run --rm --name $NAME --env-file .env $NAME
