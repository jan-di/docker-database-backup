import logging

from src.database import Database, DatabaseType
from src import settings
import subprocess
import os
import pyAesCrypt
import humanize


class Backup:
    def __init__(self, config, global_labels, docker, healthcheck):
        self._config = config
        self._global_labels = global_labels
        self._healthcheck = healthcheck
        self._docker = docker

    def run(self):
        # Start healthcheck integrations
        self._healthcheck.start("Starting backup cycle.")

        # Find available database containers
        containers = self._docker.get_targets(f"{settings.LABEL_PREFIX}enable=true")

        container_count = len(containers)
        successful_count = 0

        if container_count:
            logging.info(f"Starting backup cycle with {len(containers)} container(s)..")

            self._docker.create_backup_network()

            for i, container in enumerate(containers):
                database = Database(container, self._global_labels)
                dump_file = f"/dump/{database.dump_name if database.dump_name != None else container.name}.sql"
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
                self._docker.connect_target(container)

                try:
                    env = os.environ.copy()

                    if (
                        database.type == DatabaseType.mysql
                        or database.type == DatabaseType.mariadb
                    ):
                        subprocess.run(
                            (
                                f"mysqldump"
                                f' --host="{self._config.docker_target_name}"'
                                f' --user="{database.username}"'
                                f' --password="{database.password}"'
                                f" --all-databases"
                                f" --ignore-database=mysql"
                                f" --ignore-database=information_schema"
                                f" --ignore-database=performance_schema"
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
                                f"pg_dumpall"
                                f' --host="{self._config.docker_target_name}"'
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

                self._docker.disconnect_target(container)

                if not failed and (not os.path.exists(dump_file)):
                    logging.error(
                        f"FAILED: Dump cannot be created due to an unknown error!"
                    )
                    failed = True

                dump_size = os.path.getsize(dump_file)
                if not failed and dump_size == 0:
                    logging.error(f"FAILED: Dump file is empty!")
                    failed = True

                # Compress pump
                if not failed and database.compress:
                    logging.debug(
                        f"Compressing dump (level: {database.compression_level})"
                    )
                    compressed_dump_file = f"{dump_file}.gz"

                    try:
                        if os.path.exists(compressed_dump_file):
                            os.remove(compressed_dump_file)

                        subprocess.check_output(
                            f'gzip -{database.compression_level} "{dump_file}"',
                            shell=True,
                        )
                    except Exception as e:
                        logging.error(f"FAILED: Error while compressing: {e}")
                        failed = True

                    processed_dump_size = os.path.getsize(compressed_dump_file)
                    dump_file = compressed_dump_file

                # Encrypt dump
                if not failed and database.encrypt and dump_size > 0:
                    logging.debug(f"Encrypting dump")
                    encrypted_dump_file = f"{dump_file}.aes"

                    if database.encryption_key == None:
                        logging.error(f"FAILED: No encryption key specified!")
                        failed = True
                    else:
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

                if not failed:
                    # Change Owner of dump
                    os.chown(
                        dump_file, self._config.dump_uid, self._config.dump_gid
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

            self._docker.remove_backup_network()

        # Summarize backup cycle
        full_success = successful_count == container_count
        if container_count == 0:
            message = "Finished backup cycle. No databases to backup."
            logging.info(message)
            self._healthcheck.success(message)
        else:
            message = f"Finished backup cycle. {successful_count}/{container_count} successful."
            logging.info(message)
            if full_success:
                self._healthcheck.success(message)
            else:
                self._healthcheck.fail(message)
