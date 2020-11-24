import docker
import re 
import subprocess
import os
from database import Database, DatabaseType

LABEL_PREFIX = "jan-di.database-backup."

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
        database = Database(container)

        print("[{}/{}] Processing container {} {} ({})".format(
            i + 1, 
            len(containers), 
            container.short_id,
            container.name,
            database.type.name
        ))

        if database.type == DatabaseType.unknown:
            print("Cannot read database type. Please specify via label.")

        network.connect(container, aliases = ["database-backup-target"])

        if database.type == DatabaseType.mysql or database.type == DatabaseType.mariadb:
            try:
                outFile = "/dump/{}_{}.sql".format(container.short_id, container.name)
                output = subprocess.check_output(
                    "mysqldump --host=database-backup-target --user={} --password={} --all-databases > {}".format(
                        database.username, 
                        database.password,
                        outFile),
                    shell=True,
                    text=True,
                    stderr=subprocess.STDOUT,
                ).strip()
            except subprocess.CalledProcessError as e:
                output = str(e.output).strip()

            print("...")
        elif database.type == DatabaseType.postgres:
            print("Not implemented yet ¯\\_(ツ)_/¯")
            
        network.disconnect(container)

    network.disconnect(ownContainerID)
    network.remove()
else:
    print("No databases to backup")
