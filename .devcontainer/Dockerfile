# https://github.com/devcontainers/images/tree/main/src/python
FROM mcr.microsoft.com/vscode/devcontainers/python:3-3.14-trixie

# Add postgresql repository
RUN set -eu; \
    mkdir -p /etc/apt/keyrings; \
    wget --quiet -O /etc/apt/keyrings/pgdg.asc https://www.postgresql.org/media/keys/ACCC4CF8.asc; \
    sh -c 'echo "deb [signed-by=/etc/apt/keyrings/pgdg.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release --codename --short)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends mariadb-client postgresql-client-18
RUN pip install pip-tools

LABEL jan-di.database-backup.instance_id="devcontainer"
RUN mkdir /dump && chmod 777 /dump