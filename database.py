from enum import Enum
import re

class DatabaseType(Enum):
  unknown = -1
  auto = 0
  mysql = 1
  mariadb = 2
  postgres = 3

KNOWN_IMAGES = {
  # MySQL
  "mysql": DatabaseType.mysql,
  # MariaDB
  "mariadb": DatabaseType.mariadb,
  "linuxserver/mariadb": DatabaseType.mariadb,
  # Postgres
  "postgres": DatabaseType.postgres
}

class DatabaseDefaults:
  def __init__(self, port):
    self.port = port

class Database:
  LABEL_PREFIX = "jan-di.database-backup."
  DEFAULTS = {
    DatabaseType.unknown: DatabaseDefaults(0),
    DatabaseType.mysql: DatabaseDefaults(3306),
    DatabaseType.mariadb: DatabaseDefaults(3306),
    DatabaseType.postgres: DatabaseDefaults(5432)
  }
  IMAGE_REGEX = re.compile("^(.+?)(?::.+)?$")

  def __init__(self, container, settings):
    self._container = container

    # database type
    typeLabel = self._getLabel("type", "auto")
    try:
      self.type = DatabaseType[typeLabel]
    except AttributeError:
      self.type = DatabaseType["unknown"]

    if self.type == DatabaseType.auto:
      for tag in self._container.image.tags:
        matches = self.IMAGE_REGEX.match(tag)
        searchPart = matches.group(1)
        matchedType = KNOWN_IMAGES.get(searchPart, None)
        if matchedType != None:
          self.type = matchedType
          break
      if self.type == DatabaseType.auto:
        self.type = DatabaseType.unknown

    defaults = self.DEFAULTS.get(self.type)
    globalDefaults = settings.defaults

    # parameter
    self.port = self._getLabel("port", defaults.port)
    self.username = self._getLabel("username", globalDefaults.username)
    self.password = self._getLabel("password", globalDefaults.password)

  def _getLabel(self, key, default):
    return self._container.labels.get("{}{}".format(self.LABEL_PREFIX, key), default)