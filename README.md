# oura-exporter

[![Badge](https://img.shields.io/badge/docker-legnoh/oura--exporter-blue?logo=docker&link=https://hub.docker.com/r/legnoh/oura-exporter)](https://hub.docker.com/r/legnoh/oura-exporter) [![ci](https://github.com/legnoh/oura-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/legnoh/oura-exporter/actions/workflows/ci.yml)

Prometheus(OpenMetrics) exporter for [Oura Ring](https://ouraring.com).

## Usage

### Registration

At first, create Oura Personal Access Tokens(PATs) for yours.

- [Personal Access Tokens - Authentication | Oura Developer](https://cloud.ouraring.com/docs/authentication#personal-access-tokens)

And check your local TZ identifier.

- [List of tz database time zones - Wikipedia](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

### Start(Docker)

The simplest way to use it is with Docker.

```
docker run -p 8000:8000 \
     -e OURA_ACCESS_TOKEN="youraccesstokenhere" \
     -e TZ="Asia/Tokyo" \
    legnoh/oura-exporter
```

### Start(source)

Alternatively, it can be started from the source.

```sh
# clone
git clone https://github.com/legnoh/oura-exporter.git && cd oura-exporter
pipenv install

# prepare .env file for your apps
cat << EOS > .env
OURA_ACCESS_TOKEN="youraccesstokenhere"
TZ="Asia/Tokyo"
EOS

# run exporter
pipenv run main
```

## Metrics

please check [metrics.yml](./config/metrics.yml) or [example](./example/oura.prom)

## Disclaim

- This script is NOT authorized by Oura.
  - We are not responsible for any damages caused by using this script.
- This script is not intended to overload these sites or services.
  - When using this script, please keep your request frequency within a sensible range.
