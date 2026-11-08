# syntax=docker.io/docker/dockerfile:1

FROM docker.io/library/python:3.15-slim-trixie

LABEL jan-di.database-backup.instance_id="default"

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

# Add postgresql repository and install apt packages
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates wget; \
    mkdir -p /etc/apt/keyrings; \
    wget --quiet -O /etc/apt/keyrings/pgdg.asc https://www.postgresql.org/media/keys/ACCC4CF8.asc; \
    echo "deb [signed-by=/etc/apt/keyrings/pgdg.asc] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" > /etc/apt/sources.list.d/pgdg.list; \
    apt-get update; \
    apt-get upgrade -y; \
    apt-get install -y --no-install-recommends mariadb-client postgresql-client-18 tzdata zstd; \
    apt-get purge -y --auto-remove wget; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    mkdir -p /dump

COPY requirements.txt ./

RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt

WORKDIR /app
COPY . .

CMD [ "python3", "/app/main.py" ]