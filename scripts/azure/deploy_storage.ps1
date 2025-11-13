param(
  [string]$ResourceGroup = "rg-datalake-ficp",
  [string]$StorageAccountName = "stficpdata$(Get-Random -Maximum 999999)",
  [string]$Location = "francecentral",
  [string]$FileSystem = "ficp"
)

# Deploy ADLS Gen2 storage account and filesystem
Write-Host "== DEPLOY ADLS GEN2 =="
Write-Host "ResourceGroup: $ResourceGroup"
Write-Host "StorageAccount: $StorageAccountName"
Write-Host "Location: $Location"
Write-Host "FileSystem: $FileSystem"

# Ensure az is logged in
az account show > $null 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "Please run: az login" -ForegroundColor Yellow
  exit 1
}

# Get RG location if exists
$rg = az group show -n $ResourceGroup --only-show-errors | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $rg) {
  Write-Host "Resource group not found: $ResourceGroup" -ForegroundColor Red
  exit 1
}
$Location = $rg.location

# Create storage account (HNS=true)
az storage account create `
  -g $ResourceGroup `
  -n $StorageAccountName `
  -l $Location `
  --sku Standard_LRS `
  --kind StorageV2 `
  --https-only true `
  --hns true `
  --min-tls-version TLS1_2 `
  --allow-shared-key-access true `
  --only-show-errors
if ($LASTEXITCODE -ne 0) { exit 1 }

# Get key
$key = az storage account keys list -g $ResourceGroup -n $StorageAccountName --query "[0].value" -o tsv
if (-not $key) { Write-Host "Cannot retrieve storage key" -ForegroundColor Red; exit 1 }

# Create filesystem (container)
az storage fs create -n $FileSystem --account-name $StorageAccountName --account-key $key --only-show-errors | Out-Null
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "OK - Storage deployed" -ForegroundColor Green
Write-Host "Account: $StorageAccountName" -ForegroundColor Green
