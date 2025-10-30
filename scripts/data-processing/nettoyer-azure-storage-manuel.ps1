# E7 CERTIFICATION - NETTOYAGE AZURE STORAGE BRONZE (SANS AZURE CLI)
# ===================================================================
# Description: Nettoyage du conteneur Bronze via REST API
# Version: 1.0.0 - PowerShell REST Edition  
# Author: E7 Data Engineering Team
# Date: 2025-10-30

# Configuration
$StorageAccount = "datalakeficp5647"
$ContainerName = "bronze"

Write-Host "🧹🧹🧹 NETTOYAGE AZURE STORAGE BRONZE 🧹🧹🧹" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor DarkGray
Write-Host "🎯 OBJECTIF: Nettoyer le conteneur Bronze sur Azure Storage" -ForegroundColor Yellow
Write-Host "📦 STORAGE: $StorageAccount" -ForegroundColor Gray
Write-Host "📁 CONTENEUR: $ContainerName" -ForegroundColor Gray
Write-Host "⚠️ MÉTHODE: Azure Portal manuel (Azure CLI non disponible)" -ForegroundColor Yellow
Write-Host "="*80 -ForegroundColor DarkGray

Write-Host "`n❌ AZURE CLI NON INSTALLÉ" -ForegroundColor Red
Write-Host "="*40 -ForegroundColor Red

Write-Host "`n🎯 SOLUTION MANUELLE VIA AZURE PORTAL:" -ForegroundColor Yellow
Write-Host "="*50 -ForegroundColor Yellow

Write-Host "1️⃣ Ouvrir Azure Portal: https://portal.azure.com" -ForegroundColor White
Write-Host "2️⃣ Aller sur Storage Account: $StorageAccount" -ForegroundColor White
Write-Host "3️⃣ Cliquer sur 'Containers'" -ForegroundColor White
Write-Host "4️⃣ Ouvrir le conteneur: $ContainerName" -ForegroundColor White
Write-Host "5️⃣ Naviguer vers: historique_quotidien/" -ForegroundColor White
Write-Host "6️⃣ Sélectionner TOUS les fichiers .csv" -ForegroundColor White
Write-Host "7️⃣ Cliquer 'Delete' pour supprimer" -ForegroundColor White

Write-Host "`n🚀 ALTERNATIVE: INSTALLATION AZURE CLI" -ForegroundColor Green
Write-Host "="*50 -ForegroundColor Green

Write-Host "Option A - Via winget:" -ForegroundColor White
Write-Host "  winget install Microsoft.AzureCLI" -ForegroundColor Gray

Write-Host "`nOption B - Via MSI:" -ForegroundColor White
Write-Host "  https://aka.ms/installazurecliwindows" -ForegroundColor Gray

Write-Host "`nOption C - Via PowerShell:" -ForegroundColor White
Write-Host "  Invoke-WebRequest -Uri https://aka.ms/installazurecliwindows -OutFile AzureCLI.msi" -ForegroundColor Gray
Write-Host "  Start-Process msiexec.exe -Wait -ArgumentList '/I AzureCLI.msi /quiet'" -ForegroundColor Gray

Write-Host "`n🔄 APRÈS INSTALLATION AZURE CLI:" -ForegroundColor Yellow
Write-Host "1️⃣ Redémarrer PowerShell" -ForegroundColor White
Write-Host "2️⃣ Lancer: az login" -ForegroundColor White
Write-Host "3️⃣ Relancer: .\scripts\data-processing\nettoyer-azure-storage-bronze.ps1" -ForegroundColor White

Write-Host "`n📋 FICHIERS À SUPPRIMER MANUELLEMENT:" -ForegroundColor Cyan
Write-Host "="*50 -ForegroundColor Cyan
Write-Host "📁 historique_quotidien/consultations/*.csv" -ForegroundColor Gray
Write-Host "📁 historique_quotidien/inscriptions/*.csv" -ForegroundColor Gray  
Write-Host "📁 historique_quotidien/radiations/*.csv" -ForegroundColor Gray

Write-Host "`n💡 CONSEIL:" -ForegroundColor Green
Write-Host "Dans Azure Portal, tu peux sélectionner plusieurs fichiers" -ForegroundColor White
Write-Host "en maintenant Ctrl et en cliquant sur chaque fichier," -ForegroundColor White
Write-Host "puis cliquer 'Delete' pour supprimer en lot." -ForegroundColor White

Write-Host "`n✅ OBJECTIF FINAL:" -ForegroundColor Green
Write-Host "Conteneur Bronze vide et prêt pour les nouveaux" -ForegroundColor White
Write-Host "fichiers cohérents avec conformité réglementaire!" -ForegroundColor White

Write-Host "`n" + "="*80 -ForegroundColor DarkGray
Write-Host "🎯 Une fois le nettoyage Azure terminé, on pourra lancer" -ForegroundColor Yellow
Write-Host "l'import massif des 264,451 nouveaux enregistrements!" -ForegroundColor Yellow
Write-Host "="*80 -ForegroundColor DarkGray