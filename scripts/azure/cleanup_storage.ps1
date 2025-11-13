param(
  [string]$ResourceGroup = "rg-datalake-ficp",
  [string]$StorageAccountName,
  [string]$FileSystem = "ficp"
)

Write-Host "== CLEANUP STORAGE =="
if (-not $StorageAccountName) { Write-Host "Provide -StorageAccountName" -ForegroundColor Yellow; exit 1 }

az account show > $null 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "Please run: az login" -ForegroundColor Yellow; exit 1 }

$key = az storage account keys list -g $ResourceGroup -n $StorageAccountName --query "[0].value" -o tsv
if (-not $key) { Write-Host "Cannot get key" -ForegroundColor Red; exit 1 }

# Remove filesystem (container) to clean all data
az storage fs delete -n $FileSystem --yes --account-name $StorageAccountName --account-key $key --only-show-errors
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "OK - FileSystem deleted" -ForegroundColor Green
