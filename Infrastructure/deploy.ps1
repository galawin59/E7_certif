# ===============================
# SCRIPT DE DÉPLOIEMENT DATA LAKE FICP
# Certification Data Engineer C19
# ===============================

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("test", "prod")]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "francecentral",
    
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$false)]
    [switch]$WhatIf
)

# Configuration
$ResourcePrefix = "dl-ficp"
$ResourceGroupName = "rg-$ResourcePrefix-$Environment"

# Couleurs pour l'affichage
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Green "🚀 DÉPLOIEMENT DATA LAKE FICP - ENVIRONNEMENT: $Environment"
Write-ColorOutput Green "=================================================="

# 1. Vérification des prérequis
Write-ColorOutput Yellow "📋 Vérification des prérequis..."

# Vérifier Azure CLI
try {
    $azVersion = az --version | Select-String "azure-cli" | ForEach-Object { $_.ToString().Split()[1] }
    Write-ColorOutput Green "✅ Azure CLI version: $azVersion"
} catch {
    Write-ColorOutput Red "❌ Azure CLI non installé. Installez-le depuis: https://aka.ms/azure-cli"
    exit 1
}

# Vérifier connexion Azure
try {
    $currentAccount = az account show --query "name" -o tsv 2>$null
    if ($currentAccount) {
        Write-ColorOutput Green "✅ Connecté à Azure: $currentAccount"
    } else {
        Write-ColorOutput Yellow "🔐 Connexion à Azure requise..."
        az login
    }
} catch {
    Write-ColorOutput Yellow "🔐 Connexion à Azure..."
    az login
}

# Définir la subscription si fournie
if ($SubscriptionId) {
    Write-ColorOutput Yellow "🎯 Configuration de la subscription: $SubscriptionId"
    az account set --subscription $SubscriptionId
}

$currentSub = az account show --query "name" -o tsv
Write-ColorOutput Green "✅ Subscription active: $currentSub"

# 2. Création du Resource Group
Write-ColorOutput Yellow "📁 Création du Resource Group: $ResourceGroupName"

$rgExists = az group exists --name $ResourceGroupName
if ($rgExists -eq "false") {
    if ($WhatIf) {
        Write-ColorOutput Cyan "🔍 [WHAT-IF] Créerait le Resource Group: $ResourceGroupName"
    } else {
        az group create --name $ResourceGroupName --location $Location
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "✅ Resource Group créé: $ResourceGroupName"
        } else {
            Write-ColorOutput Red "❌ Échec création Resource Group"
            exit 1
        }
    }
} else {
    Write-ColorOutput Green "✅ Resource Group existe déjà: $ResourceGroupName"
}

# 3. Validation du template Bicep
Write-ColorOutput Yellow "🔍 Validation du template Bicep..."

$bicepFile = Join-Path $PSScriptRoot "main.bicep"
if (-not (Test-Path $bicepFile)) {
    Write-ColorOutput Red "❌ Fichier main.bicep introuvable dans: $PSScriptRoot"
    exit 1
}

$validationResult = az deployment group validate `
    --resource-group $ResourceGroupName `
    --template-file $bicepFile `
    --parameters environment=$Environment location=$Location `
    --query "error" -o tsv 2>$null

if ($validationResult -and $validationResult -ne "null") {
    Write-ColorOutput Red "❌ Erreur de validation Bicep:"
    Write-ColorOutput Red $validationResult
    exit 1
} else {
    Write-ColorOutput Green "✅ Template Bicep valide"
}

# 4. Estimation des coûts (simulation)
Write-ColorOutput Yellow "💰 Estimation des coûts mensuels..."
Write-ColorOutput Cyan "   Storage Account (Standard LRS): ~1€"
Write-ColorOutput Cyan "   Data Factory (Basic): ~2€"
Write-ColorOutput Cyan "   Synapse Serverless: ~1€"
Write-ColorOutput Cyan "   Purview Account: ~3€"
Write-ColorOutput Cyan "   Log Analytics: ~0.50€"
Write-ColorOutput Cyan "   ================================="
Write-ColorOutput Green "   TOTAL ESTIMÉ: ~7.50€/mois"

# Confirmation avant déploiement
if (-not $WhatIf) {
    Write-ColorOutput Yellow "⚠️  Confirmer le déploiement en environnement $Environment ? (O/N)"
    $confirmation = Read-Host
    if ($confirmation -ne "O" -and $confirmation -ne "o" -and $confirmation -ne "Y" -and $confirmation -ne "y") {
        Write-ColorOutput Yellow "🚫 Déploiement annulé par l'utilisateur"
        exit 0
    }
}

# 5. Déploiement de l'infrastructure
if ($WhatIf) {
    Write-ColorOutput Cyan "🔍 [WHAT-IF] Simulation du déploiement..."
    az deployment group what-if `
        --resource-group $ResourceGroupName `
        --template-file $bicepFile `
        --parameters environment=$Environment location=$Location
} else {
    Write-ColorOutput Yellow "🚀 Déploiement de l'infrastructure..."
    
    $deploymentName = "datalake-ficp-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    
    $deployment = az deployment group create `
        --resource-group $ResourceGroupName `
        --name $deploymentName `
        --template-file $bicepFile `
        --parameters environment=$Environment location=$Location `
        --output json | ConvertFrom-Json
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✅ Déploiement réussi!"
        
        # Affichage des outputs
        Write-ColorOutput Yellow "📋 Informations des ressources créées:"
        $outputs = $deployment.properties.outputs
        
        foreach ($output in $outputs.PSObject.Properties) {
            $name = $output.Name
            $value = $output.Value.value
            Write-ColorOutput Cyan "   $name : $value"
        }
        
        # URLs d'accès rapide
        Write-ColorOutput Yellow "🔗 Liens d'accès rapide:"
        if ($outputs.dataFactoryUrl) {
            Write-ColorOutput Cyan "   Data Factory: $($outputs.dataFactoryUrl.value)"
        }
        if ($outputs.synapseStudioUrl) {
            Write-ColorOutput Cyan "   Synapse Studio: $($outputs.synapseStudioUrl.value)"
        }
        if ($outputs.purviewStudioUrl) {
            Write-ColorOutput Cyan "   Purview Studio: $($outputs.purviewStudioUrl.value)"
        }
        
    } else {
        Write-ColorOutput Red "❌ Échec du déploiement"
        exit 1
    }
}

# 6. Configuration post-déploiement
if (-not $WhatIf) {
    Write-ColorOutput Yellow "⚙️  Configuration post-déploiement..."
    
    # Attendre que les services soient prêts
    Write-ColorOutput Yellow "⏳ Attente de la disponibilité des services (30s)..."
    Start-Sleep -Seconds 30
    
    # Configuration des permissions supplémentaires si nécessaire
    Write-ColorOutput Yellow "🔐 Vérification des permissions RBAC..."
    
    # Récupérer l'utilisateur courant pour lui donner les accès
    $currentUser = az ad signed-in-user show --query "id" -o tsv
    $storageAccountName = $outputs.storageAccountName.value
    
    # Assigner Storage Blob Data Contributor à l'utilisateur courant
    $roleAssignment = az role assignment create `
        --assignee $currentUser `
        --role "Storage Blob Data Contributor" `
        --scope "/subscriptions/$(az account show --query 'id' -o tsv)/resourceGroups/$ResourceGroupName/providers/Microsoft.Storage/storageAccounts/$storageAccountName" `
        2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput Green "✅ Permissions utilisateur configurées"
    } else {
        Write-ColorOutput Yellow "⚠️  Configuration manuelle des permissions peut être nécessaire"
    }
}

# 7. Validation du déploiement
Write-ColorOutput Yellow "🧪 Validation du déploiement..."

if (-not $WhatIf) {
    # Test de connectivité aux services
    $resourcesOk = 0
    $totalResources = 5
    
    # Test Storage Account
    $storageExists = az storage account show --name $outputs.storageAccountName.value --resource-group $ResourceGroupName --query "name" -o tsv 2>$null
    if ($storageExists) {
        Write-ColorOutput Green "✅ Storage Account accessible"
        $resourcesOk++
    } else {
        Write-ColorOutput Red "❌ Storage Account non accessible"
    }
    
    # Test Data Factory
    $adfExists = az datafactory show --name $outputs.dataFactoryName.value --resource-group $ResourceGroupName --query "name" -o tsv 2>$null
    if ($adfExists) {
        Write-ColorOutput Green "✅ Data Factory accessible"
        $resourcesOk++
    } else {
        Write-ColorOutput Red "❌ Data Factory non accessible"
    }
    
    # Score final
    $successRate = [math]::Round(($resourcesOk / $totalResources) * 100)
    if ($successRate -ge 80) {
        Write-ColorOutput Green "🎉 DÉPLOIEMENT RÉUSSI ($successRate% des services OK)"
    } else {
        Write-ColorOutput Yellow "⚠️  DÉPLOIEMENT PARTIEL ($successRate% des services OK)"
    }
}

Write-ColorOutput Yellow "📚 Prochaines étapes:"
Write-ColorOutput Cyan "   1. Configurer les pipelines Data Factory"
Write-ColorOutput Cyan "   2. Uploader les données FICP test"
Write-ColorOutput Cyan "   3. Configurer Purview scan"
Write-ColorOutput Cyan "   4. Créer les vues Synapse"
Write-ColorOutput Cyan "   5. Développer le dashboard Power BI"

Write-ColorOutput Green "🏁 SCRIPT TERMINÉ - Environnement $Environment prêt!"

# Génération du fichier de configuration pour les étapes suivantes
$configFile = "config-$Environment.json"
$config = @{
    environment = $Environment
    resourceGroup = $ResourceGroupName
    location = $Location
    deploymentDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

if (-not $WhatIf -and $outputs) {
    $config.storageAccount = $outputs.storageAccountName.value
    $config.dataFactory = $outputs.dataFactoryName.value
    $config.synapseWorkspace = $outputs.synapseWorkspaceName.value
    $config.purviewAccount = $outputs.purviewAccountName.value
}

$config | ConvertTo-Json -Depth 3 | Out-File -FilePath $configFile -Encoding UTF8
Write-ColorOutput Green "✅ Configuration sauvée dans: $configFile"