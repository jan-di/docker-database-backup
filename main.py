import logging
import subprocess
import os
import datetime
import time
import sys

import pyAesCrypt
import humanize

from src.database import Database, DatabaseType
from src.healthcheck import Healthcheck
from src import settings
from src import docker

# Read config and setup logging
config, global_labels = settings.read()
logging.basicConfig(
    level=config.loglevel, format="%(asctime)s %(levelname)s %(message)s"
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
    healthcheck.start("Starting backup cycle.")

    # Find available database containers
    containers = docker_client.containers.list(
        filters={"status": "running", "label": settings.LABEL_PREFIX + "enable=true"}
    )

    container_count = len(containers)
    successful_count = 0

    if container_count:
        logging.info(f"Starting backup cycle with {len(containers)} container(s)..")

        network = docker_client.networks.create(config.docker_network_name)
        network.connect(own_container.id)

        for i, container in enumerate(containers):
            database = Database(container, global_labels)
            dump_file = f"/dump/{database.dump_file if database.dump_file != None else container.name}.sql"
            failed = False

            logging.info(
                "[{}/{}] Processing container {} {} ({})".format(
                    i + 1,
                    container_count,
                    container.short_id,
                    container.name,
                    database.type.name,
                )
            )

            if database.type == DatabaseType.unknown:
                logging.error(
                    "FAILED: Cannot read database type. Please specify via label."
                )
                failed = True

            logging.debug(
                "Login {}@host:{} using Password: {}".format(
                    database.username,
                    database.port,
                    "YES" if len(database.password) > 0 else "NO",
                )
            )

            # Create dump
            network.connect(container, aliases=[config.docker_target_name])

            try:
                env = os.environ.copy()

                if (
                    database.type == DatabaseType.mysql
                    or database.type == DatabaseType.mariadb
                ):
                    subprocess.run(
                        (
                            f'mysqldump'
                            f' --host="{config.docker_target_name}"'
                            f' --user="{database.username}"'
                            f' --password="{database.password}"'
                            f' --all-databases'
                            f' --ignore-database=mysql'
                            f' --ignore-database=information_schema'
                            f' --ignore-database=performance_schema'
                            f' > "{dump_file}"'
                        ),
                        shell=True,
                        text=True,
                        capture_output=True,
                        env=env,
                    ).check_returncode()
                elif database.type == DatabaseType.postgres:
                    env["PGPASSWORD"] = database.password
                    subprocess.run(
                        (
                            f'pg_dumpall'
                            f' --host="{config.docker_target_name}"'
                            f' --username="{database.username}"'
                            f' > "{dump_file}"'
                        ),
                        shell=True,
                        text=True,
                        capture_output=True,
                        env=env,
                    ).check_returncode()
            except subprocess.CalledProcessError as e:
                error_text = f"\n{e.stderr.strip()}".replace("\n", "\n> ").strip()
                logging.error(
                    f"FAILED. Error while crating dump. Return Code: {e.returncode}; Error Output:"
                )
                logging.error(f"{error_text}")
                failed = True

            if not failed and not os.path.exists(dump_file):
                logging.error(
                    f"FAILED: Dump cannot be created due to an unknown error!"
                )
                failed = True

            network.disconnect(container)

            dump_size = os.path.getsize(dump_file)

            # Compress pump
            if not failed and database.compress and dump_size > 0:
                logging.debug(f"Compressing dump (level: {database.compression_level})")
                compressed_dump_file = f"{dump_file}.gz"

                try:
                    if os.path.exists(compressed_dump_file):
                        os.remove(compressed_dump_file)

                    subprocess.check_output(
                        f'gzip -{database.compression_level} "{dump_file}"', shell=True
                    )
                except Exception as e:
                    logging.error(f"FAILED: Error while compressing: {e}")
                    failed = True

                processed_dump_size = os.path.getsize(compressed_dump_file)
                dump_file = compressed_dump_file
            else:
                database.compress = False

            # Encrypt dump
            if not failed and database.encrypt and dump_size > 0:
                logging.debug(f"Encrypting dump")
                encrypted_dump_file = f"{dump_file}.aes"

                try:
                    if os.path.exists(encrypted_dump_file):
                        os.remove(encrypted_dump_file)

                    pyAesCrypt.encryptFile(
                        dump_file, encrypted_dump_file, database.encryption_key
                    )
                    os.remove(dump_file)
                except Exception as e:
                    logging.error(f"FAILED: Error while encrypting: {e}")
                    failed = True

                processed_dump_size = os.path.getsize(encrypted_dump_file)
                dump_file = encrypted_dump_file

            else:
                database.encrypt = False

            if not failed:
                # Change Owner of dump
                os.chown(
                    dump_file, config.dump_uid, config.dump_gid
                )  # pylint: disable=maybe-no-member

                successful_count += 1
                logging.info(
                    "SUCCESS. Size: {}{}".format(
                        humanize.naturalsize(dump_size),
                        " ("
                        + humanize.naturalsize(processed_dump_size)
                        + " compressed/encrypted)"
                        if database.compress or database.encrypt
                        else "",
                    )
                )

        network.disconnect(own_container.id)
        network.remove()

    # Summarize backup cycle
    full_success = successful_count == container_count
    if container_count == 0:
        message = "Finished backup cycle. No databases to backup."
        logging.info(message)
        healthcheck.success(message)
    else:
        message = (
            f"Finished backup cycle. {successful_count}/{container_count} successful."
        )
        logging.info(message)
        if full_success:
            healthcheck.success(message)
        else:
            healthcheck.fail(message)

    # Scheduling next run
    if config.interval > 0:
        nextRun = datetime.datetime.now() + datetime.timedelta(seconds=config.interval)
        logging.info(
            "Scheduled next run at {}..".format(nextRun.strftime("%Y-%m-%d %H:%M:%S"))
        )

        time.sleep(config.interval)
    else:
        sys.exit()
