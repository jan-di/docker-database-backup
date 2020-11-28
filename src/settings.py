import os

LABEL_PREFIX = "jan-di.database-backup."

CONFIG_DEFAULTS = {
    "interval": "3600"
}

LABEL_DEFAULTS = {
    "enable": "false",
    "username": "root",
    "password": "",
    "type": "auto",
    "port": "auto",
}

class Config:
    def __init__(self, values):
        self.interval = int(values["interval"])
        if self.interval < 0:
            raise AttributeError("Interval must be positive")

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