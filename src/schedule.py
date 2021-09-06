import datetime
import time
from croniter import croniter
from enum import Enum

class ScheduleMode(Enum):
  once = 1
  interval = 2
  cron = 3

class Schedule:
    def __init__(self, config):
        if config.schedule == None:
            self.mode = ScheduleMode.once
        else:
            try:
                self.interval = int(config.schedule)
                self.cron = None
                self.mode = ScheduleMode.interval
            except ValueError:
                self.interval = None
                self.cron = config.schedule
                self.mode = ScheduleMode.cron

        if self.mode == ScheduleMode.interval:
            if self.interval <= 0:
                raise ValueError("Interval must be at least one second!")

        if self.mode == ScheduleMode.cron:
            if not croniter.is_valid(self.cron):
                raise ValueError("Invalid cron expression!")

    def get_next(self):
        now = datetime.datetime.now()

        if self.mode == ScheduleMode.once:
            return None
        elif self.mode == ScheduleMode.interval:
            return now + datetime.timedelta(seconds=self.interval)
        elif self.mode == ScheduleMode.cron:
            cron = croniter(self.cron, now)
            return cron.get_next(datetime.datetime)

    def get_humanized_schedule(self):
        if self.mode == ScheduleMode.once:
            return 'Run once'
        elif self.mode == ScheduleMode.interval:
            return f'Interval ({self.interval} seconds)'
        elif self.mode == ScheduleMode.cron:
            return f'Cron ({self.cron})'

    def wait_until(self, until):
        now = datetime.datetime.now()

        diff = (until - now).total_seconds()
        if diff > 0:
            time.sleep(diff)

