# Mum - Discord Bot

[![Docker Build/Publish](https://github.com/drewburr-labs/mum-discord-bot/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/drewburr-labs/mum-discord-bot/actions/workflows/docker-publish.yml) [![Chart Publish](https://github.com/drewburr-labs/mum-discord-bot/actions/workflows/helm-publish.yml/badge.svg)](https://github.com/drewburr-labs/mum-discord-bot/actions/workflows/helm-publish.yml)
[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/mum-discord-bot)](https://artifacthub.io/packages/search?repo=mum-discord-bot) [![pages-build-deployment](https://github.com/drewburr-labs/mum-discord-bot/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/drewburr-labs/mum-discord-bot/actions/workflows/pages/pages-build-deployment)

Mum is a Discord bot designed to handle managing voice channels using semi-private lobbies that are created when needed and deleted when they are not.

## Server Setup

Before inviting Mum to your server, be sure to create a voice channel named `Create New Lobby`.

Once the above has been created, [give Mum a call](https://discord.com/api/oauth2/authorize?client_id=754124084769587213&permissions=2164337744&redirect_uri=https%3A%2F%2Fdiscord.com%2Foauth2%2Fauthorize&scope=bot%20applications.commands)!

### The Lobby System

Mum manages voice channels by creating what is referred to as a 'Lobby'. A Lobby is automatically created every time someone joins the `Create New Lobby` voice channel. This new Lobby will be named after the user who created it, for example, `drewburr's Lobby`. Once created, the user will be automatically transferred into thier Libby's voice channel.

In Discord terms, a Lobby is a category that contains both a voice channel and a text channel. Each channel is aptly named `voice chat` and `text-chat`, respectively.

<img src="https://raw.githubusercontent.com/drewburr-labs/mum-discord-bot/main/docs/lobby-example.png" alt="drawing" width="280"/>

A Lobby is intended to be a semi-private, dedicated space for an activity. To support this, the `text-chat` is created as a private channel, so it wil be invisible. Once a user joins the Lobby's `voice chat`, they will receive permissions to view the channel.

To help support administration, several steps are taken to ensure control over Lobby settings. The category and voice channel permissions are based on the permissions surrounding the `Create New Lobby` voice channel. For `text chat`, only the `view channel` permission is managed by the bot. All other text channel permissions will follow the category and server permissions.

### Limitations

A Lobby is considered a 'Lobby' when the category name ends with, well, Lobby. This is not case-sensitive, so names like `my lobby` and `another LoBbY` are both valid Lobby names. Due to this, it is critical that lobbies are not manually renamed, **and no existing category names end in 'lobby', otherwise Mum will delete it!**

## Self-hosting

Mum can be self-hosted using the packages provided by this repository

- [mum-discord-bot](https://github.com/drewburr-labs/mum-discord-bot/pkgs/container/mum-discord-bot) is a Dockerized version of this repository.
- [mum-discord-bot/mum-discord-bot](https://github.com/drewburr-labs/mum-discord-bot/pkgs/container/mum-discord-bot%2Fmum-discord-bot) is a Helm chart for deploying the Docker container to Kubernetes.

### Environment variables

The bot application expects the below environment variables to be set.

| Name                  | Description                                          |
| --------------------- | ---------------------------------------------------- |
| DISCORD_TOKEN         | Discord application token for bot authentication     |
| CONTROLLER_GUILD_ID   | Guild ID for admin control and logging               |
| CONTROLLER_CHANNEL_ID | Channel ID in the controller guild for admin logging |

## Testing Changes

Local testing requires Docker to be installed.

To support consistent testing and local development, [test.sh](./test.sh) has been provided.

Before executing, first create `.env` in the root of the repository. This should include the following data:

```text
DISCORD_TOKEN="your-token-here"
CONTROLLER_GUILD_ID="guild-id"
CONTROLLER_CHANNEL_ID="log-channel-id"
```

To execute, run the following command. This will build and run the bot using your local files.

```shell
./test.sh
```

To exit, use `CTRL+C`. After exiting, the container will automatically be deleted.
