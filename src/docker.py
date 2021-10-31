import logging
import os
import docker


class Docker:
    _DOCKER_SOCK = "/var/run/docker.sock"
    _IMAGE_REF = "jan-di/database-backup"

    def __init__(self, config):
        self._config = config

        if not os.path.exists(self._DOCKER_SOCK):
            raise RuntimeError(
                f"Docker Socket not found. Socket file must be created at {self._DOCKER_SOCK}"
            )

        self._client = docker.from_env()

        containers = self._client.containers.list(
            filters={
                "status": "running",
                "label": f"org.opencontainers.image.ref.name={self._IMAGE_REF}",
            }
        )

        if len(containers) == 0:
            raise RuntimeError("Cannot determine own container id!")
        elif len(containers) > 1:
            raise RuntimeError(
                "Detected another instance of this image."
                " Running multiple instances of the backup service is currently not supported!"
            )

        self._own_container = containers[0]

        logging.debug(f"Own Container ID: {self._own_container.id}")

    def get_targets(self, label):
        return self._client.containers.list(
            filters={"status": "running", "label": label}
        )

    def create_backup_network(self):
        self._network = self._client.networks.create(
            self._config.docker_network_name)
        self._network.connect(self._own_container.id)

    def remove_backup_network(self):
        if self._network is not None:
            self._network.disconnect(self._own_container.id)
            self._network.remove()
            self._network = None

    def connect_target(self, container):
        self._network.connect(container, aliases=[
                              self._config.docker_target_name])

    def disconnect_target(self, container):
        self._network.disconnect(container)
