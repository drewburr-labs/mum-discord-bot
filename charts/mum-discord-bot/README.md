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

## prometheus.io/scrape

The prometheus operator does not support annotation-based discovery of services, using the `PodMonitor` or `ServiceMonitor` CRD in its place as they provide far more configuration options.
For information on how to use PodMonitors/ServiceMonitors, please see the documentation on the `prometheus-operator/prometheus-operator` documentation here:

- [ServiceMonitors](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md#include-servicemonitors)
- [PodMonitors](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/getting-started.md#include-podmonitors)
- [Running Exporters](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/user-guides/running-exporters.md)

By default, Prometheus discovers PodMonitors and ServiceMonitors within its namespace, that are labeled with the same release tag as the prometheus-operator release.
Sometimes, you may need to discover custom PodMonitors/ServiceMonitors, for example used to scrape data from third-party applications.
An easy way of doing this, without compromising the default PodMonitors/ServiceMonitors discovery, is allowing Prometheus to discover all PodMonitors/ServiceMonitors within its namespace, without applying label filtering.
To do so, you can set `prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues` and `prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues` to `false`.
