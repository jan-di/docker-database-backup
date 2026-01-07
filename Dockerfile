FROM docker.io/library/python:3.14-trixie

LABEL jan-di.database-backup.instance_id="default"

# Add postgresql repository
RUN set -eu; \
    mkdir -p /etc/apt/keyrings; \
    wget --quiet -O /etc/apt/keyrings/pgdg.asc https://www.postgresql.org/media/keys/ACCC4CF8.asc; \
    sh -c 'echo "deb [signed-by=/etc/apt/keyrings/pgdg.asc] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1

# Install apt packages
RUN set -eux; \
    apt-get update; \
    apt-get install -y mariadb-client postgresql-client-18 tzdata; \
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