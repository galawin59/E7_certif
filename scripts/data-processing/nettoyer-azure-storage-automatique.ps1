# E7 CERTIFICATION - NETTOYAGE AZURE STORAGE BRONZE AUTOMATIQUE
# ===============================================================
# Description: Nettoyage automatique du conteneur Bronze
# Version: 2.0.0 - Utilisation directe du chemin Azure CLI
# Author: E7 Data Engineering Team
# Date: 2025-10-30

# Configuration Azure Storage
$StorageAccount = "datalakeficp5647"
$ContainerName = "bronze"

# Chemin direct vers Azure CLI (après installation winget)
$AzPath = "${env:ProgramFiles}\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"

Write-Host "🧹🧹🧹 NETTOYAGE AUTOMATIQUE AZURE STORAGE BRONZE 🧹🧹🧹" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor DarkGray
Write-Host "🎯 SUPPRESSION: Tous les CSV dans historique_quotidien/" -ForegroundColor Red
Write-Host "📦 STORAGE: $StorageAccount" -ForegroundColor Gray
Write-Host "📁 CONTENEUR: $ContainerName" -ForegroundColor Gray
Write-Host "🤖 MODE: Automatique (structure mois/jours)" -ForegroundColor Yellow
Write-Host "="*80 -ForegroundColor DarkGray

# Vérification Azure CLI
Write-Host "`n🔍 Vérification d'Azure CLI..." -ForegroundColor Blue
if (Test-Path $AzPath) {
    Write-Host "✅ Azure CLI trouvé: $AzPath" -ForegroundColor Green
} else {
    # Essayer d'autres chemins possibles
    $AlternatePaths = @(
        "${env:ProgramFiles(x86)}\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
        "$env:LOCALAPPDATA\Programs\Microsoft\Azure CLI\az.cmd",
        "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
    )
    
    $AzFound = $false
    foreach ($Path in $AlternatePaths) {
        if (Test-Path $Path) {
            $AzPath = $Path
            $AzFound = $true
            Write-Host "✅ Azure CLI trouvé: $Path" -ForegroundColor Green
            break
        }
    }
    
    if (-not $AzFound) {
        Write-Host "❌ Azure CLI non trouvé après installation" -ForegroundColor Red
        Write-Host "💡 Redémarrer PowerShell puis relancer ce script" -ForegroundColor Yellow
        exit 1
    }
}

# Test de version
try {
    $Version = & $AzPath --version 2>$null | Select-Object -First 1
    Write-Host "📊 Version Azure CLI: $Version" -ForegroundColor Gray
} catch {
    Write-Host "⚠️ Erreur test version Azure CLI" -ForegroundColor Yellow
}

# Connexion Azure (si pas déjà connecté)
Write-Host "`n🔐 Vérification connexion Azure..." -ForegroundColor Blue
try {
    $Account = & $AzPath account show --output json 2>$null | ConvertFrom-Json
    if ($Account) {
        Write-Host "✅ Connecté à Azure: $($Account.name)" -ForegroundColor Green
        Write-Host "📧 Utilisateur: $($Account.user.name)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Non connecté à Azure" -ForegroundColor Red
        Write-Host "🔐 Lancement de la connexion..." -ForegroundColor Yellow
        & $AzPath login
        
        # Vérifier à nouveau
        $Account = & $AzPath account show --output json 2>$null | ConvertFrom-Json
        if (-not $Account) {
            Write-Host "❌ Échec de connexion Azure" -ForegroundColor Red
            exit 1
        }
        Write-Host "✅ Connexion réussie !" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Erreur connexion Azure: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Analyse du conteneur
Write-Host "`n📊 Analyse du conteneur Bronze..." -ForegroundColor Blue
try {
    Write-Host "🔍 Recherche des fichiers CSV..." -ForegroundColor Gray
    
    $BlobListJson = & $AzPath storage blob list `
        --account-name $StorageAccount `
        --container-name $ContainerName `
        --prefix "historique_quotidien/" `
        --query "[?ends_with(name, '.csv')]" `
        --output json 2>$null
    
    if ($BlobListJson) {
        $BlobList = $BlobListJson | ConvertFrom-Json
        
        if ($BlobList -and $BlobList.Count -gt 0) {
            Write-Host "📊 FICHIERS CSV TROUVÉS: $($BlobList.Count)" -ForegroundColor Yellow
            
            # Analyse par type
            $ConsultationsFiles = @($BlobList | Where-Object { $_.name -like "*consultation*" })
            $InscriptionsFiles = @($BlobList | Where-Object { $_.name -like "*inscription*" })  
            $RadiationsFiles = @($BlobList | Where-Object { $_.name -like "*radiation*" })
            
            Write-Host "  📋 Consultations: $($ConsultationsFiles.Count) fichiers" -ForegroundColor Gray
            Write-Host "  📋 Inscriptions: $($InscriptionsFiles.Count) fichiers" -ForegroundColor Gray
            Write-Host "  📋 Radiations: $($RadiationsFiles.Count) fichiers" -ForegroundColor Gray
            
            # Taille totale
            $TotalSize = ($BlobList | Measure-Object -Property contentLength -Sum).Sum
            $TotalSizeMB = [math]::Round($TotalSize / 1MB, 2)
            Write-Host "  💾 Taille totale: $TotalSizeMB MB" -ForegroundColor Gray
            
        } else {
            Write-Host "✅ Aucun fichier CSV dans le conteneur Bronze" -ForegroundColor Green
            Write-Host "🎉 Conteneur déjà propre !" -ForegroundColor Green
            exit 0
        }
    } else {
        Write-Host "✅ Conteneur Bronze vide ou pas de CSV" -ForegroundColor Green
        exit 0
    }
    
} catch {
    Write-Host "❌ Erreur analyse conteneur: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Confirmation
Write-Host "`n" + "="*60 -ForegroundColor Red
Write-Host "⚠️ SUPPRESSION AUTOMATIQUE DES FICHIERS AZURE !" -ForegroundColor Red
Write-Host "="*60 -ForegroundColor Red
Write-Host "📦 Storage: $StorageAccount" -ForegroundColor Yellow
Write-Host "📁 Conteneur: $ContainerName" -ForegroundColor Yellow
Write-Host "🗑️ Fichiers: $($BlobList.Count) CSV à supprimer" -ForegroundColor Yellow
Write-Host "💾 Taille: $TotalSizeMB MB à libérer" -ForegroundColor Yellow
Write-Host "🤖 Méthode: Suppression automatique en lot" -ForegroundColor Yellow
Write-Host "="*60 -ForegroundColor Red

$Confirmation = Read-Host "🚨 Confirmer SUPPRESSION AUTOMATIQUE ? (OUI pour confirmer)"
if ($Confirmation.ToUpper() -ne "OUI") {
    Write-Host "❌ Nettoyage annulé" -ForegroundColor Yellow
    exit 0
}

# Suppression en lot
Write-Host "`n🗑️ SUPPRESSION AUTOMATIQUE EN COURS..." -ForegroundColor Red
$StartTime = Get-Date
$FilesDeleted = 0
$ErrorCount = 0

# Supprimer par batch pour éviter les timeouts
$BatchSize = 10
$TotalBatches = [math]::Ceiling($BlobList.Count / $BatchSize)

for ($batch = 0; $batch -lt $TotalBatches; $batch++) {
    $StartIndex = $batch * $BatchSize
    $EndIndex = [math]::Min($StartIndex + $BatchSize - 1, $BlobList.Count - 1)
    $CurrentBatch = $BlobList[$StartIndex..$EndIndex]
    
    Write-Host "🔄 Batch $($batch + 1)/$TotalBatches : Suppression $($CurrentBatch.Count) fichiers..." -ForegroundColor Gray
    
    foreach ($Blob in $CurrentBatch) {
        try {
            & $AzPath storage blob delete `
                --account-name $StorageAccount `
                --container-name $ContainerName `
                --name $Blob.name `
                --output none 2>$null
            
            $FilesDeleted++
            
        } catch {
            Write-Host "  ❌ Erreur: $($Blob.name)" -ForegroundColor Red
            $ErrorCount++
        }
    }
    
    $PercentComplete = [math]::Round((($batch + 1) / $TotalBatches) * 100, 1)
    Write-Host "  ✅ Batch terminé - Progression: $PercentComplete%" -ForegroundColor Green
    
    # Pause courte entre les batches
    Start-Sleep -Milliseconds 500
}

# Vérification finale
Write-Host "`n🔍 Vérification finale..." -ForegroundColor Blue
try {
    $RemainingBlobsJson = & $AzPath storage blob list `
        --account-name $StorageAccount `
        --container-name $ContainerName `
        --prefix "historique_quotidien/" `
        --query "[?ends_with(name, '.csv')]" `
        --output json 2>$null
    
    if ($RemainingBlobsJson) {
        $RemainingBlobs = $RemainingBlobsJson | ConvertFrom-Json
        
        if ($RemainingBlobs -and $RemainingBlobs.Count -gt 0) {
            Write-Host "⚠️ $($RemainingBlobs.Count) fichiers CSV restants" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Conteneur Bronze complètement nettoyé !" -ForegroundColor Green
        }
    } else {
        Write-Host "✅ Conteneur Bronze complètement nettoyé !" -ForegroundColor Green
    }
    
} catch {
    Write-Host "⚠️ Erreur vérification finale" -ForegroundColor Yellow
}

# Statistiques finales
$EndTime = Get-Date
$Duration = $EndTime - $StartTime

Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "🎊 NETTOYAGE AUTOMATIQUE AZURE TERMINÉ !" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green
Write-Host "🗑️ Fichiers supprimés: $FilesDeleted / $($BlobList.Count)" -ForegroundColor Cyan
Write-Host "❌ Erreurs: $ErrorCount" -ForegroundColor $(if($ErrorCount -eq 0){"Green"}else{"Red"})
Write-Host "💾 Espace libéré: $TotalSizeMB MB" -ForegroundColor Cyan
Write-Host "⏱️ Durée: $($Duration.ToString('mm\:ss'))" -ForegroundColor Cyan
Write-Host "🤖 Batches traités: $TotalBatches" -ForegroundColor Gray

if ($FilesDeleted -eq $BlobList.Count -and $ErrorCount -eq 0) {
    Write-Host "✅ NETTOYAGE PARFAITEMENT RÉUSSI !" -ForegroundColor Green
    Write-Host "🚀 Conteneur Bronze prêt pour l'import massif !" -ForegroundColor Yellow
    Write-Host "💰 Prêt à utiliser les 200€ de crédits Azure gratuits !" -ForegroundColor Green
} else {
    Write-Host "⚠️ NETTOYAGE PARTIEL - $ErrorCount erreurs" -ForegroundColor Yellow
}

Write-Host "="*80 -ForegroundColor Green