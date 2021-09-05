FROM python:3.9-bullseye AS base

LABEL org.opencontainers.image.ref.name="jan-di/database-backup"

RUN set -eux; \
	apt-get update; \
    apt-get upgrade -qq -o=Dpkg::Use-Pty=0 -y --with-new-pkgs; \
	apt-get install -qq -o=Dpkg::Use-Pty=0 -y --no-install-recommends \
		mariadb-client \
        postgresql-client \
        tzdata \
	; \
	rm -rf /var/lib/apt/lists/*

FROM base AS python-deps

ENV PIPENV_VENV_IN_PROJECT=1 \
    CI=1

RUN set -eux; \
    pip install pipenv

COPY Pipfile .
COPY Pipfile.lock .
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