# EXPLORATION COMPLETE DATA LAKE FICP
Import-Module Az.Storage -Force

Write-Host "========================================" -ForegroundColor Green
Write-Host "   EXPLORATION DATA LAKE MEDALLION" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$resourceGroupName = "rg-datalake-ficp"
$storageAccountName = "ficpstorageaccount"

try {
    $storageAccount = Get-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName
    $ctx = $storageAccount.Context
    
    # Liste des containers (couches)
    $containers = @("bronze-ficp", "silver-ficp", "gold-ficp", "logs-ficp", "ficp-data")
    
    foreach ($containerName in $containers) {
        Write-Host "=== COUCHE: $containerName ===" -ForegroundColor Cyan
        
        try {
            $blobs = Get-AzStorageBlob -Container $containerName -Context $ctx
            
            if ($blobs.Count -eq 0) {
                Write-Host "   -> Aucun fichier" -ForegroundColor Yellow
            } else {
                Write-Host "   -> $($blobs.Count) fichiers total" -ForegroundColor Green
                
                # Affichage détaillé des fichiers
                $blobs | Sort-Object Name | ForEach-Object {
                    $sizeKB = [math]::Round($_.Length / 1KB, 2)
                    $lastModified = $_.LastModified.ToString("dd/MM/yyyy HH:mm")
                    Write-Host "      $($_.Name)" -ForegroundColor White
                    Write-Host "        Taille: $sizeKB KB | Modifie: $lastModified" -ForegroundColor Gray
                }
                
                # Statistiques par couche
                $totalSize = ($blobs | Measure-Object Length -Sum).Sum
                $totalSizeMB = [math]::Round($totalSize / 1MB, 2)
                Write-Host "   -> Taille totale: $totalSizeMB MB" -ForegroundColor Green
            }
        } catch {
            Write-Host "   -> Container inexistant ou inaccessible" -ForegroundColor Red
        }
        
        Write-Host ""
    }
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   RESUME ARCHITECTURE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Résumé global
    $totalFiles = 0
    $totalSizeGlobal = 0
    
    foreach ($containerName in $containers) {
        try {
            $blobs = Get-AzStorageBlob -Container $containerName -Context $ctx -ErrorAction SilentlyContinue
            $containerSize = ($blobs | Measure-Object Length -Sum).Sum
            $totalFiles += $blobs.Count
            $totalSizeGlobal += $containerSize
            
            $containerSizeMB = [math]::Round($containerSize / 1MB, 2)
            
            $description = switch ($containerName) {
                "bronze-ficp" { "Donnees brutes partitionnees" }
                "silver-ficp" { "Donnees nettoyees et enrichies" }
                "gold-ficp" { "KPI et analytics business" }
                "logs-ficp" { "Audit et monitoring" }
                "ficp-data" { "Donnees initiales de test" }
            }
            
            Write-Host "$containerName".PadRight(15) " | $($blobs.Count) fichiers | $containerSizeMB MB | $description" -ForegroundColor White
        } catch {
            Write-Host "$containerName".PadRight(15) " | Non accessible" -ForegroundColor Red
        }
    }
    
    $totalSizeGlobalMB = [math]::Round($totalSizeGlobal / 1MB, 2)
    Write-Host ""
    Write-Host "TOTAL GLOBAL: $totalFiles fichiers | $totalSizeGlobalMB MB" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "LIENS DIRECTS PORTAIL AZURE :" -ForegroundColor Cyan
    Write-Host "-> Storage Account: https://portal.azure.com/#@/resource/subscriptions/.../resourceGroups/$resourceGroupName/providers/Microsoft.Storage/storageAccounts/$storageAccountName" -ForegroundColor Yellow
    Write-Host "-> Resource Group: https://portal.azure.com/#@/resource/subscriptions/.../resourceGroups/$resourceGroupName" -ForegroundColor Yellow
    
} catch {
    Write-Host "ERREUR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Verifiez votre connexion Azure" -ForegroundColor Yellow
}