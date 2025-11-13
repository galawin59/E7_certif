param(
  [string]$ResourceGroup = "rg-datalake-ficp",
  [string]$Location = "francecentral",
  [string]$FunctionAppName = "ficp-daily-func-$(Get-Random)",
  [string]$DataLakeStorageAccountName,
  [string]$ContainerName = "ficp"
)

Write-Host "== DEPLOY FICP DAILY FUNCTION ==" -ForegroundColor Cyan
if (-not $DataLakeStorageAccountName) { Write-Error "Provide -DataLakeStorageAccountName"; exit 1 }

$ErrorActionPreference = 'Stop'

# Ensure az login
az account show > $null 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "Please run: az login" -ForegroundColor Yellow; exit 1 }

# 1) Ensure providers are registered
az provider register -n Microsoft.Web --wait --only-show-errors | Out-Null

# 2) Storage for the Function App (separate from data lake)
$funcStorage = ("stfuncficp" + (Get-Random -Maximum 999999)).ToLower()
az storage account create -g $ResourceGroup -n $funcStorage -l $Location --sku Standard_LRS --kind StorageV2 --only-show-errors | Out-Null

# 3) Create consumption plan Function App (Python)
az functionapp create `
  --name $FunctionAppName `
  --resource-group $ResourceGroup `
  --consumption-plan-location $Location `
  --os-type Linux `
  --runtime python `
  --runtime-version 3.11 `
  --functions-version 4 `
  --storage-account $funcStorage `
  --only-show-errors | Out-Null

# 4) Enable managed identity
az functionapp identity assign -g $ResourceGroup -n $FunctionAppName --only-show-errors | Out-Null

# 5) Grant MI access to the data lake container
$principalId = az functionapp identity show -g $ResourceGroup -n $FunctionAppName --query principalId -o tsv
az role assignment create `
  --assignee $principalId `
  --role "Storage Blob Data Contributor" `
  --scope "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$ResourceGroup/providers/Microsoft.Storage/storageAccounts/$DataLakeStorageAccountName" `
  --only-show-errors | Out-Null

# 6) App settings
az functionapp config appsettings set -g $ResourceGroup -n $FunctionAppName --settings `
  TARGET_STORAGE_ACCOUNT=$DataLakeStorageAccountName `
  TARGET_CONTAINER=$ContainerName `
  WEBSITE_TIME_ZONE="Romance Standard Time" `
  --only-show-errors | Out-Null

# 7) Zip and deploy
$src = Resolve-Path "azure_function_ficp_daily"
$zipPath = Join-Path $env:TEMP "ficp_daily_func.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $src '*') -DestinationPath $zipPath -Force
az functionapp deployment source config-zip -g $ResourceGroup -n $FunctionAppName --src $zipPath --only-show-errors | Out-Null

Write-Host "OK - Function deployed: $FunctionAppName" -ForegroundColor Green
Write-Host "It will run daily at 06:30 (Romance Standard Time)."
Write-Host "App URL: https://$FunctionAppName.azurewebsites.net"
