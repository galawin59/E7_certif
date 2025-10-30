# CREATION ARCHITECTURE MEDALLION DATA LAKE FICP
Import-Module Az.Storage -Force

Write-Host "CREATION ARCHITECTURE MEDALLION" -ForegroundColor Green
Write-Host "===============================" -ForegroundColor Green

$resourceGroupName = "rg-datalake-ficp"
$storageAccountName = "ficpstorageaccount"

# Containers Medallion
$containers = @("bronze-ficp", "silver-ficp", "gold-ficp", "logs-ficp")

try {
    $storageAccount = Get-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName
    $ctx = $storageAccount.Context
    
    Write-Host "Creation des couches Medallion..." -ForegroundColor Yellow
    
    foreach ($container in $containers) {
        try {
            New-AzStorageContainer -Name $container -Context $ctx -ErrorAction SilentlyContinue
            Write-Host "-> Container $container cree" -ForegroundColor Green
        } catch {
            Write-Host "-> Container $container existe deja" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "ARCHITECTURE MEDALLION CREEE !" -ForegroundColor Green
    Write-Host ""
    Write-Host "COUCHES DISPONIBLES :" -ForegroundColor Cyan
    Write-Host "Bronze: Donnees brutes CSV" -ForegroundColor White
    Write-Host "Silver: Donnees nettoyees Parquet" -ForegroundColor White
    Write-Host "Gold: KPI et dashboards" -ForegroundColor White
    Write-Host "Logs: Suivi des traitements" -ForegroundColor White
    
} catch {
    Write-Host "ERREUR: $($_.Exception.Message)" -ForegroundColor Red
}