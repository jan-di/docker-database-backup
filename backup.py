import docker
import re 
import subprocess
import os
from enum import Enum

LABEL_PREFIX = "jan-di.database-backup."

def getLabel(container, key, default = None):
    return container.labels.get("{}{}".format(LABEL_PREFIX, key), default)

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
imageRegex = re.compile("^(.+?)(?::.+)?$")

client = docker.from_env()
containers = client.containers.list(
    filters = {
        "label": LABEL_PREFIX + "enable=true"
    }
)

if len(containers):
    ownContainerID = subprocess.check_output("basename $(cat /proc/1/cpuset)", shell=True, text=True).strip()

    network = client.networks.create("docker-database-backup")
    network.connect(ownContainerID)

    for i, container in enumerate(containers):
        # check database type
        typeLabel = getLabel(container, "type", "auto")
        try:
            databaseType = DatabaseType[typeLabel]
        except AttributeError as e:
            databaseType = DatabaseType["unknown"]
        
        # resolve auto type using image names
        if databaseType == DatabaseType.auto:
            for tag in container.image.tags:
                matches = imageRegex.match(tag)
                searchPart = matches.group(1)
                matchedType = KNOWN_IMAGES.get(searchPart, None)
                if matchedType != None:
                    databaseType = matchedType
            if databaseType == DatabaseType.auto:
                databaseType = DatabaseType.unknown

        print("[{}/{}] Processing container {} {} ({})".format(i + 1, len(containers), container.short_id, container.name, databaseType.name))

        if databaseType == DatabaseType.unknown:
            print("Cannot read database type. Please specify via label.")

        network.connect(container, aliases = ["database-backup-target"])

        username = getLabel(container, "username", "root")
        password = getLabel(container, "password", "")

        if databaseType == DatabaseType.mysql or databaseType == DatabaseType.mariadb:
            try:
                outFile = "/dump/{}_{}.sql".format(container.short_id, container.name)
                output = subprocess.check_output(
                    "mysqldump --host=database-backup-target --user={} --password={} --all-databases > {}".format(username, password, outFile),
                    shell=True,
                    text=True,
                    stderr=subprocess.STDOUT,
                ).strip()
            except subprocess.CalledProcessError as e:
                output = str(e.output).strip()

            print(output)
            
        network.disconnect(container)

    network.disconnect(ownContainerID)
    network.remove()
