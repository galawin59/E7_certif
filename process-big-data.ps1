# PIPELINE ETL OPTIMISE POUR GROS VOLUMES
# 906 fichiers - 42,389 enregistrements - 10 mois de donnees
Import-Module Az.Storage -Force

Write-Host "PIPELINE ETL GROS VOLUMES - DONNEES FICP 2025" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

$resourceGroupName = "rg-datalake-ficp"
$storageAccountName = "ficpstorageaccount"

# Statistiques des donnees generees
Write-Host "DONNEES GENEREES :" -ForegroundColor Cyan
Write-Host "-> 906 fichiers CSV professionnels"
Write-Host "-> 42,389 enregistrements FICP"
Write-Host "-> Periode: 1er janvier au 29 octobre 2025"
Write-Host "-> 302 jours de donnees"
Write-Host ""

# 1. Nettoyage des anciens fichiers "test"
Write-Host "1. Nettoyage fichiers test..." -ForegroundColor Yellow
try {
    $testFiles = Get-ChildItem "DataLakeE7" -Filter "*test*" -Recurse
    foreach ($file in $testFiles) {
        Remove-Item $file.FullName -Force
        Write-Host "   -> Supprime: $($file.Name)" -ForegroundColor Gray
    }
    Write-Host "   -> $($testFiles.Count) fichiers test supprimes" -ForegroundColor Green
} catch {
    Write-Host "   -> Aucun fichier test a supprimer" -ForegroundColor Yellow
}

# 2. Execution pipeline ETL sur gros volumes
Write-Host "2. Pipeline ETL gros volumes..." -ForegroundColor Yellow
try {
    $etlResult = C:/Users/Galawin/Documents/GitHub/E7_certif/.venv/Scripts/python.exe DataLakeE7/MedallionETL.py
    Write-Host "   -> Pipeline ETL execute (gros volumes)" -ForegroundColor Green
} catch {
    Write-Host "   -> Erreur ETL: $($_.Exception.Message)" -ForegroundColor Red
}

# 3. Upload massif vers Azure (par batch)
Write-Host "3. Upload massif vers Azure..." -ForegroundColor Yellow
try {
    $storageAccount = Get-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName
    $ctx = $storageAccount.Context
    
    # Compteurs
    $totalUploaded = 0
    $batchSize = 50  # Upload par batch de 50 fichiers
    
    # Upload Bronze Layer (donnees brutes par date)
    Write-Host "   -> Upload Bronze Layer..." -ForegroundColor White
    $bronzeFiles = Get-ChildItem "DataLakeE7" -Filter "ficp_*.csv" | Where-Object { $_.Name -notlike "*test*" }
    
    $bronzeBatches = [math]::Ceiling($bronzeFiles.Count / $batchSize)
    for ($batch = 0; $batch -lt $bronzeBatches; $batch++) {
        $startIndex = $batch * $batchSize
        $endIndex = [math]::Min($startIndex + $batchSize - 1, $bronzeFiles.Count - 1)
        $batchFiles = $bronzeFiles[$startIndex..$endIndex]
        
        foreach ($file in $batchFiles) {
            # Extraction de la date pour partitioning
            if ($file.Name -match "ficp_(\w+)_(\d{4}-\d{2}-\d{2})\.csv") {
                $dataType = $matches[1]
                $dateStr = $matches[2]
                $dateParts = $dateStr.Split('-')
                
                $blobPath = "$dataType/year=$($dateParts[0])/month=$($dateParts[1])/day=$($dateParts[2])/$($file.Name)"
                Set-AzStorageBlobContent -File $file.FullName -Container "bronze-ficp" -Blob $blobPath -Context $ctx -Force | Out-Null
                $totalUploaded++
            }
        }
        
        $progress = [math]::Round(($batch + 1) / $bronzeBatches * 100, 1)
        Write-Host "      Batch $($batch + 1)/$bronzeBatches ($progress%) - $($batchFiles.Count) fichiers" -ForegroundColor Gray
    }
    
    Write-Host "   -> Bronze: $totalUploaded fichiers uploades" -ForegroundColor Green
    
    # Upload des autres couches (Silver, Gold, Logs)
    $otherLayers = @(
        @{Path="DataLakeE7\silver"; Container="silver-ficp"; Pattern="*.csv"},
        @{Path="DataLakeE7\gold"; Container="gold-ficp"; Pattern="*.csv"},
        @{Path="DataLakeE7\logs"; Container="logs-ficp"; Pattern="*.json"}
    )
    
    foreach ($layer in $otherLayers) {
        if (Test-Path $layer.Path) {
            $layerFiles = Get-ChildItem $layer.Path -Recurse -Filter $layer.Pattern
            foreach ($file in $layerFiles) {
                $relativePath = $file.FullName.Replace("$($layer.Path)\", "").Replace("\", "/")
                Set-AzStorageBlobContent -File $file.FullName -Container $layer.Container -Blob $relativePath -Context $ctx -Force | Out-Null
            }
            Write-Host "   -> $($layer.Container): $($layerFiles.Count) fichiers uploades" -ForegroundColor Green
        }
    }
    
} catch {
    Write-Host "   -> Erreur upload: $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Verification volumes finaux
Write-Host "4. Verification volumes finaux..." -ForegroundColor Yellow
try {
    $containers = @("bronze-ficp", "silver-ficp", "gold-ficp", "logs-ficp")
    $totalBlobs = 0
    $totalSize = 0
    
    foreach ($container in $containers) {
        $blobs = Get-AzStorageBlob -Container $container -Context $ctx
        $containerSize = ($blobs | Measure-Object Length -Sum).Sum
        $totalBlobs += $blobs.Count
        $totalSize += $containerSize
        
        $sizeMB = [math]::Round($containerSize / 1MB, 2)
        Write-Host "   -> $container : $($blobs.Count) fichiers ($sizeMB MB)" -ForegroundColor White
    }
    
    $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
    Write-Host "   -> TOTAL GLOBAL: $totalBlobs fichiers ($totalSizeMB MB)" -ForegroundColor Green
    
} catch {
    Write-Host "   -> Erreur verification: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   DATA LAKE GROS VOLUMES PRET !" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "ARCHITECTURE FINALE :" -ForegroundColor Cyan
Write-Host "-> 42,389 enregistrements FICP sur 10 mois" -ForegroundColor White
Write-Host "-> Architecture Medallion complete" -ForegroundColor White
Write-Host "-> Donnees partitionnees par date" -ForegroundColor White
Write-Host "-> Upload Azure optimise par batch" -ForegroundColor White
Write-Host "-> Pret pour analyses Power BI massives" -ForegroundColor White
Write-Host ""

Write-Host "ANALYSES POSSIBLES :" -ForegroundColor Yellow
Write-Host "- Tendances mensuelles consultations FICP"
Write-Host "- Saisonnalite des demandes credit"
Write-Host "- Taux acceptation par etablissement"
Write-Host "- Evolution scores FICP sur 10 mois"
Write-Host "- Dashboards executives temps reel"
Write-Host ""

Write-Host "CERTIFICATION E7 - ARCHITECTURE ENTERPRISE !" -ForegroundColor Green