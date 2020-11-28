# Contributing

## Setup

1. Make sure python3 and pipenv is installed
2. Create virtualenv `python -m venv .venv`
3. Install dependencies `pipenv install --dev`

## Test Locally

`docker build . -t docker-database-backup-debug && docker run -e GLOBAL_COMPRESS=true -e INTERVAL=5 -v /var/run/docker.sock:/var/run/docker.sock docker-database-backup-debug`