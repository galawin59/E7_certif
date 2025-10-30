# E7 CERTIFICATION - NETTOYAGE AZURE STORAGE BRONZE
# ==================================================
# Description: Nettoyage complet du conteneur Bronze sur Azure Storage
# Version: 1.0.0 - PowerShell Edition
# Author: E7 Data Engineering Team
# Date: 2025-10-30

# Configuration Azure Storage
$StorageAccount = "datalakeficp5647"
$ContainerName = "bronze"
$ResourceGroup = "rg-ficp-datawarehouse"

Write-Host "🧹🧹🧹 NETTOYAGE AZURE STORAGE BRONZE 🧹🧹🧹" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor DarkGray
Write-Host "🎯 OBJECTIF: Supprimer tous les anciens CSV du conteneur Bronze" -ForegroundColor Yellow
Write-Host "📦 STORAGE ACCOUNT: $StorageAccount" -ForegroundColor Gray
Write-Host "📁 CONTENEUR: $ContainerName" -ForegroundColor Gray
Write-Host "🗑️ SUPPRESSION: Tous les fichiers .csv dans historique_quotidien/" -ForegroundColor Red
Write-Host "="*80 -ForegroundColor DarkGray

# Vérification de la connexion Azure
Write-Host "`n🔍 Vérification de la connexion Azure..." -ForegroundColor Blue
try {
    $Account = az account show --output json | ConvertFrom-Json
    if ($Account) {
        Write-Host "✅ Connecté à Azure: $($Account.name)" -ForegroundColor Green
        Write-Host "📧 Utilisateur: $($Account.user.name)" -ForegroundColor Gray
    } else {
        Write-Host "❌ Non connecté à Azure - Connexion requise" -ForegroundColor Red
        Write-Host "💡 Lancer: az login" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Erreur vérification Azure: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Azure CLI requis - Installer: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    exit 1
}

# Listage des fichiers existants
Write-Host "`n📊 Analyse du conteneur Bronze..." -ForegroundColor Blue
try {
    Write-Host "🔍 Recherche des fichiers CSV dans $ContainerName/historique_quotidien/..." -ForegroundColor Gray
    
    # Lister tous les blobs CSV dans le préfixe historique_quotidien
    $BlobList = az storage blob list `
        --account-name $StorageAccount `
        --container-name $ContainerName `
        --prefix "historique_quotidien/" `
        --query "[?ends_with(name, '.csv')]" `
        --output json | ConvertFrom-Json
    
    if ($BlobList -and $BlobList.Count -gt 0) {
        Write-Host "📊 FICHIERS CSV TROUVÉS: $($BlobList.Count)" -ForegroundColor Yellow
        
        # Grouper par type
        $ConsultationsFiles = $BlobList | Where-Object { $_.name -like "*consultation*" }
        $InscriptionsFiles = $BlobList | Where-Object { $_.name -like "*inscription*" }
        $RadiationsFiles = $BlobList | Where-Object { $_.name -like "*radiation*" }
        
        Write-Host "  📋 Consultations: $($ConsultationsFiles.Count) fichiers" -ForegroundColor Gray
        Write-Host "  📋 Inscriptions: $($InscriptionsFiles.Count) fichiers" -ForegroundColor Gray
        Write-Host "  📋 Radiations: $($RadiationsFiles.Count) fichiers" -ForegroundColor Gray
        
        # Calculer la taille totale
        $TotalSize = ($BlobList | Measure-Object -Property contentLength -Sum).Sum
        $TotalSizeMB = [math]::Round($TotalSize / 1MB, 2)
        Write-Host "  💾 Taille totale: $TotalSizeMB MB" -ForegroundColor Gray
        
    } else {
        Write-Host "✅ Aucun fichier CSV trouvé dans le conteneur Bronze" -ForegroundColor Green
        Write-Host "🎉 Conteneur déjà propre !" -ForegroundColor Green
        exit 0
    }
    
} catch {
    Write-Host "❌ Erreur lors de l'analyse: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Confirmation de suppression
Write-Host "`n" + "="*60 -ForegroundColor Red
Write-Host "⚠️ ATTENTION: SUPPRESSION DÉFINITIVE DES FICHIERS AZURE !" -ForegroundColor Red
Write-Host "="*60 -ForegroundColor Red
Write-Host "📦 Storage Account: $StorageAccount" -ForegroundColor Yellow
Write-Host "📁 Conteneur: $ContainerName" -ForegroundColor Yellow
Write-Host "🗑️ Fichiers à supprimer: $($BlobList.Count) CSV" -ForegroundColor Yellow
Write-Host "💾 Taille à libérer: $TotalSizeMB MB" -ForegroundColor Yellow
Write-Host "="*60 -ForegroundColor Red
Write-Host "✅ CONSERVATION: Structure des dossiers (vides)" -ForegroundColor Green
Write-Host "🚀 PRÉPARATION: Pour nouveaux fichiers cohérents" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Red

$Confirmation = Read-Host "🚨 Confirmer la SUPPRESSION des $($BlobList.Count) fichiers ? (SUPPRIMER pour confirmer)"
if ($Confirmation -ne "SUPPRIMER") {
    Write-Host "❌ Nettoyage Azure Storage annulé par l'utilisateur" -ForegroundColor Yellow
    exit 0
}

# Suppression des fichiers
Write-Host "`n🗑️ DÉBUT DE LA SUPPRESSION..." -ForegroundColor Red
$StartTime = Get-Date
$FilesDeleted = 0
$ErrorCount = 0

foreach ($Blob in $BlobList) {
    try {
        Write-Progress -Activity "Suppression fichiers Azure Storage" -Status "Suppression: $($Blob.name)" -PercentComplete (($FilesDeleted / $BlobList.Count) * 100)
        
        az storage blob delete `
            --account-name $StorageAccount `
            --container-name $ContainerName `
            --name $Blob.name `
            --output none
        
        $FilesDeleted++
        
        if ($FilesDeleted % 50 -eq 0) {
            Write-Host "  🗑️ $FilesDeleted / $($BlobList.Count) fichiers supprimés..." -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "  ❌ Erreur suppression $($Blob.name): $($_.Exception.Message)" -ForegroundColor Red
        $ErrorCount++
    }
}

Write-Progress -Activity "Suppression fichiers Azure Storage" -Completed

# Vérification finale
Write-Host "`n🔍 Vérification après suppression..." -ForegroundColor Blue
try {
    $RemainingBlobs = az storage blob list `
        --account-name $StorageAccount `
        --container-name $ContainerName `
        --prefix "historique_quotidien/" `
        --query "[?ends_with(name, '.csv')]" `
        --output json | ConvertFrom-Json
    
    if ($RemainingBlobs -and $RemainingBlobs.Count -gt 0) {
        Write-Host "⚠️ $($RemainingBlobs.Count) fichiers CSV restants" -ForegroundColor Yellow
        foreach ($Remaining in $RemainingBlobs) {
            Write-Host "  📄 $($Remaining.name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "✅ Aucun fichier CSV restant dans le conteneur Bronze" -ForegroundColor Green
    }
    
} catch {
    Write-Host "⚠️ Erreur lors de la vérification finale: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Statistiques finales
$EndTime = Get-Date
$Duration = $EndTime - $StartTime

Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "🎊 NETTOYAGE AZURE STORAGE BRONZE TERMINÉ !" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green
Write-Host "🗑️ Fichiers supprimés: $FilesDeleted / $($BlobList.Count)" -ForegroundColor Cyan
Write-Host "❌ Erreurs: $ErrorCount" -ForegroundColor $(if($ErrorCount -eq 0){"Green"}else{"Red"})
Write-Host "💾 Espace libéré: $TotalSizeMB MB" -ForegroundColor Cyan
Write-Host "⏱️ Durée: $($Duration.ToString('mm\:ss'))" -ForegroundColor Cyan
Write-Host "📦 Storage Account: $StorageAccount" -ForegroundColor Gray
Write-Host "📁 Conteneur: $ContainerName (Bronze layer)" -ForegroundColor Gray

if ($FilesDeleted -eq $BlobList.Count -and $ErrorCount -eq 0) {
    Write-Host "✅ NETTOYAGE AZURE PARFAITEMENT RÉUSSI !" -ForegroundColor Green
    Write-Host "🚀 Conteneur Bronze prêt pour nouveaux fichiers cohérents" -ForegroundColor Yellow
} else {
    Write-Host "⚠️ NETTOYAGE PARTIEL - Vérifier les erreurs ci-dessus" -ForegroundColor Yellow
}

Write-Host "="*80 -ForegroundColor Green