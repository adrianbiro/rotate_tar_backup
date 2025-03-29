# rotate_tar_or_rsync_backup

Rotate tar or rsync backup: daily, weekly, monthly, yearly, and hourly.

It is written for unix like systems with tar, and rsync installed.



## Deployemnt

### Script configuration

Change configuration variables in bash version script or `config.json` for python version.

#### bash version supports just tar

```bash
SRC_DIR="/srv/gits"
BACKUP_DIR="/srv/backups"
PROJECT_NAME="gits"
BACKUP_RETENTION_HOURLY=12
BACKUP_RETENTION_DAILY=6
BACKUP_RETENTION_WEEKLY=3
BACKUP_RETENTION_MONTHLY=3
BACKUP_RETENTION_YEARLY=0
```

* Set to propper path to interpreter `#!/usr/bin/env python3`

* Ensure that backup paths exists before you enable backup.

* Adjut unit files and ansible playbooks, it is intended for git server setup.

```bash
mkdir -p /srv/{gits,backups}
```

Use ansible playbook

## Systemd links

* <https://www.freedesktop.org/software/systemd/man/latest/systemd.time.html#>
* <https://documentation.suse.com/smart/systems-management/html/systemd-working-with-timers/index.html>
* <https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html>


### Systemd debugging

```bash
systemd-analyze verify gitsBackup.*
systemd-run --user --wait ./backup.sh
sudo systemctl edit --force --full  gitsBackup.timer
sudo systemctl edit --force --full  gitsBackup.service
sudo systemctl daemon-reload 
sudo systemctl enable --now gitsBackup.service
sudo systemctl enable --now gitsBackup.timer
systemctl status gitsBackup
```

## Backup structure

```txt
gits-hourly-2025:03:07-06:00:00.tar.gz 
... # hour increments in hourly retention range
gits-hourly-2025:03:07-17:00:00.tar.gz
gits-daily-2025:03:07.tar.gz
gits-daily-2025:03:06.tar.gz
gits-daily-2025:03:05.tar.gz
gits-daily-2025:03:04.tar.gz
gits-daily-2025:03:03.tar.gz
gits-weekly-2025:03:02.tar.gz # doubes as daily
gits-daily-2025:03:01.tar.gz  # in ocasion weekly doubles as daily, so you have temporarrly +1 daily retention period
gits-weekly-2025:02:23.tar.gz
gits-weekly-2025:02:16.tar.gz
gits-monthly-2025:03:01.tar.gz
gits-monthly-2025:02:01.tar.gz
gits-yearly-2025:01:01.tar.gz  # doubles as monthly
```

---

Inspiration for rotation from forked gist <https://gist.github.com/adrianbiro/22fa0362fe1a510eb00fe11dced759d4>
