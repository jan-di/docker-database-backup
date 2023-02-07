# Contributing

## Setup

1. Install Requirements for [Visual Studio Code Dev Container](https://code.visualstudio.com/docs/remote/containers)
2. Start and connect to Dev Container

## Debugging

- (optional) Start test databases. Example: `docker compose -f tests/mariadb.docker-compose.yml up`
- Debug via Visual Studio Code Launchconfig
    - Custom Environment Variables can be put into `.vscode/.env`

## Test

docker build . -t docker-database-backup-debug && docker run  -v /var/run/docker.sock:/var/run/docker.sock -e GLOBAL_COMPRESS=true -e INTERVAL=5 docker-database-backup-debug