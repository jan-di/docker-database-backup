import logging
import os
import distutils.util

LABEL_PREFIX = "jan-di.database-backup."

CONFIG_DEFAULTS = {
    "interval": "3600",
    "verbose": "false",
    "dump_uid": "0",
    "dump_gid": "0",
}

LABEL_DEFAULTS = {
    "enable": "false",
    "username": "root",
    "password": "",
    "type": "auto",
    "port": "auto",
    "compress": "false",
}

class Config:
    def __init__(self, values):
        self.interval = int(values["interval"])
        if self.interval < 0:
            raise AttributeError("Interval must be positive")

        self.verbose = distutils.util.strtobool(values["verbose"])
        self.loglevel = logging.DEBUG if self.verbose else logging.INFO

        self.dump_uid = int(values["dump_uid"])
        self.dump_gid = int(values["dump_gid"])

def read():
    config_values = {}
    label_values = {}

    for key, default_value in CONFIG_DEFAULTS.items():
        env_name = _create_env_name(key)
        config_values[key] = os.getenv(env_name, default_value)

    for key, default_value in LABEL_DEFAULTS.items():
        env_name = _create_env_name(key, "global")
        label_values[key] = os.getenv(env_name, default_value)

    return Config(config_values), label_values

def _create_env_name(name, prefix = ""):
    if len(prefix) > 0:
        prefix = prefix + "."
    return "{}{}".format(prefix, name).upper().replace(".", "_")