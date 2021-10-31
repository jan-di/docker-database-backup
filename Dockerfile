FROM python:3.10.0-alpine3.14 AS base

LABEL jan-di.database-backup.instance_id="default"

RUN set -eux; \
    apk --no-cache add \
    mariadb-client \
    postgresql-client \
    tzdata

FROM base AS python-deps

RUN set -eux; \
    apk --no-cache add \
    # cryptography
    gcc musl-dev python3-dev libffi-dev openssl-dev cargo \
    ; \
    pip install pipenv

COPY Pipfile .
COPY Pipfile.lock .
ENV CI=1 \
    PIPENV_VENV_IN_PROJECT=1
RUN set -eux; \
    pipenv install --deploy

FROM base

COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

WORKDIR /app

RUN set -eux; \
    mkdir -p /dump

ENV PYTHONUNBUFFERED=1

COPY . .

ENTRYPOINT [ "python3", "/app/main.py" ]