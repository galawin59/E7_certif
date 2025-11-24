<#!
Runbook: FICP Daily Generation & Upload (Pure PowerShell)
Goal: Generate three CSV files (consultation, inscription, radiation) for a target date (default: today) using deterministic logic (hash based delays) and upload to the storage account container.
Assumptions:
- Az.Accounts & Az.Storage modules available.
- Storage account key provided (variable or parameter) for upload.
- Container already exists (ficp) else will be created.
#>
param(
    [string]$ResourceGroup = 'rg-datalake-ficp',
    [string]$StorageAccountName = 'stficpdata330940',
    [string]$ContainerName = 'ficp',
    [string]$TargetDate = $(Get-Date -Format 'yyyy-MM-dd'),
    [switch]$Overwrite,
    [switch]$SkipUpload
)

# Constants
$CONSULTATIONS_PAR_JOUR = 1000
$EVENEMENTS_PAR_JOUR = 300
$PART_SURDET = 0.30
$SURV_TO_INS_DMIN = 31; $SURV_TO_INS_DMAX = 37
$RAD_PROBA = 0.70
$RAD_DMIN = 18; $RAD_DMAX = 24

# Connect using managed identity when running inside Azure Automation (AUTOMATION_ACCOUNT_ID env set)
if ($env:AUTOMATION_ACCOUNT_ID) {
    try {
        Connect-AzAccount -Identity -ErrorAction Stop | Out-Null
    } catch {
        Write-Output "Managed identity connection failed: $_"
    }
}

function New-Key([System.Collections.Generic.HashSet[string]]$Existing) {
    $letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    $digits = '0123456789'
    while ($true) {
        $cle = -join ((1..8 | ForEach-Object { $letters[(Get-Random -Min 0 -Max $letters.Length)] }) + (1..5 | ForEach-Object { $digits[(Get-Random -Min 0 -Max $digits.Length)] }))
        if (-not $Existing.Contains($cle)) { $Existing.Add($cle) | Out-Null; return $cle }
    }
}

function Md5-Int([string]$s) {
    $md5 = [System.Security.Cryptography.MD5]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($s)
    $hash = $md5.ComputeHash($bytes)
    # Convert 16 bytes to big integer
    [System.Numerics.BigInteger]([byte[]]($hash + 0)) # append 0 to force positive
}

function Payment-Delay-Days([string]$cle) {
    $range = $SURV_TO_INS_DMAX - $SURV_TO_INS_DMIN + 1
    $val = (Md5-Int "pay:$cle") % $range
    return $SURV_TO_INS_DMIN + $val
}

function Radiation-Delay-Days([string]$cle) {
    $range = $RAD_DMAX - $RAD_DMIN + 1
    $val = (Md5-Int "radd:$cle") % $range
    return $RAD_DMIN + $val
}

function Will-Radiate([string]$cle) {
    $val = ((Md5-Int "radp:$cle") % 10000) / 10000.0
    return $val -lt $RAD_PROBA
}

# Directories (local temp)
# In Azure Automation, $PSScriptRoot can be empty. Use TEMP safely.
$Base = [System.IO.Path]::GetTempPath()
$DataRoot = Join-Path $Base 'ficp_data_lake'
$DirConsult = Join-Path $DataRoot 'consultation'
$DirInscr = Join-Path $DataRoot 'inscription'
$DirRad = Join-Path $DataRoot 'radiation'
New-Item -ItemType Directory -Path $DirConsult -Force | Out-Null
New-Item -ItemType Directory -Path $DirInscr -Force | Out-Null
New-Item -ItemType Directory -Path $DirRad -Force | Out-Null

# Parse date
try { $day = [DateTime]::ParseExact($TargetDate,'yyyy-MM-dd',$null) } catch { throw "Invalid date: $TargetDate" }
$dayStr = $day.ToString('yyyy-MM-dd')

$consultPath = Join-Path $DirConsult "$dayStr.csv"
$inscrPath = Join-Path $DirInscr "$dayStr.csv"
$radPath    = Join-Path $DirRad "$dayStr.csv"

# Point de départ pour mesurer la durée d'exécution globale
$__start = Get-Date

if (-not $Overwrite) {
    foreach ($p in @($consultPath,$inscrPath,$radPath)) { if (Test-Path $p) { Write-Output "EXISTS $p (use -Overwrite to regenerate)"; return }}
}

# Load history upto day (inscription CSVs)
$surveillances = @{} # cle -> list[DateTime]
$inscriptions = @{} # cle -> list of tuples (insc_dt,type_inc,surv_dt)
$known = [System.Collections.Generic.HashSet[string]]::new()

function Add-Surv([string]$cle,[DateTime]$d){ if (-not $surveillances[$cle]) { $surveillances[$cle] = New-Object System.Collections.Generic.List[DateTime] }; $surveillances[$cle].Add($d) }
function Add-Insc([string]$cle,[DateTime]$insc,[string]$type,$surv){
    if (-not $inscriptions[$cle]) { $inscriptions[$cle] = New-Object System.Collections.Generic.List[Object] }
    $inscriptions[$cle].Add([PSCustomObject]@{insc=$insc;type=$type;surv=$surv})
}

if (Test-Path $DirInscr) {
    Get-ChildItem -Path $DirInscr -Filter '*.csv' | ForEach-Object {
        $fdateStr = $_.Name.Substring(0,10)
        try { $fdate = [DateTime]::ParseExact($fdateStr,'yyyy-MM-dd',$null) } catch { return }
        if ($fdate -ge $day) { return }
        $lines = Get-Content -LiteralPath $_.FullName -Encoding UTF8
        if ($lines.Count -lt 2) { return }
        foreach ($line in $lines[1..($lines.Count-1)]) {
            $parts = $line -split ','
            if ($parts.Length -lt 5) { continue }
            $cle = $parts[0]; $statut=$parts[1]; $type_inc=$parts[2]; $d_surv=$parts[3]; $d_insc=$parts[4]
            $known.Add($cle) | Out-Null
            if ($statut -eq 'SURVEILLANCE' -and $d_surv) {
                Add-Surv $cle ([DateTime]::ParseExact($d_surv,'yyyy-MM-dd',$null))
            } elseif ($statut -eq 'INSCRIT' -and $d_insc) {
                $survDt = if ($d_surv) { [DateTime]::ParseExact($d_surv,'yyyy-MM-dd',$null) } else { $null }
                Add-Insc $cle ([DateTime]::ParseExact($d_insc,'yyyy-MM-dd',$null)) $type_inc $survDt
            }
        }
    }
}

# Consult history (optional) to extend known clients
if (Test-Path $DirConsult) {
    Get-ChildItem $DirConsult -Filter '*.csv' | ForEach-Object {
        $fdateStr = $_.Name.Substring(0,10)
        try { $fdate = [DateTime]::ParseExact($fdateStr,'yyyy-MM-dd',$null) } catch { return }
        if ($fdate -ge $day) { return }
        $lines = Get-Content $_.FullName -Encoding UTF8
        if ($lines.Count -lt 2) { return }
        $lines[1..($lines.Count-1)] | ForEach-Object {
            $parts = $_ -split ','
            if ($parts.Length -lt 1) { return }
            $known.Add($parts[0]) | Out-Null
        }
    }
}

# 1) Scheduled payment inscriptions today
$todayInsc = New-Object System.Collections.Generic.List[Object]
$scheduledPaiements = 0
foreach ($cle in $surveillances.Keys) {
    $list = $surveillances[$cle]
    if (-not $list -or $list.Count -eq 0) { continue }
    $lastSurv = ($list | Sort-Object)[-1]
    $target = $lastSurv.AddDays( (Payment-Delay-Days $cle) )
    if ($target -eq $day) {
        # Avoid if already inscription before today
        $existing = $false
    if ($inscriptions[$cle]) { foreach ($t in $inscriptions[$cle]) { if ($t.insc -le $day) { $existing = $true; break } } }
        if (-not $existing) {
            $todayInsc.Add([PSCustomObject]@{cle_bdf=$cle;statut_ficp='INSCRIT';type_incident='PAIEMENT';date_surveillance=$lastSurv.ToString('yyyy-MM-dd');date_inscription=$dayStr})
            $scheduledPaiements++
        }
    }
}

$remaining = [Math]::Max(0,$EVENEMENTS_PAR_JOUR - $scheduledPaiements)
$newDirect = [int][Math]::Round($remaining * $PART_SURDET)
$newSurv = $remaining - $newDirect

$existingKeys = [System.Collections.Generic.HashSet[string]]::new($known)

# Direct SURENDETTEMENT
for ($i=0; $i -lt $newDirect; $i++) {
    $cle = New-Key $existingKeys
    $todayInsc.Add([PSCustomObject]@{cle_bdf=$cle;statut_ficp='INSCRIT';type_incident='SURENDETTEMENT';date_surveillance='';date_inscription=$dayStr})
    Add-Insc $cle $day 'SURENDETTEMENT' $null
}

# New SURVEILLANCE (PAIEMENT)
for ($i=0; $i -lt $newSurv; $i++) {
    $cle = New-Key $existingKeys
    $todayInsc.Add([PSCustomObject]@{cle_bdf=$cle;statut_ficp='SURVEILLANCE';type_incident='PAIEMENT';date_surveillance=$dayStr;date_inscription=''})
    Add-Surv $cle $day
}

# Radiations
$todayRad = New-Object System.Collections.Generic.List[Object]
foreach ($cle in $inscriptions.Keys) {
    foreach ($t in $inscriptions[$cle]) {
        $inscDt = $t.insc; $typeInc = $t.type
        if ($inscDt -ge $day) { continue }
        if (Will-Radiate $cle) {
            $rday = $inscDt.AddDays( (Radiation-Delay-Days $cle) )
            if ($rday -eq $day) {
                $todayRad.Add([PSCustomObject]@{cle_bdf=$cle;date_inscription=$inscDt.ToString('yyyy-MM-dd');date_radiation=$dayStr;type_incident=$typeInc})
            }
        }
    }
}

function Compute-Status($cle) {
    $inscs = $inscriptions[$cle]
    if ($inscs) {
        $valid = @($inscs | Where-Object { $_.insc -le $day } | Sort-Object insc)
        if ($valid.Count -gt 0) {
            $last = $valid[-1]
            $survDt = if ($last.surv) { $last.surv.ToString('yyyy-MM-dd') } else { '' }
            return @('INSCRIT',$survDt,$last.insc.ToString('yyyy-MM-dd'))
        }
    }
    $survs = $surveillances[$cle]
    if ($survs) {
        $valid = @($survs | Where-Object { $_ -le $day } | Sort-Object)
        if ($valid.Count -gt 0) {
            return @('SURVEILLANCE',$valid[-1].ToString('yyyy-MM-dd'),'')
        }
    }
    return @('NON_INSCRIT','','')
}

# Consultations
$consultRows = New-Object System.Collections.Generic.List[Object]
$knownPool = @($existingKeys)
$nbKnown = [int]($CONSULTATIONS_PAR_JOUR * 0.6)
$nbNew = $CONSULTATIONS_PAR_JOUR - $nbKnown

for ($i=0; $i -lt $nbKnown; $i++) {
    $cle = if ($knownPool.Count -gt 0) { $knownPool[(Get-Random -Min 0 -Max $knownPool.Count)] } else { New-Key $existingKeys }
    $statusParts = Compute-Status $cle
    $consultRows.Add([PSCustomObject]@{cle_bdf=$cle;date_consultation=$dayStr;statut_ficp=$statusParts[0];date_surveillance=$statusParts[1];date_inscription=$statusParts[2]})
}
for ($i=0; $i -lt $nbNew; $i++) {
    $cle = New-Key $existingKeys
    $consultRows.Add([PSCustomObject]@{cle_bdf=$cle;date_consultation=$dayStr;statut_ficp='NON_INSCRIT';date_surveillance='';date_inscription=''})
}

# Write CSV helper
function Write-CsvRows($path,$header,$rows) {
    $sb = New-Object System.Text.StringBuilder
    $null = $sb.AppendLine( ($header -join ',') )
    foreach ($r in $rows) {
        $values = foreach ($col in $header) { $r.$col }
        $line = ($values -join ',')
        $null = $sb.AppendLine($line)
    }
    [IO.File]::WriteAllText($path,$sb.ToString(),[Text.UTF8Encoding]::new($false))
}

Write-CsvRows $consultPath @('cle_bdf','date_consultation','statut_ficp','date_surveillance','date_inscription') $consultRows
Write-CsvRows $inscrPath   @('cle_bdf','statut_ficp','type_incident','date_surveillance','date_inscription') $todayInsc
Write-CsvRows $radPath     @('cle_bdf','date_inscription','date_radiation','type_incident') $todayRad

$countConsult = $consultRows.Count
$countInsc    = $todayInsc.Count
$countRad     = $todayRad.Count
$sizeConsult = (Get-Item $consultPath).Length
$sizeInsc    = (Get-Item $inscrPath).Length
$sizeRad     = (Get-Item $radPath).Length
$totalSize   = $sizeConsult + $sizeInsc + $sizeRad
Write-Output "SUMMARY LOCAL $dayStr -> consultations=$countConsult inscriptions=$countInsc radiations=$countRad size_bytes_total=$totalSize"
Write-Output "SUMMARY SIZES $dayStr -> consult=$sizeConsult inscr=$sizeInsc rad=$sizeRad"
Write-Output "OK - files generated: $consultPath $inscrPath $radPath"

if ($SkipUpload) {
    Write-Output "SkipUpload enabled - upload phase skipped."
} else {
    # Attempt managed identity login (Automation). Safe to ignore if running locally.
    try { Connect-AzAccount -Identity -ErrorAction Stop | Out-Null } catch { Write-Output "Identity login not used (local or already authenticated)." }
    # Upload to storage (prefer AAD context with managed identity)
    try {
        $ctx = New-AzStorageContext -StorageAccountName $StorageAccountName -UseConnectedAccount -ErrorAction Stop
    } catch {
        # Fallback to ARM context (requires Reader role on storage account)
        $ctx = (Get-AzStorageAccount -ResourceGroupName $ResourceGroup -Name $StorageAccountName).Context
    }
    $container = Get-AzStorageContainer -Context $ctx -Name $ContainerName -ErrorAction SilentlyContinue
    if (-not $container) { $container = New-AzStorageContainer -Context $ctx -Name $ContainerName -Permission Off }

    Set-AzStorageBlobContent -Context $ctx -Container $ContainerName -File $consultPath -Blob "consultation/$dayStr.csv" -Force | Out-Null
    Set-AzStorageBlobContent -Context $ctx -Container $ContainerName -File $inscrPath -Blob "inscription/$dayStr.csv" -Force | Out-Null
    Set-AzStorageBlobContent -Context $ctx -Container $ContainerName -File $radPath -Blob "radiation/$dayStr.csv" -Force | Out-Null

    Write-Output "UPLOAD OK vers $StorageAccountName/$ContainerName pour $dayStr"
    Write-Output "SUMMARY REMOTE $dayStr -> consultations=$countConsult inscriptions=$countInsc radiations=$countRad size_bytes_total=$totalSize"
}

# Durée d'exécution totale
$__elapsed = (Get-Date) - $__start
Write-Output "SUMMARY DURATION $dayStr -> seconds=$([int]$__elapsed.TotalSeconds)" 
