FROM python:3-slim-bullseye
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV WORKDIR=/usr/src/app
WORKDIR ${WORKDIR}

COPY . ${WORKDIR}
RUN uv sync --frozen

EXPOSE 8000

CMD ["uv", "run", "main.py"]
