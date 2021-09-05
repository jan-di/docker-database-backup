FROM python:3.9-bullseye AS base

LABEL org.opencontainers.image.ref.name="jan-di/database-backup"

RUN set -eux; \
	apt-get update; \
    apt-get upgrade -y --with-new-pkgs; \
	apt-get install -y --no-install-recommends \
		mariadb-client \
        postgresql-client \
        tzdata \
	; \
	rm -rf /var/lib/apt/lists/*

FROM base AS python-deps

RUN set -eux; \
    pip install pipenv

COPY Pipfile .
COPY Pipfile.lock .
ENV PIPENV_VENV_IN_PROJECT=1
RUN set -eux; \
    pipenv install --deploy

FROM base

COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

WORKDIR /app

RUN set -eux; \
    mkdir -p /dump

ENV PYTHONUNBUFFERED=1

COPY . .

ENTRYPOINT [ "python3", "/app/main.py" ]