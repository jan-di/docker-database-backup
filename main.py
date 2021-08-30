import logging
import subprocess
import os
import datetime
import time
import sys

import humanize

from src.database import Database, DatabaseType
from src.healthcheck import Healthcheck
from src import settings
from src import docker

# Read config and setup logging
config, global_labels = settings.read()
logging.basicConfig(
    level=config.loglevel,
    format='%(asctime)s %(levelname)s %(message)s'
)
logging.info("Starting backup service")

# Connecting to docker API
docker_client = docker.get_client()
own_container = docker.get_own_container(docker_client)
logging.debug(f"Own Container ID: {own_container.id}")

# Initializing Healthcheck integrations
healthcheck = Healthcheck(config)

while True:
    # Start healthcheck integrations
    healthcheck.start('Starting backup cycle.')

    # Find available database containers
    containers = docker_client.containers.list(
        filters = {
            "status": "running",
            "label": settings.LABEL_PREFIX + "enable=true"
        }
    )

    container_count = len(containers)
    successful_count = 0
    
    if container_count:
        logging.info(f"Starting backup cycle with {len(containers)} container(s)..")

        network = docker_client.networks.create("docker-database-backup")
        network.connect(own_container.id)

        for i, container in enumerate(containers):
            database = Database(container, global_labels)

            logging.info("[{}/{}] Processing container {} {} ({})".format(
                i + 1, 
                container_count, 
                container.short_id,
                container.name,
                database.type.name
            ))

            logging.debug("Login {}@host:{} using Password: {}".format(database.username, database.port, "YES" if len(database.password) > 0 else "NO"))
            if database.compress:
                logging.debug("Compressing backup")

            if database.type == DatabaseType.unknown:
                logging.error("FAILED: Cannot read database type. Please specify via label.")

            network.connect(container, aliases = ["database-backup-target"])
            outFile = "/dump/{}.sql".format(container.name)
            error_code = 0
            error_text = ""
            
            try:
                env = os.environ.copy()

                if database.type == DatabaseType.mysql or database.type == DatabaseType.mariadb:
                    subprocess.run(
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
                        capture_output=True,
                        env=env,
                    ).check_returncode()
                elif database.type == DatabaseType.postgres:
                    env["PGPASSWORD"] = database.password
                    subprocess.run(
                        ("pg_dumpall --host=database-backup-target --username={}"
                        " > {}").format(
                            database.username, 
                            outFile),
                        shell=True,
                        text=True,
                        capture_output=True,
                        env=env
                    ).check_returncode()
            except subprocess.CalledProcessError as e:
                error_code = e.returncode
                error_text = f"\n{e.stderr.strip()}".replace('\n', '\n> ').strip()

            network.disconnect(container)

            if error_code > 0:
                logging.error(f"FAILED. Return Code: {error_code}; Error Output:")
                logging.error(f"{error_text}")
            else:
                if (os.path.exists(outFile)):
                    uncompressed_size = os.path.getsize(outFile)
                    if database.compress and uncompressed_size > 0:
                        if os.path.exists(outFile + ".gz"):
                            os.remove(outFile + ".gz")
                        subprocess.check_output("gzip {}".format(outFile), shell=True)
                        outFile = outFile + ".gz"
                        compressed_size = os.path.getsize(outFile)
                    else:
                        database.compress = False

                    os.chown(outFile, config.dump_uid, config.dump_gid) # pylint: disable=maybe-no-member

                    successful_count += 1
                    logging.info("SUCCESS. Size: {}{}".format(humanize.naturalsize(uncompressed_size), " (" + humanize.naturalsize(compressed_size) + " compressed)" if database.compress else ""))

        network.disconnect(own_container.id)
        network.remove()
    
    # Summarize backup cycle
    full_success = (successful_count == container_count)
    if container_count == 0:
        message = "Finished backup cycle. No databases to backup."
        logging.info(message)
        healthcheck.success(message)
    else:
        message = f"Finished backup cycle. {successful_count}/{container_count} successful."
        logging.info(message)
        if full_success:
            healthcheck.success(message)
        else:
            healthcheck.fail(message)

    # Scheduling next run
    if config.interval > 0:
        nextRun = datetime.datetime.now() + datetime.timedelta(seconds=config.interval)
        logging.info("Scheduled next run at {}..".format(nextRun.strftime("%Y-%m-%d %H:%M:%S")))

        time.sleep(config.interval)
    else:
        sys.exit()