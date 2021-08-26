import os
import sys

import docker

DOCKER_SOCK = "/var/run/docker.sock"
IMAGE_REF = "jan-di/database-backup"

def get_client():
    if not os.path.exists(DOCKER_SOCK):
        print(f"ERROR: Docker Socket not found. Socket file must be created at {DOCKER_SOCK}")
        sys.exit(1)

    return docker.from_env()

def get_own_container(docker_client):
    containers = docker_client.containers.list(
        filters = {
            "status": "running",
            "label": f"org.opencontainers.image.ref.name={IMAGE_REF}"
        }
    )

    if len(containers) == 0:
        print("ERROR: Cannot determine own container id!")
        sys.exit(1)
    elif len(containers) > 1:
        print("ERROR: Detected another instance of this image. Running multiple instances of the backup service is currently not supported!")
        sys.exit(1)

    return containers[0]