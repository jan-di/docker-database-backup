FROM docker.io/library/python:3.9.16-bullseye 

LABEL jan-di.database-backup.instance_id="default"

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

RUN set -eux; \
    apt-get update; \
    apt-get install -y mariadb-client postgresql-client tzdata; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    mkdir -p /dump

COPY requirements.txt ./

RUN set -eux; \
    pip install --no-cache-dir pip-tools; \
    pip-sync requirements.txt --pip-args '--user --only-binary=:all':

WORKDIR /app
COPY . .

CMD [ "python3", "/app/main.py" ]