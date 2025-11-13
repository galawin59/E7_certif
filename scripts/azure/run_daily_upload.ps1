param(
  [string]$ResourceGroup = "rg-datalake-ficp",
  [string]$StorageAccountName,
  [string]$FileSystem = "ficp",
  [string]$Date = (Get-Date -Format 'yyyy-MM-dd'),
  [switch]$Overwrite
)

Write-Host "== DAILY GENERATE + UPLOAD ==" -ForegroundColor Cyan
if (-not $StorageAccountName) { Write-Error "Provide -StorageAccountName"; exit 1 }

# 1) Generate today's files
$py = "$(Resolve-Path ./\.venv/Scripts/python.exe)"
& $py scripts/generate_ficp_daily.py --date $Date $(if ($Overwrite) {"--overwrite"} else {""})
if ($LASTEXITCODE -ne 0) { Write-Error "Daily generation failed"; exit 1 }

# 2) Get account key
az account show > $null 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "Please run: az login" -ForegroundColor Yellow; exit 1 }
$key = az storage account keys list -g $ResourceGroup -n $StorageAccountName --query "[0].value" -o tsv
if (-not $key) { Write-Error "Cannot get storage key"; exit 1 }

# 3) Upload only the 3 files for the day (overwrite=true for idempotence)
$base = "ficp_data_lake"
$paths = @(
  "consultation/$Date.csv",
  "inscription/$Date.csv",
  "radiation/$Date.csv"
)

foreach ($rel in $paths) {
  $src = Join-Path $base $rel
  if (-not (Test-Path $src)) { Write-Warning "Missing local file: $src"; continue }
  az storage blob upload `
    --account-name $StorageAccountName `
    --account-key $key `
    --container-name $FileSystem `
    --file $src `
    --name $rel `
    --overwrite `
    --only-show-errors
  if ($LASTEXITCODE -ne 0) { Write-Error "Upload failed for $rel"; exit 1 }
}

Write-Host "OK - Daily $Date generated and uploaded" -ForegroundColor Green
