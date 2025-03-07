# rotate_tar_backup

Rotate tar backup: daily, weekly, monthly, yearly, and hourly.

<https://www.freedesktop.org/software/systemd/man/latest/systemd.time.html#>
<https://documentation.suse.com/smart/systems-management/html/systemd-working-with-timers/index.html>

```bash
systemd-analyze verify gitsBackup.*
sudo systemctl edit --force --full  gitsBackup.timer
sudo systemctl edit --force --full  gitsBackup.service
sudo systemctl daemon-reload 
sudo systemctl enable --now gitsBackup.service
sudo systemctl enable --now gitsBackup.timer
systemctl status gitsBackup
```

Inspiration from forked gist <https://gist.github.com/adrianbiro/22fa0362fe1a510eb00fe11dced759d4>