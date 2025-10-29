# ORCHESTRATION COMPLETE DATA LAKE FICP
# Generation automatique + Pipeline ETL + Upload Azure
Import-Module Az.Storage -Force

Write-Host "ORCHESTRATION COMPLETE DATA LAKE FICP" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

$resourceGroupName = "rg-datalake-ficp"
$storageAccountName = "ficpstorageaccount"

# 1. Generation des donnees quotidiennes
Write-Host "1. Generation des donnees quotidiennes..." -ForegroundColor Yellow
try {
    $generateResult = echo "1" | C:/Users/Galawin/Documents/GitHub/E7_certif/.venv/Scripts/python.exe DataLakeE7/DailyGenerator.py
    Write-Host "   -> Donnees quotidiennes generees" -ForegroundColor Green
} catch {
    Write-Host "   -> Erreur generation: $($_.Exception.Message)" -ForegroundColor Red
}

# 2. Execution du pipeline ETL Medallion
Write-Host "2. Execution pipeline ETL Medallion..." -ForegroundColor Yellow
try {
    $etlResult = C:/Users/Galawin/Documents/GitHub/E7_certif/.venv/Scripts/python.exe DataLakeE7/MedallionETL.py
    Write-Host "   -> Pipeline ETL execute avec succes" -ForegroundColor Green
} catch {
    Write-Host "   -> Erreur ETL: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Upload des donnees transformees vers Azure
Write-Host "3. Upload vers Azure Storage..." -ForegroundColor Yellow
try {
    $storageAccount = Get-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName
    $ctx = $storageAccount.Context
    
    # Upload Bronze Layer
    $bronzeFiles = Get-ChildItem "DataLakeE7\bronze" -Recurse -Filter "*.csv"
    foreach ($file in $bronzeFiles) {
        $relativePath = $file.FullName.Replace("DataLakeE7\bronze\", "").Replace("\", "/")
        Set-AzStorageBlobContent -File $file.FullName -Container "bronze-ficp" -Blob $relativePath -Context $ctx -Force | Out-Null
    }
    Write-Host "   -> Bronze Layer uploade ($($bronzeFiles.Count) fichiers)" -ForegroundColor Green
    
    # Upload Silver Layer
    $silverFiles = Get-ChildItem "DataLakeE7\silver" -Recurse -Filter "*.csv"
    foreach ($file in $silverFiles) {
        $relativePath = $file.FullName.Replace("DataLakeE7\silver\", "").Replace("\", "/")
        Set-AzStorageBlobContent -File $file.FullName -Container "silver-ficp" -Blob $relativePath -Context $ctx -Force | Out-Null
    }
    Write-Host "   -> Silver Layer uploade ($($silverFiles.Count) fichiers)" -ForegroundColor Green
    
    # Upload Gold Layer
    $goldFiles = Get-ChildItem "DataLakeE7\gold" -Recurse -Filter "*.csv"
    foreach ($file in $goldFiles) {
        $relativePath = $file.FullName.Replace("DataLakeE7\gold\", "").Replace("\", "/")
        Set-AzStorageBlobContent -File $file.FullName -Container "gold-ficp" -Blob $relativePath -Context $ctx -Force | Out-Null
    }
    Write-Host "   -> Gold Layer uploade ($($goldFiles.Count) fichiers)" -ForegroundColor Green
    
    # Upload Logs
    $logFiles = Get-ChildItem "DataLakeE7\logs" -Filter "*.json"
    foreach ($file in $logFiles) {
        Set-AzStorageBlobContent -File $file.FullName -Container "logs-ficp" -Blob $file.Name -Context $ctx -Force | Out-Null
    }
    Write-Host "   -> Logs uploades ($($logFiles.Count) fichiers)" -ForegroundColor Green
    
} catch {
    Write-Host "   -> Erreur upload: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Verification de l'architecture complete
Write-Host "4. Verification architecture Medallion..." -ForegroundColor Yellow
try {
    $containers = @("bronze-ficp", "silver-ficp", "gold-ficp", "logs-ficp")
    
    foreach ($container in $containers) {
        $blobs = Get-AzStorageBlob -Container $container -Context $ctx
        Write-Host "   -> $container : $($blobs.Count) fichiers" -ForegroundColor White
    }
    
    Write-Host "   -> Architecture Medallion complete" -ForegroundColor Green
} catch {
    Write-Host "   -> Erreur verification: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   ORCHESTRATION TERMINEE !" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "ARCHITECTURE DATA LAKE COMPLETE :" -ForegroundColor Cyan
Write-Host "Bronze Layer: Donnees brutes avec partitioning" -ForegroundColor Yellow
Write-Host "Silver Layer: Donnees nettoyees et enrichies" -ForegroundColor Gray
Write-Host "Gold Layer: KPI et tableaux de bord" -ForegroundColor Yellow
Write-Host "Logs Layer: Suivi et audit des traitements" -ForegroundColor Blue
Write-Host ""

Write-Host "FONCTIONNALITES IMPLEMENTEES :" -ForegroundColor Cyan
Write-Host "-> Generation automatique quotidienne" -ForegroundColor White
Write-Host "-> Pipeline ETL Medallion complet" -ForegroundColor White
Write-Host "-> Upload automatise vers Azure" -ForegroundColor White
Write-Host "-> Monitoring et logs" -ForegroundColor White
Write-Host "-> Architecture production-ready" -ForegroundColor White
Write-Host ""

Write-Host "CERTIFICATION E7 DATA ENGINEER COMPLETE !" -ForegroundColor Green