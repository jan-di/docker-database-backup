import logging
import sys

from src.healthcheck import Healthcheck
from src.schedule import Schedule
from src.docker import Docker
from src.backup import Backup
from src.metrics import Metrics
from src import settings

# Read config and setup logging
config, global_labels = settings.read()
logging.basicConfig(
    level=config.loglevel, format="%(asctime)s %(levelname)s %(message)s"
)
logging.info("Starting backup service")

# Initializin Backup
docker = Docker(config)
metrics = Metrics(config)
healthcheck = Healthcheck(config)
backup = Backup(config, global_labels, docker, healthcheck, metrics)

# Initializing Scheduler
schedule = Schedule(config)
logging.info(f"Schedule: {schedule.get_humanized_schedule()}")

while True:
    # Scheduling next run
    next_run = schedule.get_next()
    if next_run is not None:
        logging.info(
            f"Scheduled next run at {next_run.strftime('%Y-%m-%d %H:%M:%S')}.."
        )

        schedule.wait_until(next_run)
    else:
        logging.info("Exiting backup service")
        sys.exit()

    backup.run()
