FROM python:3.10.0-bullseye AS base

LABEL jan-di.database-backup.instance_id="default"

RUN apt-get update && apt-get install -y \
    mariadb-client \
    postgresql-client \ 
    tzdata \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

FROM base AS python-deps

RUN set -eux; \
    pip install pipenv

COPY Pipfile Pipfile.lock  ./

RUN set -eux; \
    CI=1 PIPENV_VENV_IN_PROJECT=1 PIP_ONLY_BINARY=:all: \
    pipenv install --deploy --verbose

FROM base

COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN set -eux; \
    mkdir -p /dump

COPY . .

ENTRYPOINT [ "python3", "/app/main.py" ]