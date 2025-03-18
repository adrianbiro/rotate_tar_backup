#!/bin/bash
# shellcheck disable=CS2010
SRC_DIR="/srv/gits"
BACKUP_DIR="/srv/backups"
PROJECT_NAME="gits"

BACKUP_RETENTION_HOURLY=12
BACKUP_RETENTION_DAILY=6
BACKUP_RETENTION_WEEKLY=3
BACKUP_RETENTION_MONTHLY=3
BACKUP_RETENTION_YEARLY=0

DAYYEAR="$(date +%j)"
DAYMONTH="$(date +%d)"
DAYWEEK="$(date +%u)"

# force base-10 interpretation by 10#$variable, since $date +%d will return zero padded number
[[ (10#$DAYYEAR -eq 1) && ($BACKUP_RETENTION_YEARLY -gt 0) ]] && RATE='yearly'
[[ (10#$DAYMONTH -eq 1) && (-z $RATE) && ($BACKUP_RETENTION_MONTHLY -gt 0) ]] && RATE='monthly'
[[ (10#$DAYWEEK -eq 7) && (-z $RATE) && ($BACKUP_RETENTION_WEEKLY -gt 0) ]] && RATE='weekly'
[[ (10#$DAYWEEK -lt 7) && (-z $RATE) ]] && RATE='daily'

DATE=$RATE-"$(date +"%Y:%m:%d")"
: <<'END_COMMENT'
Example $BACKUP_DIR structure:
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
    gits-yearly-2025:01:01.tar.gz # doubles as monthly
END_COMMENT
BKP_FILE="${BACKUP_DIR}/${PROJECT_NAME}-${DATE}.tar.gz"

function backup() {
    : <<'END_COMMENT'
In the case backup is runned hourly, do not recreate daily, weekly, monthly, and yearly.
In effect this part is running just onnce a day.
END_COMMENT
    [[ -f "${BKP_FILE}" ]] || {
        echo -e "Creating:\t${BKP_FILE}"
        tar czf "${BKP_FILE}" "${SRC_DIR}"
    }
    : <<'END_COMMENT'
Hourly backup
Skip tar creation and compresion if eg. daily backup was created in less then 6 minutes (360 sec). 
Just cp previous one, to avoid unnecesery load.
END_COMMENT
    [[ ($BACKUP_RETENTION_HOURLY -gt 0) ]] && {
        BKP_FILE_hourly="${BACKUP_DIR}/${PROJECT_NAME}-hourly-$(date +"%Y:%m:%d-%X").tar.gz"
        echo -e "Creating:\t${BKP_FILE_hourly}"
        [[ $(("$(date +'%s')" - "$(stat -c '%W' ${BKP_FILE})")) -lt 360 ]] && cp "${BKP_FILE}" "${BKP_FILE_hourly}"
        [[ -f "${BKP_FILE_hourly}" ]] || tar czf "${BKP_FILE_hourly}" "${SRC_DIR}"
    }
}

function rotate_backups() {
    cd "${BACKUP_DIR}" || {
        echo "${BACKUP_DIR}: does not exists"
        exit 1
    }
    echo "Rotating old backups"
    ls -t | grep "${PROJECT_NAME}" | grep "hourly" | sed -e 1,"$BACKUP_RETENTION_HOURLY"d | xargs -d '\n' rm -vR 2>/dev/null
    ls -t | grep "${PROJECT_NAME}" | grep "daily" | sed -e 1,"$BACKUP_RETENTION_DAILY"d | xargs -d '\n' rm -vR 2>/dev/null
    ls -t | grep "${PROJECT_NAME}" | grep "weekly" | sed -e 1,"$BACKUP_RETENTION_WEEKLY"d | xargs -d '\n' rm -vR 2>/dev/null
    ls -t | grep "${PROJECT_NAME}" | grep "monthly" | sed -e 1,"$BACKUP_RETENTION_MONTHLY"d | xargs -d '\n' rm -vR 2>/dev/null
    ls -t | grep "${PROJECT_NAME}" | grep yearly | sed -e 1,"$BACKUP_RETENTION_YEARLY"d | xargs -d '\n' rm -vR 2>/dev/null
}

backup
rotate_backups
exit 0