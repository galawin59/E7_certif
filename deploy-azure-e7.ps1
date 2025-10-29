# ====================================
# DÉPLOIEMENT DATA LAKE E7 - CERTIFICATION
# Script propre pour compte Azure GitHub
# ====================================

Write-Host "🎓 DÉPLOIEMENT DATA LAKE E7 CERTIFICATION" -ForegroundColor Green
Write-Host ""

# Vérification de la connexion Azure
Write-Host "🔍 Vérification connexion Azure..." -ForegroundColor Yellow
try {
    $context = Get-AzContext
    if ($null -eq $context) {
        Write-Host "❌ Pas de connexion Azure détectée" -ForegroundColor Red
        Write-Host "💡 Connectez-vous avec: Connect-AzAccount" -ForegroundColor Cyan
        exit 1
    }
    Write-Host "✅ Connecté à Azure: $($context.Account.Id)" -ForegroundColor Green
    Write-Host "📋 Subscription: $($context.Subscription.Name)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Erreur de vérification Azure: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Configuration du projet
$resourceGroupName = "rg-datalake-e7"
$location = "West Europe"
$projectName = "e7certif"

Write-Host "📋 PARAMÈTRES DE DÉPLOIEMENT :" -ForegroundColor Cyan
Write-Host "→ Resource Group: $resourceGroupName"
Write-Host "→ Location: $location"
Write-Host "→ Project Name: $projectName"
Write-Host ""

# Création du Resource Group
Write-Host "🏗️ Création Resource Group..." -ForegroundColor Yellow
try {
    $rg = New-AzResourceGroup -Name $resourceGroupName -Location $location -Force
    Write-Host "✅ Resource Group créé: $($rg.ResourceGroupName)" -ForegroundColor Green
} catch {
    Write-Host "❌ Erreur création Resource Group: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Déploiement du template Bicep
Write-Host "🚀 Déploiement infrastructure Data Lake..." -ForegroundColor Yellow
$templateFile = ".\Infrastructure\main.bicep"

if (Test-Path $templateFile) {
    try {
        $deployment = New-AzResourceGroupDeployment `
            -ResourceGroupName $resourceGroupName `
            -TemplateFile $templateFile `
            -projectName $projectName `
            -location $location `
            -Verbose

        Write-Host "✅ DÉPLOIEMENT RÉUSSI !" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 RESSOURCES CRÉÉES :" -ForegroundColor Cyan
        Write-Host "→ Data Lake Gen2: $($deployment.Outputs.dataLakeAccountName.Value)"
        Write-Host "→ Data Factory: $($deployment.Outputs.dataFactoryName.Value)"
        Write-Host "→ Key Vault: $($deployment.Outputs.keyVaultName.Value)"
        Write-Host ""
        Write-Host "🎉 VOTRE DATA LAKE EST PRÊT POUR LA CERTIFICATION !" -ForegroundColor Green
        
    } catch {
        Write-Host "❌ Erreur déploiement: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Template Bicep introuvable: $templateFile" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔗 PROCHAINES ÉTAPES :" -ForegroundColor Cyan
Write-Host "1. Connectez-vous au portail Azure"
Write-Host "2. Naviguez vers le Resource Group: $resourceGroupName"
Write-Host "3. Explorez vos ressources Data Lake"
Write-Host "4. Uploadez vos données FICP pour tester"
Write-Host ""
Write-Host "💪 Félicitations ! Votre environnement E7 est déployé !" -ForegroundColor Green