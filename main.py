import docker
import re 
import subprocess
import os
import datetime
import humanize
import time
import sys
from database import Database, DatabaseType

DOCKER_SOCK = "/var/run/docker.sock"
LABEL_PREFIX = "jan-di.database-backup."

BACKUP_INTERVAL = int(os.getenv("BACKUP_INTERVAL", 3600))

if not os.path.exists(DOCKER_SOCK):
    print("ERROR: Docker Socket not found. Socket file must be provided to {}".format(DOCKER_SOCK))
    sys.exit(1)

client = docker.from_env()

while True:
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

    if BACKUP_INTERVAL > 0:
        nextRun = datetime.datetime.now() + datetime.timedelta(seconds=BACKUP_INTERVAL)
        print("Scheduled next run at {}..".format(nextRun.strftime("%Y-%m-%d %H:%M:%S")))

        time.sleep(BACKUP_INTERVAL)
    else:
        sys.exit()