# Mum - Discord Bot

Installs Mum, a Discord bot that helps manage and organize voice channels.

See [Mum - Discord Bot](https://github.com/drewburr-labs/mum-discord-bot/blob/main/README.md) README for details about usage and setup requirements.

## Prerequisites

- Kubernetes 1.19+
- Helm 3+

## Get Helm Repository Info

```console
helm repo add mum-discord-bot https://drewburr-labs.github.io/mum-discord-bot
helm repo update
```

_See [`helm repo`](https://helm.sh/docs/helm/helm_repo/) for command documentation._

## Install Helm Chart

```console
helm install [RELEASE_NAME] mum-discord-bot/mum-discord-bot
```

_See [configuration](#configuration) below._

_See [helm install](https://helm.sh/docs/helm/helm_install/) for command documentation._

## Dependencies

There are no dependencies at this time.

## Uninstall Helm Chart

```console
helm uninstall [RELEASE_NAME]
```

This removes all the Kubernetes components associated with the chart and deletes the release.

_See [helm uninstall](https://helm.sh/docs/helm/helm_uninstall/) for command documentation._

## Upgrading Chart

```console
helm upgrade [RELEASE_NAME] mum-discord-bot/mum-discord-bot
```

_See [helm upgrade](https://helm.sh/docs/helm/helm_upgrade/) for command documentation._

## Configuration

See [Customizing the Chart Before Installing](https://helm.sh/docs/intro/using_helm/#customizing-the-chart-before-installing). To see all configurable options with detailed comments:

```console
helm show values mum-discord-bot/mum-discord-bot
```
