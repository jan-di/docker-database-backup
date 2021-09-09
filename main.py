import logging
import sys

from src.healthcheck import Healthcheck
from src.schedule import Schedule
from src.docker import Docker
from src.backup import Backup
from src import settings


# Read config and setup logging
config, global_labels = settings.read()
logging.basicConfig(
    level=config.loglevel, format="%(asctime)s %(levelname)s %(message)s"
)
logging.info("Starting backup service")

# Initializing Backup
docker = Docker(config)
healthcheck = Healthcheck(config)
backup = Backup(config, global_labels, docker, healthcheck)

# Initializing Scheduler
schedule = Schedule(config)
logging.info(f"Schedule: {schedule.get_humanized_schedule()}")


while True:
    backup.run()

    # Scheduling next run
    next_run = schedule.get_next()
    if next_run != None:
        logging.info(
            f"Scheduled next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}.."
        )

        schedule.wait_until(next_run)
    else:
        logging.info("Exiting backup service")
        sys.exit()
