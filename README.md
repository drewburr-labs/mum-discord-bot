# centralstation-bot

A bot meant to handle managing roles and voice channels for the Central Station Discord server

Each namespace requires [a secret to be created](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/) for pulling the Docker image.

```shell
docker login
kubectl create secret generic regcred --from-file=.dockerconfigjson=$HOME/.docker/config.json --type=kubernetes.io/dockerconfigjson
```
