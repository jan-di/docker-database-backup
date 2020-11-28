import re 
import subprocess
import os
import datetime
import time
import sys

import humanize

from src.database import Database, DatabaseType
from src import settings
from src import docker

config, global_labels = settings.read()
docker_client = docker.get_client()

config.verbose = False

while True:
    containers = docker_client.containers.list(
        filters = {
            "label": settings.LABEL_PREFIX + "enable=true"
        }
    )

    if len(containers):
        ownContainerID = subprocess.check_output("basename $(cat /proc/1/cpuset)", shell=True, text=True).strip()

        network = docker_client.networks.create("docker-database-backup")
        network.connect(ownContainerID)

        for i, container in enumerate(containers):
            database = Database(container, global_labels)

            print("[{}/{}] Processing container {} {} ({})".format(
                i + 1, 
                len(containers), 
                container.short_id,
                container.name,
                database.type.name
            ))

            if config.verbose:
                print("> Login {}@host:{} using Password: {}".format(database.username, database.port, "YES" if len(database.password) > 0 else "NO"))

            if database.type == DatabaseType.unknown:
                print("Cannot read database type. Please specify via label.")

            network.connect(container, aliases = ["database-backup-target"])
            outFile = "/dump/{}_{}.sql".format(container.short_id, container.name)

            if database.type == DatabaseType.mysql or database.type == DatabaseType.mariadb:
                try:
                    
                    output = subprocess.check_output(
                        ("mysqldump --host=database-backup-target --user={} --password={}"
                        " --all-databases"
                        " --ignore-database=mysql"
                        " --ignore-database=information_schema"
                        " --ignore-database=performance_schema"
                        " > {}").format(
                            database.username, 
                            database.password,
                            outFile),
                        shell=True,
                        text=True,
                        stderr=subprocess.STDOUT,
                    ).strip()
                except subprocess.CalledProcessError as e:
                    output = str(e.output).strip()
            elif database.type == DatabaseType.postgres:
                print("Not implemented yet ¯\\_(ツ)_/¯")
                
            network.disconnect(container)

            if (os.path.exists(outFile)):
                size = os.path.getsize(outFile)
                print("Success. Size: {}".format(humanize.naturalsize(size)))

        network.disconnect(ownContainerID)
        network.remove()
    else:
        print("No databases to backup")

    if config.interval > 0:
        nextRun = datetime.datetime.now() + datetime.timedelta(seconds=config.interval)
        print("Scheduled next run at {}..".format(nextRun.strftime("%Y-%m-%d %H:%M:%S")))

        time.sleep(config.interval)
    else:
        sys.exit()