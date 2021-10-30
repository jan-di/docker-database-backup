# Contributing

## Setup

1. Make sure [python3](https://www.python.org/) and [pipenv](https://pipenv.pypa.io) is installed
2. Create virtualenv `python -m venv .venv`
3. Install dependencies `pipenv install --dev`

## Test Locally

`docker build . -t docker-database-backup-debug && docker run -v /var/run/docker.sock:/var/run/docker.sock -e GLOBAL_COMPRESS=true -e SCHEDULE=5 docker-database-backup-debug`
