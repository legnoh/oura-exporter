# oura-exporter

[![Badge](https://img.shields.io/badge/docker-legnoh/oura--exporter-blue?logo=docker&link=https://hub.docker.com/r/legnoh/oura-exporter)](https://hub.docker.com/r/legnoh/oura-exporter) [![publish](https://github.com/legnoh/oura-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/legnoh/oura-exporter/actions/workflows/ci.yml)

Prometheus(OpenMetrics) exporter for [Oura Ring](https://ouraring.com).

## Usage

### Registration

Oura is deprecating Personal Access Tokens; use OAuth (Authorization Code with PKCE).

1. Create an app in the [Oura Cloud developer console](https://cloud.ouraring.com/docs/authentication) and note the Client ID (and Client Secret if provided).
2. Add a redirect URI that Oura accepts and includes a path, e.g. `http://localhost:8000/callback` (it can 404 locally; you just need the `code` in the URL). Make sure this exact URI is registered in the Oura app.
3. Set env vars:
   - `OURA_CLIENT_ID` (required)
   - `OURA_CLIENT_SECRET` (if your app issues one)
   - `OURA_REDIRECT_URI` (defaults to `http://localhost:8000/callback`)
   - `OURA_SCOPES` (optional space-delimited override; defaults to `email personal daily heartrate spo2 stress`)
   - `OURA_TOKEN_PATH` (optional token cache path; defaults to `~/.config/oura-exporter/oauth_token.json`)
   - `OURA_AUTH_CODE` (optional, set the one-time `code` from the OAuth redirect for non-interactive runs)
   - `OURA_AUTH_CODE_FILE` (optional, path to a file containing that `code`)
4. On first run the exporter prints an OAuth URL; open it, grant access, then paste the `code` query parameter from the redirected URL into the prompt (or set `OURA_AUTH_CODE` / `OURA_AUTH_CODE_FILE` in non-interactive setups). Tokens are refreshed automatically afterward.
5. Legacy `OURA_ACCESS_TOKEN` is still accepted but will stop working when Oura removes PAT support.

And check your local TZ identifier.

- [List of tz database time zones - Wikipedia](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

### Start(Docker)

The simplest way to use it is with Docker.

```
docker run -p 8000:8000 \
     -e OURA_CLIENT_ID="your_client_id" \
     -e OURA_CLIENT_SECRET="your_client_secret" \
     -e OURA_REDIRECT_URI="http://localhost:8000/callback" \
     -e OURA_AUTH_CODE="the_code_from_redirect" \
     -e TZ="Asia/Tokyo" \
    -it legnoh/oura-exporter
```

To expose ports when using `docker compose run`, add `--service-ports` (or prefer `docker compose up -d` after the initial auth run).
```

`OURA_AUTH_CODE` is optional; omit it if you can provide input interactively.

For headless Docker/Compose runs, set `OURA_AUTH_CODE` (or `OURA_AUTH_CODE_FILE`) once with the short-lived code from the redirect URL; tokens are then cached in the mounted volume so subsequent restarts do not need the code. If the container restarts between printing the URL and you supplying the code, reuse the code from that same URL—PKCE verifier is persisted in the volume to allow a second run to exchange it. Use `docker compose run --service-ports` (or `docker compose up -d` after auth) to expose the `/metrics` port on the host.
```

### Start(source)

Alternatively, it can be started from the source.

```sh
# clone
git clone https://github.com/legnoh/oura-exporter.git && cd oura-exporter
uv sync

# prepare .env file for your apps
cat << EOS > .env
OURA_CLIENT_ID="your_client_id"
OURA_CLIENT_SECRET="your_client_secret"
OURA_REDIRECT_URI="http://localhost:8000/callback"
# OURA_AUTH_CODE="the_code_from_redirect"  # optional non-interactive
TZ="Asia/Tokyo"
EOS

# run exporter
uv run main.py
```

## Metrics

please check [metrics.yml](./config/metrics.yml) or [example](./example/oura.prom)

## Disclaim

- This script is NOT authorized by Oura.
  - We are not responsible for any damages caused by using this script.
- This script is not intended to overload these sites or services.
  - When using this script, please keep your request frequency within a sensible range.
