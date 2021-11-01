from enum import Enum
import re
import distutils.util
import tempora

from . import settings


class DatabaseType(Enum):
    unknown = -1
    auto = 0
    mysql = 1
    mariadb = 2
    postgres = 3


KNOWN_IMAGES = {
    # MySQL
    "mysql": "mysql",
    "bitnami/mysql": "mysql",
    "mysql/mysql-server": "mysql",
    # MariaDB
    "mariadb": "mariadb",
    "bitnami/mariadb": "mariadb",
    "linuxserver/mariadb": "mariadb",
    "mariadb/server": "mariadb",
    # Postgres
    "postgres": "postgres",
    "bitnami/postgresql": "postgres",
}

TYPE_DEFAULTS = {
    "unknown": {
        "port": "0"
    },
    "mysql": {
        "port": "3306",
    },
    "mariadb": {
        "port": "3306",
    },
    "postgres": {
        "port": "5432",
    }
}

RETENTION_DEFAULTS = {
    "none": {
        "dump_timestamp": "false",
        "retention_min_count": "1",
        "retention_min_age": "0s",
        "retention_max_count": "1",
        "retention_max_age": "0s"
    },
    "simple": {
        "dump_timestamp": "true",
        "retention_min_count": "10",
        "retention_min_age": "0s",
        "retention_max_count": "0",
        "retention_max_age": "1 month"
    },
    "all": {
        "dump_timestamp": "true",
        "retention_min_count": "1",
        "retention_min_age": "0s",
        "retention_max_count": "0",
        "retention_max_age": "0s"
    }
}


class Database:
    def __init__(self, container, global_labels):
        self._load_labels(global_labels)
        local_labels = self._get_labels_from_container(container)
        self._load_labels(local_labels)
        self._resolve_labels(container)

    def _load_labels(self, values, only_auto_values=False):
        for key in settings.LABEL_DEFAULTS.keys():
            if key in values and (not only_auto_values or getattr(self, key) == "auto"):
                setattr(self, key, values[key])

    def _get_labels_from_container(self, container):
        labels = {}

        for key, value in container.labels.items():
            if key.startswith(settings.LABEL_PREFIX):
                short_key = key[len(settings.LABEL_PREFIX):len(key)]
                labels[short_key] = value

        return labels

    def _resolve_labels(self, container):
        # Resolve database type
        if self.type == "auto":
            image_regex = re.compile("^(.+?)(?::.+)?$")
            for tag in container.image.tags:
                matches = image_regex.match(tag)
                matched_type = KNOWN_IMAGES.get(matches.group(1), None)
                if matched_type is not None:
                    self.type = matched_type
                    break
            if self.type == "auto":
                self.type = "unknown"

        # Resolve default values based on other attributes
        self._load_labels(TYPE_DEFAULTS.get(self.type, {}), True)
        self._load_labels(RETENTION_DEFAULTS.get(
            self.retention_policy, {}), True)

        # Other
        self.type = DatabaseType[self.type]
        self.port = int(self.port)
        self.compress = distutils.util.strtobool(self.compress)
        self.compression_level = int(self.compression_level)
        self.encrypt = distutils.util.strtobool(self.encrypt)
        self.dump_timestamp = distutils.util.strtobool(self.dump_timestamp)
        self.retention_min_count = max(int(self.retention_min_count), 1)
        self.retention_min_age = tempora.parse_timedelta(
            self.retention_min_age)
        self.retention_max_count = max(int(self.retention_max_count), 0)
        self.retention_max_age = tempora.parse_timedelta(
            self.retention_max_age)
