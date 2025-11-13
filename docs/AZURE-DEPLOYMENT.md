# Azure deployment - ADLS Gen2 for FICP lake

This guide deploys an Azure Storage Account (ADLS Gen2) in an existing resource group and uploads the generated CSV files.

Prerequisites:
- Azure CLI installed and logged in: `az login`
- Existing resource group name: `rg-datalake-ficp`
- Generated local data under `ficp_data_lake/` (run `python scripts/generate_ficp_data.py`)

## 1) Deploy storage account (HNS=true)
PowerShell:
```
# From repo root
powershell -ExecutionPolicy Bypass -File scripts\azure\deploy_storage.ps1 -ResourceGroup rg-datalake-ficp -StorageAccountName stficpdata123456
```
Notes:
- Storage account name must be globally unique and lowercase alphanumeric (3-24 chars).
- Script auto-detects resource group location.

## 2) Upload data recursively
```
powershell -ExecutionPolicy Bypass -File scripts\azure\upload_ficp_data.ps1 -ResourceGroup rg-datalake-ficp -StorageAccountName stficpdata123456 -FileSystem ficp -LocalRoot ficp_data_lake
```
This creates a filesystem `ficp` and uploads the folder tree under `/`.

## 2-bis) Daily generation and upload (incremental)
Generate and push only one day's files (three CSVs) to the ADLS Gen2 container:
```
powershell -ExecutionPolicy Bypass -File scripts\azure\run_daily_upload.ps1 -ResourceGroup rg-datalake-ficp -StorageAccountName stficpdata123456 -FileSystem ficp -Date (Get-Date -Format 'yyyy-MM-dd') -Overwrite
```
Notes:
- The daily generator computes scheduled inscriptions/radiations deterministically from existing history, ensuring business rules and idempotence.
- Use `-Overwrite` to safely re-run the same day.

Optional: Schedule on Windows Task Scheduler (example 06:30 daily):
```
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PWD\scripts\azure\run_daily_upload.ps1`" -ResourceGroup rg-datalake-ficp -StorageAccountName stficpdata123456 -FileSystem ficp -Date (Get-Date -Format 'yyyy-MM-dd') -Overwrite"
$trigger = New-ScheduledTaskTrigger -Daily -At 6:30am
Register-ScheduledTask -TaskName "FICP-Daily-Upload" -Action $action -Trigger $trigger -Description "Generate and upload daily FICP files"
```

## 3) Cleanup (optional)
```
powershell -ExecutionPolicy Bypass -File scripts\azure\cleanup_storage.ps1 -ResourceGroup rg-datalake-ficp -StorageAccountName stficpdata123456 -FileSystem ficp
```
This deletes the filesystem (container) and all uploaded files.

## 4) Azure Function (daily generation on Azure)
The repo includes a Python Azure Function (Timer trigger) that generates the 3 CSVs daily and writes directly to your ADLS Gen2 container using managed identity.

Deploy it with:
```
powershell -ExecutionPolicy Bypass -File scripts\azure\deploy_ficp_daily_function.ps1 -ResourceGroup rg-datalake-ficp -Location francecentral -FunctionAppName ficp-daily-func-<random> -DataLakeStorageAccountName stficpdata123456 -ContainerName ficp
```
Notes:
- Schedule is 06:30 daily (Romance Standard Time). Change in `azure_function_ficp_daily/ficp_daily/function.json` if needed.
- App settings: TARGET_STORAGE_ACCOUNT, TARGET_CONTAINER, and WEBSITE_TIME_ZONE are set by the script.
- Code lives under `azure_function_ficp_daily/` with `requirements.txt`. Zip deploy is used; the platform installs deps automatically.

## Mapping to requirements
- ADLS Gen2 with hierarchical namespace -> Data lake
- Folder structure preserved -> consultation/inscription/radiation by date
- Ready for Power BI via Azure Storage connector or Synapse/SQL external tables (optional)
