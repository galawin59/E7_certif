<#
Pure az CLI provisioning for daily FICP runbook execution at 06:30 (Europe/Paris).
Idempotent and non-interactive. Uses az REST to upload runbook content and create job schedule with parameters.
Prerequisites:
  - az CLI logged in: az login
  - Resource group exists (default: rg-datalake-ficp)
  - File scripts/automation/runbook_ficp_daily_azure.ps1 present in repo
Creates:
  1. Automation Account (if missing) with SystemAssigned identity
  2. Role assignment Storage Blob Data Contributor on the Storage Account
  3. Runbook (PowerShell) imported from local file and published
  4. Daily schedule starting tomorrow 06:30 CET
  5. JobSchedule linking runbook+schedule with parameters
#>
param(
  [string]$ResourceGroup='rg-datalake-ficp',
  [string]$PreferredLocation='northeurope',
  [string]$AutomationAccountName='aa-ficp-daily',
  [string]$RunbookName='ficp-daily',
  [string]$ScheduleName='ficp-daily-0630',
  [string]$RunbookPath='scripts/automation/runbook_ficp_daily_azure.ps1',
  [string]$TimeZone='Central European Standard Time',
  [string]$StorageAccountName='stficpdata330940',
  [string]$ContainerName='ficp'
)

$ErrorActionPreference = 'Stop'

function Ensure-Success($Message) { if ($LASTEXITCODE -ne 0) { throw "FAILED: $Message (exit $LASTEXITCODE)" } }

$allowedLocations = @('eastus','eastus2','westus','northeurope','southeastasia','japanwest')

Write-Host "[0] Register provider Microsoft.Automation" -ForegroundColor Cyan
az provider register --namespace Microsoft.Automation --wait | Out-Null

Write-Host "[1] Automation Account" -ForegroundColor Cyan
$acct = az automation account show --resource-group $ResourceGroup --name $AutomationAccountName 2>$null
if (-not $acct) {
  $locationToUse = $PreferredLocation
  $created = $false
  foreach ($loc in @($locationToUse) + ($allowedLocations | Where-Object { $_ -ne $locationToUse })) {
    try {
      az automation account create --resource-group $ResourceGroup --name $AutomationAccountName --location $loc --sku Free | Out-Null
      Ensure-Success "Create Automation Account in $loc"
      Write-Host "Created in $loc." -ForegroundColor Green
      $created = $true; break
    } catch {
      Write-Host "Create in $loc failed, trying next allowed region..." -ForegroundColor Yellow
    }
  }
  if (-not $created) { throw 'Unable to create Automation Account in allowed regions.' }
} else { Write-Host 'Exists.' }

Write-Host "[1b] Managed Identity & Role" -ForegroundColor Cyan
$acctId = "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$ResourceGroup/providers/Microsoft.Automation/automationAccounts/$AutomationAccountName"
az resource update --ids $acctId --set identity.type=SystemAssigned | Out-Null
$principalId = az automation account show --resource-group $ResourceGroup --name $AutomationAccountName --query identity.principalId -o tsv
if (-not $principalId) { throw 'Unable to retrieve principalId after identity assignment' }
$scope = "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$ResourceGroup/providers/Microsoft.Storage/storageAccounts/$StorageAccountName"
$existingRole = az role assignment list --assignee $principalId --scope $scope --query "[?roleDefinitionName=='Storage Blob Data Contributor']" -o tsv 2>$null
if (-not $existingRole) {
  az role assignment create --assignee $principalId --role "Storage Blob Data Contributor" --scope $scope | Out-Null
  Ensure-Success 'Role assignment Storage Blob Data Contributor'
  Write-Host 'Role assigned.' -ForegroundColor Green
} else { Write-Host 'Role already assigned.' }

Write-Host "[2] Runbook import" -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $RunbookPath)) { throw "Runbook file not found: $RunbookPath" }
$rb = az automation runbook show --resource-group $ResourceGroup --automation-account-name $AutomationAccountName --name $RunbookName 2>$null
if (-not $rb) {
  # Create metadata container
  az automation runbook create --automation-account-name $AutomationAccountName --resource-group $ResourceGroup --name $RunbookName --type PowerShell --location $(az automation account show -g $ResourceGroup -n $AutomationAccountName --query location -o tsv) | Out-Null
}

# Upload content to draft via REST to avoid CLI length limits
$subId = az account show --query id -o tsv
$draftUrl = "https://management.azure.com/subscriptions/$subId/resourceGroups/$ResourceGroup/providers/Microsoft.Automation/automationAccounts/$AutomationAccountName/runbooks/$RunbookName/draft/content?api-version=2023-11-01"
az rest --method put --url $draftUrl --headers "Content-Type=text/plain" --body @"$RunbookPath" | Out-Null

# Publish the runbook
az automation runbook publish --automation-account-name $AutomationAccountName --resource-group $ResourceGroup --name $RunbookName | Out-Null

Write-Host "[3] Schedule" -ForegroundColor Cyan
$tomorrow = (Get-Date).Date.AddDays(1).AddHours(6).AddMinutes(30)
$startIso = $tomorrow.ToString('yyyy-MM-ddTHH:mm:ss')
$sch = az automation schedule show --automation-account-name $AutomationAccountName --resource-group $ResourceGroup --name $ScheduleName 2>$null
if (-not $sch) {
  az automation schedule create --automation-account-name $AutomationAccountName --resource-group $ResourceGroup --name $ScheduleName --start-time $startIso --frequency Day --interval 1 --time-zone "$TimeZone" | Out-Null
  Write-Host "Schedule created starting $startIso." -ForegroundColor Green
} else { Write-Host 'Schedule exists.' }

Write-Host "[4] Link runbook to schedule (JobSchedule)" -ForegroundColor Cyan
$jobListUrl = "https://management.azure.com/subscriptions/$subId/resourceGroups/$ResourceGroup/providers/Microsoft.Automation/automationAccounts/$AutomationAccountName/jobSchedules?api-version=2023-11-01"
$jobList = az rest --method get --url $jobListUrl --query "value[?properties.runbook.name=='$RunbookName' && properties.schedule.name=='$ScheduleName']" -o tsv 2>$null
if (-not $jobList) {
  $jobId = ([guid]::NewGuid()).ToString()
  $jobUrl = "https://management.azure.com/subscriptions/$subId/resourceGroups/$ResourceGroup/providers/Microsoft.Automation/automationAccounts/$AutomationAccountName/jobSchedules/$jobId?api-version=2023-11-01"
  $tmp = New-TemporaryFile
  @{
    properties = @{ 
      runbook   = @{ name = $RunbookName }
      schedule  = @{ name = $ScheduleName }
      parameters = @{ StorageAccountName = $StorageAccountName; ContainerName = $ContainerName }
    }
  } | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $tmp -Encoding UTF8
  az rest --method put --url $jobUrl --headers "Content-Type=application/json" --body @$tmp | Out-Null
  Remove-Item $tmp -Force
  Write-Host "Linked." -ForegroundColor Green
} else { Write-Host 'Already linked.' }

Write-Host "[DONE] Provisioning complete. Next run tomorrow 06:30." -ForegroundColor Green
Write-Host "Check jobs: az automation job list --automation-account-name $AutomationAccountName --resource-group $ResourceGroup"