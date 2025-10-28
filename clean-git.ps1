# ===============================
# SCRIPT DE NETTOYAGE GIT - SUPPRESSION CSV
# ===============================

# Ce script supprime les fichiers CSV du tracking Git tout en les conservant localement

Write-Host "🧹 NETTOYAGE DES FICHIERS CSV DU REPOSITORY GIT" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

$projectRoot = "c:\Users\Galawin\Documents\GitHub\E7_certif"
Set-Location $projectRoot

# Vérifier si Git est disponible
try {
    git --version | Out-Null
    Write-Host "✅ Git détecté" -ForegroundColor Green
} catch {
    Write-Host "❌ Git non trouvé. Installez Git depuis: https://git-scm.com/" -ForegroundColor Red
    exit 1
}

Write-Host "`n📋 Fichiers CSV actuellement trackés par Git:" -ForegroundColor Yellow

# Lister les fichiers CSV trackés
$csvFiles = git ls-files "*.csv" 2>$null
$csvFilesData = git ls-files "DataLakeE7/*.csv" "DataLakeE7/ficp_data/*.csv" 2>$null

if ($csvFiles -or $csvFilesData) {
    Write-Host "Fichiers CSV trouvés dans Git:" -ForegroundColor Cyan
    $csvFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Cyan }
    $csvFilesData | ForEach-Object { Write-Host "  - $_" -ForegroundColor Cyan }
    
    Write-Host "`n⚠️  Ces fichiers vont être supprimés du tracking Git (mais conservés localement)" -ForegroundColor Yellow
    Write-Host "Continuer? (O/N): " -NoNewline
    $confirmation = Read-Host
    
    if ($confirmation -eq "O" -or $confirmation -eq "o" -or $confirmation -eq "Y" -or $confirmation -eq "y") {
        
        Write-Host "`n🗑️  Suppression des fichiers CSV du tracking Git..." -ForegroundColor Yellow
        
        # Supprimer du tracking Git sans supprimer les fichiers locaux
        git rm --cached "DataLakeE7/*.csv" 2>$null
        git rm --cached "DataLakeE7/ficp_data/*.csv" 2>$null
        git rm --cached "*.csv" 2>$null
        
        # Forcer la suppression avec pattern recursif
        Get-ChildItem -Path . -Recurse -Name "DataLakeE7\*.csv" | ForEach-Object {
            git rm --cached $_ 2>$null
        }
        
        Write-Host "✅ Fichiers CSV supprimés du tracking Git" -ForegroundColor Green
        
        # Vérifier le gitignore
        if (Test-Path ".gitignore") {
            $gitignoreContent = Get-Content ".gitignore" -Raw
            if ($gitignoreContent -match "\*\.csv") {
                Write-Host "✅ .gitignore déjà configuré pour ignorer les CSV" -ForegroundColor Green
            } else {
                Write-Host "⚠️  .gitignore ne semble pas configuré correctement" -ForegroundColor Yellow
            }
        }
        
        # Afficher le status Git
        Write-Host "`n📊 Status Git après nettoyage:" -ForegroundColor Yellow
        git status --porcelain | Where-Object { $_ -match "\.csv" } | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Cyan
        }
        
        Write-Host "`n🎯 Prochaines étapes:" -ForegroundColor Yellow
        Write-Host "1. Commitez les modifications: git add .gitignore && git commit -m 'Add CSV files to gitignore'" -ForegroundColor Cyan
        Write-Host "2. Vos fichiers CSV sont toujours présents localement" -ForegroundColor Cyan
        Write-Host "3. Les futurs CSV seront automatiquement ignorés" -ForegroundColor Cyan
        
    } else {
        Write-Host "🚫 Nettoyage annulé par l'utilisateur" -ForegroundColor Yellow
    }
    
} else {
    Write-Host "✅ Aucun fichier CSV trouvé dans le tracking Git" -ForegroundColor Green
    Write-Host "Le .gitignore fonctionne correctement!" -ForegroundColor Green
}

# Vérifier la taille du repository
Write-Host "`n📏 Taille du repository:" -ForegroundColor Yellow
$gitSize = (Get-ChildItem -Path ".git" -Recurse -Force | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Repository Git: $([math]::Round($gitSize, 2)) MB" -ForegroundColor Cyan

$csvSize = (Get-ChildItem -Path . -Recurse -Include "*.csv" -Force | Measure-Object -Property Length -Sum).Sum / 1MB
if ($csvSize -gt 0) {
    Write-Host "Fichiers CSV (ignorés): $([math]::Round($csvSize, 2)) MB" -ForegroundColor Cyan
    Write-Host "💰 Espace économisé en ignorant les CSV!" -ForegroundColor Green
}

Write-Host "`n🏁 NETTOYAGE TERMINÉ" -ForegroundColor Green