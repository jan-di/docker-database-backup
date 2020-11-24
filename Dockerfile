FROM python:3.9-alpine

RUN set -eux; \
    apk --no-cache add \
        mariadb-client

RUN set -eux; \
    pip install pipenv

WORKDIR /app
COPY Pipfile .
COPY Pipfile.lock .

RUN set -eux; \
    pipenv install --system

COPY . .

RUN set -eux; \
    mkdir -p /dump

ENV PYTHONUNBUFFERED=1

ENTRYPOINT [ "python3", "/app/main.py" ]