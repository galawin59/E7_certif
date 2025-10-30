Import-Module Az.Accounts -Force
Import-Module Az.Resources -Force

Write-Host "========================================" -ForegroundColor Green
Write-Host "   DEPLOIEMENT DATA LAKE FICP COMPLET" -ForegroundColor Green  
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Configuration
$resourceGroupName = "rg-datalake-ficp"
$location = "France Central"
$templateFile = ".\Infrastructure\main.bicep"

Write-Host "PARAMETRES DE DEPLOIEMENT :" -ForegroundColor Cyan
Write-Host "-> Resource Group: $resourceGroupName"
Write-Host "-> Location: $location"
Write-Host "-> Template: $templateFile"
Write-Host ""

# Verification du template
if (!(Test-Path $templateFile)) {
    Write-Host "ERREUR: Template Bicep introuvable: $templateFile" -ForegroundColor Red
    exit 1
}

Write-Host "Template Bicep trouve" -ForegroundColor Green
Write-Host ""

# Deploiement des ressources
Write-Host "DEPLOIEMENT DES RESSOURCES DATA LAKE..." -ForegroundColor Yellow
Write-Host "Cela peut prendre 3-5 minutes..."
Write-Host ""

try {
    $deployment = New-AzResourceGroupDeployment `
        -ResourceGroupName $resourceGroupName `
        -TemplateFile $templateFile `
        -location $location `
        -Verbose

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   DEPLOIEMENT REUSSI !" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "RESSOURCES CREEES :" -ForegroundColor Cyan
    if ($deployment.Outputs.Keys -contains 'storageAccountName') {
        Write-Host "-> Storage Account: $($deployment.Outputs.storageAccountName.Value)" -ForegroundColor White
    }
    if ($deployment.Outputs.Keys -contains 'dataFactoryName') {
        Write-Host "-> Data Factory: $($deployment.Outputs.dataFactoryName.Value)" -ForegroundColor White
    }
    if ($deployment.Outputs.Keys -contains 'keyVaultName') {
        Write-Host "-> Key Vault: $($deployment.Outputs.keyVaultName.Value)" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "VOTRE DATA LAKE FICP EST PRET !" -ForegroundColor Green
    Write-Host ""
    Write-Host "PROCHAINES ETAPES :" -ForegroundColor Yellow
    Write-Host "1. Allez sur portal.azure.com"
    Write-Host "2. Naviguez vers le Resource Group: $resourceGroupName"  
    Write-Host "3. Explorez vos ressources Data Lake"
    Write-Host "4. Uploadez vos donnees FICP pour tester"
    Write-Host ""
    Write-Host "CERTIFICATION E7 - OBJECTIF ATTEINT !" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "ERREUR DEPLOIEMENT:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifiez vos permissions Azure et ressayez" -ForegroundColor Yellow
    exit 1
}