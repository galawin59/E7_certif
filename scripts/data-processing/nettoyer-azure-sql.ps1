# E7 CERTIFICATION - NETTOYAGE AZURE SQL DATABASE
# ===============================================
# Description: Nettoyage complet des tables Azure avant import massif
# Version: 1.0.0 - PowerShell Edition
# Author: E7 Data Engineering Team
# Date: 2025-10-30

# Configuration Azure SQL
$ServerInstance = 'sql-server-ficp-5647.database.windows.net'
$Database = 'db-ficp-datawarehouse'
$Username = 'ficpadmin'
$Password = 'FicpDataWarehouse2025!'

Write-Host "🧹🧹🧹 NETTOYAGE COMPLET AZURE SQL DATABASE 🧹🧹🧹" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor DarkGray
Write-Host "⚠️ SUPPRESSION DE TOUTES LES DONNÉES EXISTANTES" -ForegroundColor Red
Write-Host "🎯 Préparation pour import massif des 264,451 nouveaux enregistrements" -ForegroundColor Yellow
Write-Host "💰 Optimisation pour utilisation des crédits Azure gratuits" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor DarkGray

# Tables à nettoyer
$Tables = @('ConsultationsFICP', 'InscriptionsFICP', 'RadiationsFICP')

# 1. Test de connexion
Write-Host "`n🔍 Test de connexion Azure SQL..." -ForegroundColor Blue
try {
    $TestQuery = "SELECT @@VERSION"
    $Result = Invoke-Sqlcmd -ServerInstance $ServerInstance -Database $Database -Username $Username -Password $Password -Query $TestQuery
    Write-Host "✅ Connexion Azure SQL réussie" -ForegroundColor Green
    Write-Host "📊 Version: $($Result.Column1.Substring(0,80))..." -ForegroundColor Gray
} catch {
    Write-Host "❌ Erreur connexion Azure SQL: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Comptage avant nettoyage
Write-Host "`n📊 Comptage des enregistrements existants..." -ForegroundColor Blue
$StatsAvant = @{}
$TotalAvant = 0

foreach ($Table in $Tables) {
    try {
        $CountQuery = "SELECT COUNT(*) as Total FROM $Table"
        $Result = Invoke-Sqlcmd -ServerInstance $ServerInstance -Database $Database -Username $Username -Password $Password -Query $CountQuery
        $Count = $Result.Total
        $StatsAvant[$Table] = $Count
        $TotalAvant += $Count
        Write-Host "  📋 $Table`: $($Count.ToString('N0')) enregistrements" -ForegroundColor Gray
    } catch {
        Write-Host "  ⚠️ Erreur comptage $Table`: $($_.Exception.Message)" -ForegroundColor Yellow
        $StatsAvant[$Table] = 0
    }
}

Write-Host "📊 TOTAL AVANT NETTOYAGE: $($TotalAvant.ToString('N0')) enregistrements" -ForegroundColor Cyan

if ($TotalAvant -eq 0) {
    Write-Host "✅ Tables déjà vides - Pas de nettoyage nécessaire" -ForegroundColor Green
    exit 0
}

# 3. Confirmation
Write-Host "`n" + "="*60 -ForegroundColor Red
Write-Host "⚠️ ATTENTION: SUPPRESSION DÉFINITIVE DES DONNÉES !" -ForegroundColor Red
Write-Host "="*60 -ForegroundColor Red
foreach ($Table in $Tables) {
    $Count = $StatsAvant[$Table]
    Write-Host "  🗑️ $Table`: $($Count.ToString('N0')) enregistrements seront SUPPRIMÉS" -ForegroundColor Yellow
}
Write-Host "="*60 -ForegroundColor Red

$Confirmation = Read-Host "🚨 Confirmer la SUPPRESSION TOTALE ? (SUPPRIMER pour confirmer)"
if ($Confirmation -ne "SUPPRIMER") {
    Write-Host "❌ Nettoyage annulé par l'utilisateur" -ForegroundColor Yellow
    exit 0
}

# 4. Nettoyage table par table
Write-Host "`n🧹 DÉBUT DU NETTOYAGE..." -ForegroundColor Cyan
$StartTime = Get-Date
$TotalSupprime = 0

foreach ($Table in $Tables) {
    Write-Host "`n🧹 Nettoyage de la table $Table..." -ForegroundColor Blue
    
    try {
        # Suppression des données
        $DeleteQuery = "DELETE FROM $Table"
        Invoke-Sqlcmd -ServerInstance $ServerInstance -Database $Database -Username $Username -Password $Password -Query $DeleteQuery
        
        $RowsDeleted = $StatsAvant[$Table]
        $TotalSupprime += $RowsDeleted
        
        # Remise à zéro du compteur IDENTITY
        $ReseedQuery = "DBCC CHECKIDENT('$Table', RESEED, 0)"
        Invoke-Sqlcmd -ServerInstance $ServerInstance -Database $Database -Username $Username -Password $Password -Query $ReseedQuery
        
        Write-Host "  ✅ $Table`: $($RowsDeleted.ToString('N0')) enregistrements supprimés" -ForegroundColor Green
        Write-Host "  🔄 $Table`: Compteur IDENTITY remis à zéro" -ForegroundColor Green
        
    } catch {
        Write-Host "  ❌ Erreur nettoyage $Table`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 5. Vérification finale
Write-Host "`n🔍 Vérification après nettoyage..." -ForegroundColor Blue
$VerificationOK = $true

foreach ($Table in $Tables) {
    try {
        $CountQuery = "SELECT COUNT(*) as Total FROM $Table"
        $Result = Invoke-Sqlcmd -ServerInstance $ServerInstance -Database $Database -Username $Username -Password $Password -Query $CountQuery
        $Count = $Result.Total
        
        if ($Count -eq 0) {
            Write-Host "  ✅ $Table`: VIDE (OK)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $Table`: $Count enregistrements restants !" -ForegroundColor Red
            $VerificationOK = $false
        }
    } catch {
        Write-Host "  ❌ Erreur vérification $Table`: $($_.Exception.Message)" -ForegroundColor Red
        $VerificationOK = $false
    }
}

# 6. Statistiques finales
$EndTime = Get-Date
$Duration = $EndTime - $StartTime

Write-Host "`n" + "="*80 -ForegroundColor Green
if ($VerificationOK) {
    Write-Host "🎊 NETTOYAGE COMPLET TERMINÉ !" -ForegroundColor Green
} else {
    Write-Host "⚠️ NETTOYAGE TERMINÉ AVEC ERREURS !" -ForegroundColor Yellow
}
Write-Host "="*80 -ForegroundColor Green
Write-Host "🗑️ Enregistrements supprimés: $($TotalSupprime.ToString('N0'))" -ForegroundColor Cyan
Write-Host "📊 Tables nettoyées: $($Tables.Count)" -ForegroundColor Cyan
Write-Host "⏱️ Durée: $($Duration.ToString('mm\:ss'))" -ForegroundColor Cyan
if ($VerificationOK) {
    Write-Host "✅ Base de données prête pour import massif des 264,451 nouveaux enregistrements" -ForegroundColor Green
    Write-Host "🚀 Prochaine étape: Lancer import-massif-azure-historique.py" -ForegroundColor Yellow
}
Write-Host "="*80 -ForegroundColor Green