FROM docker.io/library/python:3.9.8-bullseye AS base

LABEL jan-di.database-backup.instance_id="default"

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

RUN set -eux; \
    apt-get update; \
    apt-get install -y mariadb-client postgresql-client tzdata; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    mkdir -p /dump

FROM base AS python-deps

COPY Pipfile Pipfile.lock  ./
RUN set -eux; \
    pip install --no-cache-dir pipenv; \
    CI=1 PIPENV_VENV_IN_PROJECT=1 PIP_ONLY_BINARY=:all: pipenv install --deploy --clear

FROM base

COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

WORKDIR /app
COPY . .

CMD [ "python3", "/app/main.py" ]