param(
  [string]$ResourceGroup = "rg-datalake-ficp",
  [string]$StorageAccountName,
  [string]$FileSystem = "ficp",
  [string]$LocalRoot = "ficp_data_lake"
)

Write-Host "== UPLOAD FICP DATA =="
if (-not (Test-Path $LocalRoot)) { Write-Host "Local root not found: $LocalRoot" -ForegroundColor Red; exit 1 }
if (-not $StorageAccountName) { Write-Host "Provide -StorageAccountName" -ForegroundColor Yellow; exit 1 }

# Ensure az logged in
az account show > $null 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "Please run: az login" -ForegroundColor Yellow; exit 1 }

# Get key
$key = az storage account keys list -g $ResourceGroup -n $StorageAccountName --query "[0].value" -o tsv
if (-not $key) { Write-Host "Cannot get key" -ForegroundColor Red; exit 1 }

# Ensure filesystem exists (ignore already exists)
try {
  az storage fs create -n $FileSystem --account-name $StorageAccountName --account-key $key --only-show-errors | Out-Null
} catch {
  Write-Host "Filesystem check: $FileSystem (exists or created)" -ForegroundColor DarkGray
}

# Upload recursively using blob batch (compatible with ADLS Gen2), overwrite to be idempotent
Write-Host "Uploading directory recursively (blob batch)..."
az storage blob upload-batch `
  --account-name $StorageAccountName `
  --account-key $key `
  --destination $FileSystem `
  --source $LocalRoot `
  --overwrite `
  --no-progress `
  --only-show-errors
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "OK - Data uploaded" -ForegroundColor Green
