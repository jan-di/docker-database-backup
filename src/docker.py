import logging
import os
import docker
from src import settings


class Docker:
    _DOCKER_SOCK = "/var/run/docker.sock"

    def __init__(self, config):
        self._config = config

        if not os.path.exists(self._DOCKER_SOCK):
            raise RuntimeError(
                f"Docker Socket not found. Socket file must be created at {self._DOCKER_SOCK}"
            )

        self._client = docker.from_env()

        logging.debug(f"Instance ID: {config.instance_id}")

        containers = self._client.containers.list(
            filters={
                "status": "running",
                "label": f"{settings.LABEL_PREFIX}instance_id={config.instance_id}",
            }
        )

        if len(containers) == 0:
            raise RuntimeError(
                f"Cannot determine own container id! InstanceId: {config.instance_id}")
        elif len(containers) > 1:
            raise RuntimeError(
                f"Detected another instance of this image with the same instance id. InstanceId: {config.instance_id}"
                " To run multiple instances of the service, each container must have a unique instance id assigned."
            )

        self._own_container = containers[0]

        logging.debug(f"Own Container ID: {self._own_container.id}")

    def get_targets(self, label):
        return self._client.containers.list(
            filters={"status": "running", "label": label}
        )

    def create_backup_network(self):
        network_name = f"{self._config.docker_network_name}_{self._config.instance_id}"

        self._network = self._client.networks.create(network_name)
        self._network.connect(self._own_container.id)

    def remove_backup_network(self):
        if self._network is not None:
            self._network.disconnect(self._own_container.id)
            self._network.remove()
            self._network = None

    def get_target_name(self, container):
        return f"{self._config.docker_target_name}_{self._config.instance_id}"

    def connect_target(self, container):
        target_name = self.get_target_name(container)

        self._network.connect(container, aliases=[target_name])

    def disconnect_target(self, container):
        self._network.disconnect(container)
