import datetime
import time
import socket
from croniter import croniter
from enum import Enum


class ScheduleMode(Enum):
    once = 1
    interval = 2
    cron = 3


class Schedule:
    def __init__(self, config):
        self._startup_run_done = False

        if config.schedule is None:
            self.mode = ScheduleMode.once
            self.run_at_startup = True
        else:
            try:
                self.interval = int(config.schedule)
                self.cron = None
                self.mode = ScheduleMode.interval
                self.run_at_startup = config.run_at_startup if config.run_at_startup is not None else True
            except ValueError:
                self.interval = None
                self.cron = config.schedule
                self.mode = ScheduleMode.cron
                self.run_at_startup = config.run_at_startup if config.run_at_startup is not None else False

        if self.mode == ScheduleMode.interval:
            if self.interval <= 0:
                raise ValueError("Interval must be at least one second!")

        if self.mode == ScheduleMode.cron:
            self.schedule_hash_id = str.encode(
                config.schedule_hash_id if config.schedule_hash_id is not None else socket.getfqdn())

            if not croniter.is_valid(self.cron, hash_id=self.schedule_hash_id):
                raise ValueError("Invalid cron expression!")

    def get_next(self):
        now = datetime.datetime.now()

        if self.run_at_startup and not self._startup_run_done:
            self._startup_run_done = True
            return now

        if self.mode == ScheduleMode.once:
            return None
        elif self.mode == ScheduleMode.interval:
            return now + datetime.timedelta(seconds=self.interval)
        elif self.mode == ScheduleMode.cron:
            cron = croniter(self.cron, now, hash_id=self.schedule_hash_id)
            return cron.get_next(datetime.datetime)

    def get_humanized_schedule(self):
        run_at_startup_suffix = ', run at startup' if self.run_at_startup else ''

        if self.mode == ScheduleMode.once:
            return 'Run once'
        elif self.mode == ScheduleMode.interval:
            return f'Interval ({self.interval} seconds){run_at_startup_suffix}'
        elif self.mode == ScheduleMode.cron:
            return f'Cron ({self.cron}){run_at_startup_suffix}'

    def wait_until(self, until):
        now = datetime.datetime.now()

        diff = (until - now).total_seconds()
        if diff > 0:
            time.sleep(diff)
