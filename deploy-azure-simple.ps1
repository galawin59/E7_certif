# DEPLOIEMENT DATA LAKE FICP - CERTIFICATION
Write-Host "=== DEPLOIEMENT DATA LAKE E7 CERTIFICATION ===" -ForegroundColor Green
Write-Host ""

# Import des modules necessaires
Write-Host "Chargement des modules Azure..." -ForegroundColor Yellow
Import-Module Az.Accounts -Force
Import-Module Az.Resources -Force

# Verification connexion Azure
Write-Host "Verification connexion Azure..." -ForegroundColor Yellow
try {
    $context = Get-AzContext
    if ($null -eq $context) {
        Write-Host "Pas de connexion Azure detectee" -ForegroundColor Red
        Write-Host "Connectez-vous avec: Connect-AzAccount" -ForegroundColor Cyan
        exit 1
    }
    Write-Host "Connecte a Azure: $($context.Account.Id)" -ForegroundColor Green
    Write-Host "Subscription: $($context.Subscription.Name)" -ForegroundColor Cyan
} catch {
    Write-Host "Erreur verification Azure: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Configuration du projet
$resourceGroupName = "rg-datalake-ficp"
$location = "France Central"
$projectName = "ficp"

Write-Host ""
Write-Host "=== PARAMETRES DE DEPLOIEMENT ===" -ForegroundColor Cyan
Write-Host "Resource Group: $resourceGroupName"
Write-Host "Location: $location (France du Nord)"
Write-Host "Project Name: $projectName (FICP Data Lake)"
Write-Host ""

# Creation du Resource Group
Write-Host "Creation du Resource Group..." -ForegroundColor Yellow
try {
    $rg = New-AzResourceGroup -Name $resourceGroupName -Location $location -Force
    Write-Host "Resource Group cree avec succes: $($rg.ResourceGroupName)" -ForegroundColor Green
} catch {
    Write-Host "Erreur creation Resource Group: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== ETAPE 1 TERMINEE AVEC SUCCES ===" -ForegroundColor Green
Write-Host "Prochaine etape: Deploiement du template Bicep"
Write-Host "Allez sur portal.azure.com pour voir votre Resource Group!"
