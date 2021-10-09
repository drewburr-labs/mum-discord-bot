# centralstation-bot

A bot meant to handle managing roles and voice channels for the Central Station Discord server

Each namespace requires [a secret to be created](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/) for pulling the Docker image.

```shell
docker login
kubectl create secret generic regcred --from-file=.dockerconfigjson=$HOME/.docker/config.json --type=kubernetes.io/dockerconfigjson
```

## Testing changes

Local testing requires Docker to be installed.

To support consistent testing and local development, [test.sh](./test.sh) has been provided.

Before executing, first create `.env` in the root of the repository. This should include the following data:

```text
DISCORD_TOKEN="your-token-here"
```

To execute, run the following command. This will build and run the bot using your local files.

```shell
./test.sh
```

To exit, use `CTRL+C`. After exiting, the container will automatically be deleted.
