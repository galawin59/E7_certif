# ==============================================================================
# E7 CERTIFICATION - INSTALLATION ET CONFIGURATION AUTOMATISÉE
# Projet : Azure Data Engineer - Architecture Medallion avec SQL Database
# Version : 1.0 Production
# Date : 29 Octobre 2025
# ==============================================================================

param(
    [Parameter(HelpMessage="Mode d'exécution: 'setup', 'deploy', 'import', 'validate', 'all'")]
    [ValidateSet("setup", "deploy", "import", "validate", "all")]
    [string]$Mode = "all",
    
    [Parameter(HelpMessage="Ignorer les vérifications de prérequis")]
    [switch]$SkipPrerequisites,
    
    [Parameter(HelpMessage="Mode silencieux sans interaction utilisateur")]
    [switch]$Silent
)

# ==============================================================================
# CONFIGURATION GLOBALE
# ==============================================================================

$Global:ProjectConfig = @{
    Name = "E7_Certification_Azure_Data_Engineer"
    Version = "1.0.0"
    Environment = "Production"
    AzureRegion = "France Central"
    ResourceGroupName = "rg-datalake-ficp"
    StorageAccountName = "ficpstorageaccount"
    DataFactoryName = "df-ficp"
    SqlServerName = "sql-server-ficp-5647"
    DatabaseName = "db-ficp-datawarehouse"
    AdminLogin = "ficpadmin"
}

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

function Write-Header {
    param([string]$Title, [string]$Color = "Cyan")
    
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor $Color
    Write-Host "   $Title" -ForegroundColor Yellow
    Write-Host ("=" * 80) -ForegroundColor $Color
    Write-Host ""
}

function Write-Step {
    param([string]$Message, [string]$Status = "Info")
    
    $icon = switch ($Status) {
        "Success" { "✅" }
        "Error" { "❌" }
        "Warning" { "⚠️" }
        "Info" { "ℹ️" }
        "Process" { "🔄" }
        default { "📋" }
    }
    
    $color = switch ($Status) {
        "Success" { "Green" }
        "Error" { "Red" }
        "Warning" { "Yellow" }
        "Info" { "Cyan" }
        "Process" { "Magenta" }
        default { "White" }
    }
    
    Write-Host "$icon $Message" -ForegroundColor $color
}

function Test-Prerequisites {
    Write-Header "VÉRIFICATION DES PRÉREQUIS"
    
    $prerequisites = @()
    
    # Vérification PowerShell
    if ($PSVersionTable.PSVersion.Major -ge 5) {
        Write-Step "PowerShell version $($PSVersionTable.PSVersion) ✓" "Success"
    } else {
        Write-Step "PowerShell version insuffisante (requis: 5.0+)" "Error"
        $prerequisites += "PowerShell 5.0+"
    }
    
    # Vérification Python
    try {
        $pythonVersion = & python --version 2>&1
        if ($pythonVersion -match "Python 3\.\d+") {
            Write-Step "Python détecté: $pythonVersion ✓" "Success"
        } else {
            Write-Step "Python 3.x requis" "Error"
            $prerequisites += "Python 3.x"
        }
    } catch {
        Write-Step "Python non installé" "Error"
        $prerequisites += "Python 3.x"
    }
    
    # Vérification Azure PowerShell
    try {
        Import-Module Az -ErrorAction SilentlyContinue
        if (Get-Module Az -ListAvailable) {
            Write-Step "Module Azure PowerShell disponible ✓" "Success"
        } else {
            Write-Step "Module Azure PowerShell requis" "Warning"
            $prerequisites += "Azure PowerShell Module"
        }
    } catch {
        Write-Step "Module Azure PowerShell non installé" "Warning"
        $prerequisites += "Azure PowerShell Module"
    }
    
    # Vérification SQL Server Module
    try {
        Import-Module SqlServer -ErrorAction SilentlyContinue
        if (Get-Module SqlServer -ListAvailable) {
            Write-Step "Module SQL Server disponible ✓" "Success"
        } else {
            Write-Step "Module SQL Server requis" "Warning"
            $prerequisites += "SQL Server PowerShell Module"
        }
    } catch {
        Write-Step "Module SQL Server non installé" "Warning"
        $prerequisites += "SQL Server PowerShell Module"
    }
    
    if ($prerequisites.Count -gt 0 -and -not $SkipPrerequisites) {
        Write-Step "Prérequis manquants détectés:" "Warning"
        foreach ($prereq in $prerequisites) {
            Write-Host "   • $prereq" -ForegroundColor Yellow
        }
        
        if (-not $Silent) {
            $continue = Read-Host "Continuer malgré les prérequis manquants? (o/N)"
            if ($continue -ne "o" -and $continue -ne "O") {
                exit 1
            }
        }
    }
    
    return $prerequisites.Count -eq 0
}

function Install-PythonDependencies {
    Write-Header "INSTALLATION DES DÉPENDANCES PYTHON"
    
    # Activation environnement virtuel si existant
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        Write-Step "Activation de l'environnement virtuel" "Process"
        & .\.venv\Scripts\Activate.ps1
    }
    
    # Installation des packages requis
    $packages = @("pandas", "numpy", "pyodbc", "sqlalchemy", "faker", "schedule")
    
    foreach ($package in $packages) {
        try {
            Write-Step "Installation de $package..." "Process"
            & pip install $package --quiet
            Write-Step "$package installé ✓" "Success"
        } catch {
            Write-Step "Erreur installation $package" "Error"
        }
    }
}

function Install-PowerShellModules {
    Write-Header "INSTALLATION DES MODULES POWERSHELL"
    
    $modules = @(
        @{Name="Az"; Description="Azure PowerShell Module"},
        @{Name="SqlServer"; Description="SQL Server Management Module"}
    )
    
    foreach ($module in $modules) {
        try {
            if (-not (Get-Module $module.Name -ListAvailable)) {
                Write-Step "Installation de $($module.Description)..." "Process"
                Install-Module $module.Name -Force -AllowClobber -Scope CurrentUser -ErrorAction Stop
                Write-Step "$($module.Description) installé ✓" "Success"
            } else {
                Write-Step "$($module.Description) déjà disponible ✓" "Success"
            }
        } catch {
            Write-Step "Erreur installation $($module.Description): $($_.Exception.Message)" "Error"
        }
    }
}

function Deploy-AzureInfrastructure {
    Write-Header "DÉPLOIEMENT INFRASTRUCTURE AZURE"
    
    try {
        Write-Step "Exécution du script de déploiement Azure SQL..." "Process"
        & ".\scripts\deployment\deploy-azure-sql-complete.ps1"
        Write-Step "Infrastructure Azure déployée ✓" "Success"
    } catch {
        Write-Step "Erreur déploiement Azure: $($_.Exception.Message)" "Error"
        return $false
    }
    
    return $true
}

function Import-Data {
    Write-Header "IMPORT DES DONNÉES VERS AZURE SQL"
    
    try {
        Write-Step "Génération des données professionnelles..." "Process"
        & python "DataLakeE7\GenerateProfessionalData.py"
        
        Write-Step "Import vers Azure SQL Database..." "Process"
        & python "scripts\data-processing\import-azure-hybrid.py"
        
        Write-Step "Données importées avec succès ✓" "Success"
    } catch {
        Write-Step "Erreur import des données: $($_.Exception.Message)" "Error"
        return $false
    }
    
    return $true
}

function Validate-Installation {
    Write-Header "VALIDATION DE L'INSTALLATION"
    
    try {
        & ".\scripts\validation\validate-e7-final.ps1"
        Write-Step "Validation terminée ✓" "Success"
    } catch {
        Write-Step "Erreur validation: $($_.Exception.Message)" "Error"
        return $false
    }
    
    return $true
}

function Show-Summary {
    Write-Header "RÉSUMÉ DE L'INSTALLATION"
    
    Write-Step "📊 Projet E7 Certification configuré" "Success"
    Write-Step "🏗️ Infrastructure Azure déployée" "Success"
    Write-Step "🗃️ Base de données Azure SQL opérationnelle" "Success"
    Write-Step "📈 Données importées et validées" "Success"
    
    Write-Host ""
    Write-Host "🔗 Informations de connexion:" -ForegroundColor Cyan
    Write-Host "   Serveur: $($Global:ProjectConfig.SqlServerName).database.windows.net" -ForegroundColor Gray
    Write-Host "   Base: $($Global:ProjectConfig.DatabaseName)" -ForegroundColor Gray
    Write-Host "   Login: $($Global:ProjectConfig.AdminLogin)" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "📋 Prochaines étapes:" -ForegroundColor Yellow
    Write-Host "   1. Ouvrir Power BI Desktop" -ForegroundColor Gray
    Write-Host "   2. Se connecter à Azure SQL Database" -ForegroundColor Gray
    Write-Host "   3. Créer les visualisations métier" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "🎉 INSTALLATION E7 CERTIFICATION TERMINÉE AVEC SUCCÈS!" -ForegroundColor Green
}

# ==============================================================================
# SCRIPT PRINCIPAL
# ==============================================================================

Write-Header "E7 CERTIFICATION - AZURE DATA ENGINEER - INSTALLATION AUTOMATISÉE"

# Vérification des prérequis
if (-not $SkipPrerequisites) {
    $prereqsOk = Test-Prerequisites
}

# Exécution selon le mode choisi
switch ($Mode) {
    "setup" {
        Install-PowerShellModules
        Install-PythonDependencies
    }
    "deploy" {
        Deploy-AzureInfrastructure
    }
    "import" {
        Import-Data
    }
    "validate" {
        Validate-Installation
    }
    "all" {
        Install-PowerShellModules
        Install-PythonDependencies
        Deploy-AzureInfrastructure
        Import-Data
        Validate-Installation
        Show-Summary
    }
}

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "Installation terminée. Mode: $Mode" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Cyan