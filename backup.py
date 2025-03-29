#!/usr/bin/env python3
""" """
import json
import logging
import shutil
import subprocess
import sys
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from subprocess import CalledProcessError
from typing import Union


class Config:
    def __init__(self, config_file: str):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                json_config: dict = json.load(f)
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
                self._backup_type_tar: bool = json_config["BACKUP_TYPE_TAR"]
                self._backup_type_rsync: bool = json_config["BACKUP_TYPE_RSYNC"]
                self.rsync_cmd: list[str] = json_config["RSYNC_CMD"]
                self.tar_cmd: list[str] = json_config["TAR_CMD"]
                self.backup_type: str = self._get_backup_type()
                self._backup_location_extension: str = json_config.setdefault(
                    "BACKUP_LOCATION_EXTENSION", ""
                )

        except (FileNotFoundError, JSONDecodeError) as e:
            logging.error("Invalid %s:\t%s", config_file, e, exc_info=False)
            sys.exit(1)
        logging.debug("%s: %s", self.__class__, self.__dict__)

    def _get_backup_type(self):
        backup_types_list: list[bool] = [
            v for k, v in self.__dict__.items() if k.startswith("_backup_type_")
        ]
        backup_types_dict: dict[str, bool] = {
            k: v for k, v in self.__dict__.items() if k.startswith("_backup_type_")
        }
        logging.debug("%s", f"{backup_types_list=} {backup_types_dict=}")
        if not any(backup_types_list) or backup_types_list.count(True) != 1:
            logging.error(
                "Enable exaclty one backup type. Current setting: %s",
                backup_types_dict,
            )
            sys.exit(1)
        return [k for k, v in backup_types_dict.items() if v][0]

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
        return "daily"  # less then 7, will return even if disabled, handle with is_daly_rate_enabled

    def is_daily_rate_enabled(self) -> bool:
        """_rate will default to daily, this will ensure that daly backup is not runned if not explicitelly enabled"""
        return self.backup_retention_daily > 0

    def bkp_location(self, rate: Union[str, None] = None, hours: bool = False) -> str:
        """Union[str, None] for pre python3.10 compability, 'str | None'"""
        time_format = "%Y:%m:%d"
        if hours:
            time_format = "%Y:%m:%d-%H:%M:%S"
        if not rate:
            rate = self._rate
        return f"{self.backup_dir}/{self.project_name}-{rate}-{datetime.now().strftime(time_format)}{self._backup_location_extension}"


class Backup:
    """ """

    def __init__(self, config_file: str):
        self.config: Config = Config(config_file)

    def create_backups(self):
        """
        https://stackoverflow.com/questions/45621476/python-tarfile-slow-than-linux-command
        In the case backup is runned hourly, do not recreate daily, weekly, monthly, and yearly.
        In effect this part is running just onnce a day.
        Skip backup (relevant for tar.gz) creation and compresion if eg. daily backup was created in less then 6 minutes (360 sec).
        Just cp previous one, to avoid unnecesery load.
        """
        backup_created = False
        logging.info("Creating:")

        def _backup(bkp_location: str) -> None:
            """valid methodes are defined in Config object"""
            bkp_methods: dict[str, list] = {
                "_backup_type_tar": self.config.tar_cmd
                + [bkp_location, self.config.src_dir],
                "_backup_type_rsync": self.config.rsync_cmd
                + [
                    self.config.src_dir,
                    bkp_location,
                ],
            }
            if not shutil.which(executable := bkp_methods[self.config.backup_type][0]):
                logging.error("Command not found: %s", executable)
                sys.exit(1)
            try:
                logging.info("\t%s", " ".join(bkp_methods[self.config.backup_type]))
                result = subprocess.run(
                    bkp_methods[self.config.backup_type],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                logging.debug("%s", f"{executable=} {result.stdout=}")
            except CalledProcessError as e:
                logging.error(e)
                sys.exit(1)
            nonlocal backup_created
            backup_created = True

        _bkp_location = Path(self.config.bkp_location())
        if not _bkp_location.exists() and self.config.is_daily_rate_enabled():
            _backup(self.config.bkp_location())
        elif self.config.is_daily_rate_enabled():
            logging.info("\tSkipping: %s, alredy exists.", self.config.bkp_location())
        # hourly backup section
        if self.config.backup_retention_hourly > 0:
            _bkp_file_hourly = self.config.bkp_location(hours=True, rate="hourly")
            # fmt: off
            if (_bkp_location.exists() and datetime.now().timestamp() - _bkp_location.stat().st_ctime) < 360:
                # fmt: on
                if _bkp_location.is_dir():
                    shutil.copytree(src=self.config.bkp_location(), dst=_bkp_file_hourly)
                if _bkp_location.is_file():
                    shutil.copy(src=self.config.bkp_location(), dst=_bkp_file_hourly)
                
            if not Path(_bkp_file_hourly).exists():
                _backup(_bkp_file_hourly)
        if not backup_created:
            logging.info("\tSkipping backup creation, no aplicable backup rate enabled at this moment.")

    def rotate_backups(self):
        logging.info("Rotating (deleting) old backups:")
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
            logging.debug(
                "%s", f"{rate=} {_all=} {_retention=} To delete: {_all[_retention:]}"
            )

        logging.debug("All old backups to dete: %s", old_backups)
        for ob in old_backups:
            logging.info("\t%s", str(ob))
            try:
                ob.unlink()
            except IsADirectoryError:
                shutil.rmtree(ob)
        if not old_backups:
            logging.info("\tNo old backups qualified for rotation found.")


def main():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        style="%",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO,
    )
    backup = Backup(config_file="config.json")
    backup.create_backups()
    backup.rotate_backups()


if __name__ == "__main__":
    raise SystemExit(main())
