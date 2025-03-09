#!/usr/bin/env python3
""" 
"""
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Config:
    SRC_DIR: str
    BACKUP_DIR: str
    PROJECT_NAME: str
    BACKUP_RETENTION_HOURLY: int
    BACKUP_RETENTION_DAILY: int
    BACKUP_RETENTION_WEEKLY: int
    BACKUP_RETENTION_MONTHLY: int
    BACKUP_RETENTION_YEARLY: int

    @property
    def _rate(self) -> str:
        if datetime.now().timetuple().tm_yday == 1:
            return "yearly"
        if datetime.now().timetuple().tm_mday == 1:
            return "monthly"
        if (datetime.now().timetuple().tm_wday + 1) == 7:
            return "weekly"
        return "daily"  # less then 7

    def bkp_file(self, rate: str | None = None, hours: bool = False) -> str:
        time_format = "%Y:%m:%d"
        if hours:
            time_format = "%Y:%m:%d-%H:%M:%S"
        if not rate:
            rate = self._rate
        return f"{self.BACKUP_DIR}/{self.PROJECT_NAME}-{rate}-{datetime.now().strftime(time_format)}.tar.gz"


class Backup:
    """ """
    def __init__(self, config_file: str):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                self.config = Config(**json.load(f))
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)

    def create_backups(self):
        """
        https://stackoverflow.com/questions/45621476/python-tarfile-slow-than-linux-command
        In the case backup is runned hourly, do not recreate daily, weekly, monthly, and yearly.
        In effect this part is running just onnce a day.
        Skip tar creation and compresion if eg. daily backup was created in less then 6 minutes (360 sec).
        Just cp previous one, to avoid unnecesery load.
        """

        def _tar(bkp_file: str) -> None:
            subprocess.call(["tar", "cvf", bkp_file, self.config.SRC_DIR])

        if not Path(self.config.bkp_file()).exists():
            print(f"Creating:\t{self.config.bkp_file}")
            _tar(self.config.bkp_file())
        if self.config.BACKUP_RETENTION_HOURLY > 0:
            _bkp_file_hourly = self.config.bkp_file(hours=True, rate="hourly")
            print(f"Creating:\t{_bkp_file_hourly}")
            if (
                datetime.now().timestamp()
                - Path(self.config.bkp_file()).stat().st_ctime
            ) < 360:
                _src = Path(self.config.bkp_file())
                _dest = Path(_bkp_file_hourly)
                _dest.write_bytes(_src.read_bytes())
            if not Path(_bkp_file_hourly).exists():
                _tar(_bkp_file_hourly)

    def rotate_backups(self):
        print("Rotating old backups:")
        old_backups: list[Path] = []
        for rate in ("hourly", "daily", "weekly", "monthly"):
            _all: list[Path] = [
                bkp
                for bkp in Path(self.config.BACKUP_DIR).glob(
                    f"*{self.config.PROJECT_NAME}*"
                )
                if bkp.match(f"*{rate}*")
            ]
            _all.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            _retention: int = getattr(self.config, f"BACKUP_RETENTION_{rate.upper()}") 
            old_backups.extend(_all[_retention:])

        for ob in old_backups:
            print(f"Deleting:\t{str(ob)}")
            ob.unlink()


if __name__ == "__main__":
    backup = Backup(config_file="config.json")
    backup.create_backups()
    backup.rotate_backups()
