# FICP Daily Azure Function

Python Azure Function (Timer trigger) that generates daily FICP CSV files and uploads them to ADLS Gen2 (Blob API) in the target storage account.

Environment settings (App Settings):
- TARGET_STORAGE_ACCOUNT: name of the ADLS Gen2 account (e.g., stficpdata330940)
- TARGET_CONTAINER: container/filesystem name (default: ficp)
- WEBSITE_TIME_ZONE: "Romance Standard Time" to run at 06:30 local time

Schedule: NCRONTAB `0 30 6 * * *` (06:30 daily). If `WEBSITE_TIME_ZONE` is set, schedule uses that time zone.

Dependencies are in `requirements.txt` and will be installed by the Azure Functions platform.
