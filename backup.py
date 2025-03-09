#!/usr/bin/env python3
"""

"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class Config:
    def __init__(self, config_file: str):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                json_config = json.load(f)
                self.src_dir: str = json_config["SRC_DIR"]
                self.backup_dir: str = json_config["BACKUP_DIR"]
                self.project_name: str = json_config["PROJECT_NAME"]
                self.backup_retention_hourly: int = json_config[
                    "BACKUP_RETENTION_HOURLY"
                ]
                self.backup_retention_daily: int = json_config["BACKUP_RETENTION_DAILY"]
                self.backup_retention_weekly: int = json_config[
                    "BACKUP_RETENTION_WEEKLY"
                ]
                self.backup_retention_monthly: int = json_config[
                    "BACKUP_RETENTION_MONTHLY"
                ]
                self.backup_retention_yearly: int = json_config[
                    "BACKUP_RETENTION_YEARLY"
                ]
        except FileNotFoundError as e:
            print(e)
            sys.exit(1)

    @property
    def _rate(self) -> str:
        # fmt: off
        if datetime.now().timetuple().tm_yday == 1 and self.backup_retention_yearly > 0:
            return "yearly"
        if datetime.now().timetuple().tm_mday == 1 and self.backup_retention_monthly > 0:
            return "monthly"
        if (datetime.now().timetuple().tm_wday + 1) == 7 and self.backup_retention_weekly > 0:
            return "weekly"
        # fmt: on
        return "daily"  # less then 7

    def bkp_file(self, rate: str | None = None, hours: bool = False) -> str:
        time_format = "%Y:%m:%d"
        if hours:
            time_format = "%Y:%m:%d-%H:%M:%S"
        if not rate:
            rate = self._rate
        return f"{self.backup_dir}/{self.project_name}-{rate}-{datetime.now().strftime(time_format)}.tar.gz"


class Backup:
    """ """

    def __init__(self, config_file: str):
        self.config: Config = Config(config_file)

    def create_backups(self):
        """
        https://stackoverflow.com/questions/45621476/python-tarfile-slow-than-linux-command
        In the case backup is runned hourly, do not recreate daily, weekly, monthly, and yearly.
        In effect this part is running just onnce a day.
        Skip tar creation and compresion if eg. daily backup was created in less then 6 minutes (360 sec).
        Just cp previous one, to avoid unnecesery load.
        """
        print("Creating:")

        def _backup(bkp_file: str) -> None:
            subprocess.call(["tar", "czf", bkp_file, self.config.src_dir])

        if not Path(self.config.bkp_file()).exists():
            print(f"\t{self.config.bkp_file}")
            _backup(self.config.bkp_file())
        if self.config.backup_retention_hourly > 0:
            _bkp_file_hourly = self.config.bkp_file(hours=True, rate="hourly")
            print(f"\t{_bkp_file_hourly}")
            # fmt: off
            if (datetime.now().timestamp() - Path(self.config.bkp_file()).stat().st_ctime) < 360:
                # fmt: on
                _src = Path(self.config.bkp_file())
                _dest = Path(_bkp_file_hourly)
                _dest.write_bytes(_src.read_bytes())
            if not Path(_bkp_file_hourly).exists():
                _backup(_bkp_file_hourly)

    def rotate_backups(self):
        print("Rotating (deleting) old backups:")
        old_backups: list[Path] = []
        for rate in ("hourly", "daily", "weekly", "monthly", "yearly"):
            _all: list[Path] = [
                bkp
                for bkp in Path(self.config.backup_dir).glob(
                    f"*{self.config.project_name}*"
                )
                if bkp.match(f"*{rate}*")
            ]
            _all.sort(key=lambda x: x.stat().st_ctime, reverse=True)
            _retention: int = getattr(self.config, f"backup_retention_{rate}")
            old_backups.extend(_all[_retention:])

        for ob in old_backups:
            print(f"\t{str(ob)}")
            ob.unlink()


if __name__ == "__main__":
    backup = Backup(config_file="config.json")
    backup.create_backups()
    backup.rotate_backups()
