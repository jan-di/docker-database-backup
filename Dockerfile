FROM docker.io/library/python:3.9.15-bullseye AS base

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

COPY requirements.txt ./

RUN set -eux; \
    pip install --no-cache-dir pip-tools; \
    pip-sync requirements.txt --pip-args '--user --only-binary=:all':

FROM base

COPY --from=python-deps /root/.local /root/.local

WORKDIR /app
COPY . .

CMD [ "python3", "/app/main.py" ]