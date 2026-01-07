import logging

from src.database import Database, DatabaseType
from src import settings
import subprocess
import os
import glob
import datetime
import pyAesCrypt
import humanize
import re
import math


class Backup:
    DUMP_DIR = "/dump"
    DUMP_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")

    def __init__(self, config, global_labels, docker, healthcheck, metrics):
        self._config = config
        self._global_labels = global_labels
        self._healthcheck = healthcheck
        self._docker = docker
        self._metrics = metrics

    def run(self):
        # Start healthcheck integrations
        self._healthcheck.start("Starting backup cycle.")
        cycle_start = datetime.datetime.now(datetime.timezone.utc)

        # Find available database containers
        containers = self._docker.get_targets(
            f"{settings.LABEL_PREFIX}enable=true")

        # Process only container with the name in the whitelist
        if self._config.whitelist is not None:
            container_whitelist = [x.strip() for x in self._config.whitelist.split(',') if x]
            if len(container_whitelist) > 0:
                logging.info(f"Container whitelist is active! Only these names are processed: {container_whitelist}")
                # Removes all containers from the list, which are not included in the filter
                containers = [x for x in containers if x.name in container_whitelist]

        # Process all container, but not with the name in the blacklist
        if self._config.blacklist is not None:   
            container_blacklist = [x.strip() for x in self._config.blacklist.split(',') if x]
            if len(container_blacklist) > 0:
                logging.info(f"Container blacklist is active! The following names will be not processed: {container_blacklist}")
                # Removes all containers from the list, which are not included in the filter
                containers = [x for x in containers if x.name not in container_blacklist]

        container_count = len(containers)
        successful_count = 0
        self._metrics.init_metrics()

        if container_count:
            logging.info(
                f"Starting backup cycle with {len(containers)} container(s)..")

            self._docker.create_backup_network()

            for i, container in enumerate(containers):
                start = datetime.datetime.now(datetime.timezone.utc)
                database = Database(container, self._global_labels)
                dump_name_part = (
                    database.dump_name if len(
                        database.dump_name) > 0 else container.name
                )
                dump_timestamp_part = (
                    start.strftime("_%Y-%m-%d_%H-%M-%S")
                    if database.dump_timestamp
                    else ""
                )
                dump_file = f"{self.DUMP_DIR}/{dump_name_part}{dump_timestamp_part}.sql"
                failed = False
                metric_labels = {
                    "name": dump_name_part,
                    "type": database.type.name
                }

                container_started_at = datetime.datetime.fromisoformat(
                    container.attrs['State']['StartedAt'].partition('.')[0] + '.000000+00:00')
                container_uptime = start - container_started_at

                logging.info(
                    "[{}/{}] Processing container {} {} ({})".format(
                        i + 1,
                        container_count,
                        container.short_id,
                        container.name,
                        database.type.name,
                    )
                )

                if not self.DUMP_NAME_PATTERN.match(dump_name_part):
                    logging.error(
                        f"> FAILED: Invalid dump name. Name must match '{self.DUMP_NAME_PATTERN.pattern}'."
                    )
                    failed = True

                if not failed and database.type == DatabaseType.unknown:
                    logging.error(
                        "> FAILED: Cannot resolve database type. Please specify via label."
                    )
                    failed = True

                if not failed:
                    logging.debug(
                        "> Login {}@host:{} using Password: {}".format(
                            database.username,
                            database.port,
                            "YES" if len(database.password) > 0 else "NO",
                        )
                    )

                    # Create dump
                    self._docker.connect_target(container)
                    target_host = self._docker.get_target_name()

                    try:
                        env = os.environ.copy()

                        if (
                            database.type == DatabaseType.mysql
                            or database.type == DatabaseType.mariadb
                        ):
                            subprocess.run(
                                (
                                    f"mysqldump"
                                    f' --host="{target_host}"'
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
                                    f' --host="{target_host}"'
                                    f' --username="{database.username}"'
                                    f' > "{dump_file}"'
                                ),
                                shell=True,
                                text=True,
                                capture_output=True,
                                env=env,
                            ).check_returncode()
                    except subprocess.CalledProcessError as e:
                        error_text = f"\n{e.stderr.strip()}".replace(
                            "\n", "\n> "
                        ).strip()
                        logging.error(
                            f"> FAILED. Error while crating dump. Return Code: {e.returncode}; Error Output:"
                        )
                        logging.error(f"{error_text}")
                        failed = True

                    self._docker.disconnect_target(container)

                if not failed and (not os.path.exists(dump_file)):
                    logging.error(
                        "> FAILED: Dump cannot be created due to an unknown error!"
                    )
                    failed = True

                if not failed:
                    dump_size = os.path.getsize(dump_file)
                    processed_dump_size = dump_size
                    if dump_size == 0:
                        logging.error("> FAILED: Dump file is empty!")
                        failed = True

                # Compress pump
                if not failed and database.compress:
                    logging.debug(
                        f"> Compressing dump (level: {database.compression_level})"
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
                        logging.error(
                            f"> FAILED: Error while compressing: {e}")
                        failed = True

                    processed_dump_size = os.path.getsize(compressed_dump_file)
                    dump_file = compressed_dump_file

                # Encrypt dump
                if not failed and database.encrypt and dump_size > 0:
                    logging.debug("> Encrypting dump")
                    encrypted_dump_file = f"{dump_file}.aes"

                    if not database.encryption_key:
                        logging.error(
                            "> FAILED: No encryption key specified!")
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
                            logging.error(
                                f"> FAILED: Error while encrypting: {e}")
                            failed = True

                        processed_dump_size = os.path.getsize(
                            encrypted_dump_file)
                        dump_file = encrypted_dump_file

                if not failed:
                    # Change Owner of dump
                    os.chown(
                        dump_file, self._config.dump_uid, self._config.dump_gid
                    )  # pylint: disable=maybe-no-member
                    # todo catch errors when chowning file

                if not failed:
                    successful_count += 1
                    logging.info(
                        "> SUCCESS. Size: {}{}".format(
                            humanize.naturalsize(dump_size),
                            " ("
                            + humanize.naturalsize(processed_dump_size)
                            + " compressed/encrypted)"
                            if database.compress or database.encrypt
                            else "",
                        )
                    )
                elif container_uptime < database.grace_time:
                    successful_count += 1
                    logging.info("> Ignore failure because of grace time")

                # Cleanup
                if database.dump_timestamp:
                    glob_expression = f"{self.DUMP_DIR}/{dump_name_part}_*.*"
                    files = sorted(glob.glob(glob_expression), reverse=True)
                    kept_files = 0
                    if len(files) > 0:

                        for i in range(len(files)):
                            # Calculate Age
                            basename = os.path.basename(files[i])
                            age_regex = re.compile(
                                r"^.+_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\..+$")
                            timestamp_str = age_regex.match(basename).group(1)
                            timestamp = datetime.datetime.strptime(
                                timestamp_str, '%Y-%m-%d_%H-%M-%S').replace(tzinfo=datetime.timezone.utc)
                            delta = start - timestamp

                            # Check if dump file should be deleted
                            delete = False
                            if i <= database.retention_min_count - 1:
                                logging.debug(f"{files[i]} KEEP (min_count)")
                            elif delta <= database.retention_min_age:
                                logging.debug(f"{files[i]} KEEP (min_age)")
                            elif database.retention_max_count > 0 and i > database.retention_max_count - 1:
                                logging.debug(f"{files[i]} DELETE (max_count)")
                                delete = True
                            elif database.retention_max_age.total_seconds() > 0 and delta > database.retention_max_age:
                                logging.debug(f"{files[i]} DELETE (max_aget)")
                                delete = True
                            else:
                                logging.debug(f"{files[i]} KEEP (default)")

                            if delete:
                                os.remove(files[i])
                            else:
                                kept_files += 1
                else:
                    # Dummy files to get useful metrics
                    files = [None]
                    kept_files = 1

                    logging.info(
                        f"> Retention ({database.retention_policy}). Kept {kept_files}/{len(files)} files")

                end = datetime.datetime.now(datetime.timezone.utc)
                duration = end - start

                # Add database specific metrics
                if "dump_size" in locals():
                    self._metrics.add_multi_value(
                        'backup_dump_raw_size', metric_labels, dump_size)
                if "processed_dump_size" in locals():
                    self._metrics.add_multi_value(
                        'backup_dump_size', metric_labels, processed_dump_size)
                self._metrics.add_multi_value(
                    'backup_status', metric_labels, int(not failed))
                self._metrics.add_multi_value(
                    'backup_duration', metric_labels, math.ceil(duration.total_seconds() * 1000))
                self._metrics.add_multi_value(
                    'backup_retention_kept_files', metric_labels, kept_files)
                self._metrics.add_multi_value(
                    'backup_retention_checked_files', metric_labels, len(files))

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

        cycle_end = datetime.datetime.now(datetime.timezone.utc)
        cycle_duration = cycle_end - cycle_start

        # Set general metrics
        self._metrics.set_single_value('targets', container_count)
        self._metrics.set_single_value(
            'successful_targets', successful_count)
        self._metrics.set_single_value(
            'cycle_duration', math.ceil(cycle_duration.total_seconds() * 1000))
        self._metrics.flush_metrics()
