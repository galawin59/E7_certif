# ==============================================================================
# E7 CERTIFICATION - VALIDATION COMPLÈTE ET PROFESSIONNELLE
# ==============================================================================
# Description: Script de validation exhaustive du projet E7 Data Engineer
# Version: 1.0.0
# Author: E7 Data Engineering Team
# Date: 2025-10-29
# ==============================================================================

param(
    [Parameter(HelpMessage="Mode de validation détaillé")]
    [switch]$Detailed,
    
    [Parameter(HelpMessage="Export des résultats au format JSON")]
    [switch]$ExportResults,
    
    [Parameter(HelpMessage="Chemin de sortie pour l'export")]
    [string]$OutputPath = "validation-results.json"
)

# ==============================================================================
# CONFIGURATION GLOBALE
# ==============================================================================

$Global:ValidationConfig = @{
    ProjectName = "E7_Certification_Azure_Data_Engineer"
    Version = "1.0.0"
    ValidationDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    ServerName = "sql-server-ficp-5647.database.windows.net"
    DatabaseName = "db-ficp-datawarehouse"
    AdminLogin = "ficpadmin"
    AdminPassword = "FicpDataWarehouse2025!"
}

$Global:ValidationResults = @{
    Summary = @{
        TotalTests = 0
        PassedTests = 0
        FailedTests = 0
        WarningTests = 0
        OverallStatus = "Unknown"
    }
    Details = @{}
}

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

function Write-ValidationHeader {
    param([string]$Title)
    
    Write-Host ""
    Write-Host ("═" * 90) -ForegroundColor Cyan
    Write-Host ("   $Title").PadRight(90) -ForegroundColor Yellow
    Write-Host ("═" * 90) -ForegroundColor Cyan
}

function Write-TestResult {
    param(
        [string]$TestName,
        [string]$Status,
        [string]$Message = "",
        [string]$Details = ""
    )
    
    $Global:ValidationResults.Summary.TotalTests++
    
    $icon = switch ($Status) {
        "PASS" { "✅"; $Global:ValidationResults.Summary.PassedTests++ }
        "FAIL" { "❌"; $Global:ValidationResults.Summary.FailedTests++ }
        "WARN" { "⚠️"; $Global:ValidationResults.Summary.WarningTests++ }
        default { "ℹ️" }
    }
    
    $color = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "WARN" { "Yellow" }
        default { "Cyan" }
    }
    
    $testResult = @{
        Status = $Status
        Message = $Message
        Details = $Details
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
    
    $Global:ValidationResults.Details[$TestName] = $testResult
    
    Write-Host "$icon [$Status] $TestName" -ForegroundColor $color
    if ($Message) {
        Write-Host "    └─ $Message" -ForegroundColor Gray
    }
    if ($Detailed -and $Details) {
        Write-Host "    └─ Détails: $Details" -ForegroundColor DarkGray
    }
}

# ==============================================================================
# TESTS DE VALIDATION
# ==============================================================================

function Test-ProjectStructure {
    Write-ValidationHeader "VALIDATION STRUCTURE DU PROJET"
    
    $requiredFolders = @(
        "scripts",
        "scripts/deployment", 
        "scripts/data-processing",
        "scripts/validation",
        "config",
        "docs",
        "DataLakeE7",
        "DataLakeE7/bronze",
        "DataLakeE7/silver", 
        "DataLakeE7/gold",
        "DataLakeE7/logs"
    )
    
    foreach ($folder in $requiredFolders) {
        if (Test-Path $folder) {
            $fileCount = (Get-ChildItem $folder -Recurse -File -ErrorAction SilentlyContinue).Count
            Write-TestResult "Structure.$folder" "PASS" "$fileCount fichiers trouvés"
        } else {
            Write-TestResult "Structure.$folder" "FAIL" "Dossier manquant"
        }
    }
    
    $requiredFiles = @(
        "README.md",
        "Install-E7Certification.ps1",
        "config/project-config.json",
        "config/azure-schema.sql",
        "scripts/data-processing/import-azure-professional.py"
    )
    
    foreach ($file in $requiredFiles) {
        if (Test-Path $file) {
            $size = [math]::Round((Get-Item $file).Length / 1KB, 2)
            Write-TestResult "Files.$file" "PASS" "$size KB"
        } else {
            Write-TestResult "Files.$file" "FAIL" "Fichier manquant"
        }
    }
}

function Test-AzureSQLConnectivity {
    Write-ValidationHeader "VALIDATION CONNECTIVITÉ AZURE SQL DATABASE"
    
    try {
        Import-Module SqlServer -Force -ErrorAction Stop
        Write-TestResult "SQL.ModuleImport" "PASS" "Module SqlServer chargé"
    } catch {
        Write-TestResult "SQL.ModuleImport" "FAIL" "Module SqlServer indisponible"
        return
    }
    
    try {
        $testQuery = "SELECT @@VERSION as SQLVersion, GETDATE() as CurrentTime"
        $result = Invoke-Sqlcmd -ServerInstance $Global:ValidationConfig.ServerName `
                                -Database $Global:ValidationConfig.DatabaseName `
                                -Username $Global:ValidationConfig.AdminLogin `
                                -Password $Global:ValidationConfig.AdminPassword `
                                -Query $testQuery -QueryTimeout 30 -ErrorAction Stop
        
        Write-TestResult "SQL.Connectivity" "PASS" "Connexion établie"
        
        if ($Detailed) {
            Write-Host "    └─ Version SQL: $($result.SQLVersion.Split('`n')[0])" -ForegroundColor DarkGray
            Write-Host "    └─ Heure serveur: $($result.CurrentTime)" -ForegroundColor DarkGray
        }
        
    } catch {
        Write-TestResult "SQL.Connectivity" "FAIL" "Impossible de se connecter: $($_.Exception.Message)"
        return
    }
    
    # Test des tables
    $expectedTables = @("ConsultationsFICP", "InscriptionsFICP", "RadiationsFICP", "KPIDashboardFICP")
    
    try {
        $tablesQuery = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        $existingTables = Invoke-Sqlcmd -ServerInstance $Global:ValidationConfig.ServerName `
                                       -Database $Global:ValidationConfig.DatabaseName `
                                       -Username $Global:ValidationConfig.AdminLogin `
                                       -Password $Global:ValidationConfig.AdminPassword `
                                       -Query $tablesQuery
        
        $tableNames = $existingTables | ForEach-Object { $_.TABLE_NAME }
        
        foreach ($expectedTable in $expectedTables) {
            if ($expectedTable -in $tableNames) {
                # Compter les enregistrements
                $countQuery = "SELECT COUNT(*) as RecordCount FROM [$expectedTable]"
                $count = Invoke-Sqlcmd -ServerInstance $Global:ValidationConfig.ServerName `
                                      -Database $Global:ValidationConfig.DatabaseName `
                                      -Username $Global:ValidationConfig.AdminLogin `
                                      -Password $Global:ValidationConfig.AdminPassword `
                                      -Query $countQuery
                
                if ($count.RecordCount -gt 0) {
                    Write-TestResult "SQL.Table.$expectedTable" "PASS" "$($count.RecordCount) enregistrements"
                } else {
                    Write-TestResult "SQL.Table.$expectedTable" "WARN" "Table vide"
                }
            } else {
                Write-TestResult "SQL.Table.$expectedTable" "FAIL" "Table manquante"
            }
        }
        
    } catch {
        Write-TestResult "SQL.TablesValidation" "FAIL" "Erreur validation tables: $($_.Exception.Message)"
    }
}

function Test-DataQuality {
    Write-ValidationHeader "VALIDATION QUALITÉ DES DONNÉES"
    
    try {
        # Test cohérence des données consultations
        $consistencyQuery = @"
        SELECT 
            COUNT(*) as TotalConsultations,
            COUNT(CASE WHEN MontantDemande > 0 THEN 1 END) as ValidAmounts,
            COUNT(CASE WHEN StatutDemande IN ('Favorable', 'Defavorable', 'A etudier') THEN 1 END) as ValidStatus,
            COUNT(DISTINCT NumeroSIREN) as UniqueCompanies,
            AVG(MontantDemande) as AvgAmount,
            MIN(DateConsultation) as MinDate,
            MAX(DateConsultation) as MaxDate
        FROM ConsultationsFICP
"@
        
        $qualityResult = Invoke-Sqlcmd -ServerInstance $Global:ValidationConfig.ServerName `
                                      -Database $Global:ValidationConfig.DatabaseName `
                                      -Username $Global:ValidationConfig.AdminLogin `
                                      -Password $Global:ValidationConfig.AdminPassword `
                                      -Query $consistencyQuery
        
        if ($qualityResult.TotalConsultations -gt 0) {
            $validAmountsPct = [math]::Round(($qualityResult.ValidAmounts / $qualityResult.TotalConsultations) * 100, 2)
            $validStatusPct = [math]::Round(($qualityResult.ValidStatus / $qualityResult.TotalConsultations) * 100, 2)
            
            if ($validAmountsPct -ge 95) {
                Write-TestResult "Data.AmountValidity" "PASS" "$validAmountsPct% montants valides"
            } else {
                Write-TestResult "Data.AmountValidity" "WARN" "$validAmountsPct% montants valides (< 95%)"
            }
            
            if ($validStatusPct -ge 95) {
                Write-TestResult "Data.StatusValidity" "PASS" "$validStatusPct% statuts valides"
            } else {
                Write-TestResult "Data.StatusValidity" "WARN" "$validStatusPct% statuts valides (< 95%)"
            }
            
            Write-TestResult "Data.Diversity" "PASS" "$($qualityResult.UniqueCompanies) entreprises uniques"
            Write-TestResult "Data.TimeSpan" "PASS" "Du $($qualityResult.MinDate.ToString('yyyy-MM-dd')) au $($qualityResult.MaxDate.ToString('yyyy-MM-dd'))"
            
            if ($Detailed) {
                Write-Host "    └─ Montant moyen: $([math]::Round($qualityResult.AvgAmount, 2))€" -ForegroundColor DarkGray
            }
        } else {
            Write-TestResult "Data.Consultations" "FAIL" "Aucune donnée de consultation"
        }
        
    } catch {
        Write-TestResult "Data.QualityCheck" "FAIL" "Erreur validation qualité: $($_.Exception.Message)"
    }
}

function Test-BusinessIntelligence {
    Write-ValidationHeader "VALIDATION BUSINESS INTELLIGENCE"
    
    try {
        # Test des requêtes complexes typiques Power BI
        $kpiQuery = @"
        SELECT 
            COUNT(*) as TotalConsultations,
            SUM(MontantDemande) as MontantTotal,
            AVG(MontantDemande) as MontantMoyen,
            COUNT(CASE WHEN StatutDemande = 'Favorable' THEN 1 END) * 100.0 / COUNT(*) as TauxAcceptation,
            COUNT(DISTINCT NumeroSIREN) as EntreprisesUniques,
            COUNT(DISTINCT RegionEntreprise) as RegionsUniques
        FROM ConsultationsFICP
"@
        
        $kpiResult = Invoke-Sqlcmd -ServerInstance $Global:ValidationConfig.ServerName `
                                  -Database $Global:ValidationConfig.DatabaseName `
                                  -Username $Global:ValidationConfig.AdminLogin `
                                  -Password $Global:ValidationConfig.AdminPassword `
                                  -Query $kpiQuery
        
        if ($kpiResult.TotalConsultations -gt 1000) {
            Write-TestResult "BI.DataVolume" "PASS" "$($kpiResult.TotalConsultations) consultations (>1000)"
        } else {
            Write-TestResult "BI.DataVolume" "WARN" "$($kpiResult.TotalConsultations) consultations (<1000)"
        }
        
        $tauxAcceptation = [math]::Round($kpiResult.TauxAcceptation, 2)
        Write-TestResult "BI.AcceptanceRate" "PASS" "$tauxAcceptation% d'acceptation"
        
        Write-TestResult "BI.DataDiversity" "PASS" "$($kpiResult.EntreprisesUniques) entreprises, $($kpiResult.RegionsUniques) régions"
        
        # Test jointure entre tables
        $joinQuery = @"
        SELECT COUNT(*) as JoinCount 
        FROM ConsultationsFICP c 
        LEFT JOIN InscriptionsFICP i ON c.NumeroSIREN = i.NumeroSIREN
"@
        
        $joinResult = Invoke-Sqlcmd -ServerInstance $Global:ValidationConfig.ServerName `
                                   -Database $Global:ValidationConfig.DatabaseName `
                                   -Username $Global:ValidationConfig.AdminLogin `
                                   -Password $Global:ValidationConfig.AdminPassword `
                                   -Query $joinQuery
        
        Write-TestResult "BI.JoinCapability" "PASS" "Jointures fonctionnelles ($($joinResult.JoinCount) résultats)"
        
    } catch {
        Write-TestResult "BI.ComplexQueries" "FAIL" "Erreur requêtes BI: $($_.Exception.Message)"
    }
}

function Test-CertificationCriteria {
    Write-ValidationHeader "VALIDATION CRITÈRES CERTIFICATION E7"
    
    # Architecture Medallion
    $medallionFolders = @("DataLakeE7/bronze", "DataLakeE7/silver", "DataLakeE7/gold", "DataLakeE7/logs")
    $medallionValid = $true
    
    foreach ($folder in $medallionFolders) {
        if (-not (Test-Path $folder)) {
            $medallionValid = $false
            break
        }
    }
    
    if ($medallionValid) {
        Write-TestResult "Certification.MedallionArchitecture" "PASS" "Architecture Bronze/Silver/Gold complète"
    } else {
        Write-TestResult "Certification.MedallionArchitecture" "FAIL" "Architecture Medallion incomplète"
    }
    
    # Infrastructure Azure
    if ($Global:ValidationResults.Details["SQL.Connectivity"].Status -eq "PASS") {
        Write-TestResult "Certification.AzureInfrastructure" "PASS" "Azure SQL Database opérationnelle"
    } else {
        Write-TestResult "Certification.AzureInfrastructure" "FAIL" "Infrastructure Azure non validée"
    }
    
    # Volume de données
    $totalRecords = 0
    try {
        $volumeQuery = @"
        SELECT 
            (SELECT COUNT(*) FROM ConsultationsFICP) + 
            (SELECT COUNT(*) FROM InscriptionsFICP) + 
            (SELECT COUNT(*) FROM RadiationsFICP) as TotalRecords
"@
        
        $volumeResult = Invoke-Sqlcmd -ServerInstance $Global:ValidationConfig.ServerName `
                                     -Database $Global:ValidationConfig.DatabaseName `
                                     -Username $Global:ValidationConfig.AdminLogin `
                                     -Password $Global:ValidationConfig.AdminPassword `
                                     -Query $volumeQuery
        
        $totalRecords = $volumeResult.TotalRecords
        
        if ($totalRecords -ge 3000) {
            Write-TestResult "Certification.DataVolume" "PASS" "$totalRecords enregistrements (≥3000)"
        } else {
            Write-TestResult "Certification.DataVolume" "WARN" "$totalRecords enregistrements (<3000)"
        }
        
    } catch {
        Write-TestResult "Certification.DataVolume" "FAIL" "Impossible de calculer le volume"
    }
    
    # Documentation
    $docFiles = @("README.md", "docs/GUIDE-POWER-BI.md", "docs/ARCHITECTURE-MEDALLION-COMPLETE.md")
    $docCount = 0
    
    foreach ($docFile in $docFiles) {
        if (Test-Path $docFile) {
            $docCount++
        }
    }
    
    if ($docCount -eq $docFiles.Count) {
        Write-TestResult "Certification.Documentation" "PASS" "Documentation complète ($docCount/$($docFiles.Count))"
    } else {
        Write-TestResult "Certification.Documentation" "WARN" "Documentation partielle ($docCount/$($docFiles.Count))"
    }
}

function Generate-ValidationSummary {
    Write-ValidationHeader "RÉSUMÉ DE LA VALIDATION"
    
    $passRate = if ($Global:ValidationResults.Summary.TotalTests -gt 0) {
        [math]::Round(($Global:ValidationResults.Summary.PassedTests / $Global:ValidationResults.Summary.TotalTests) * 100, 2)
    } else { 0 }
    
    $Global:ValidationResults.Summary.OverallStatus = if ($passRate -ge 90) { "EXCELLENT" }
        elseif ($passRate -ge 80) { "BON" }
        elseif ($passRate -ge 70) { "ACCEPTABLE" }
        else { "INSUFFISANT" }
    
    Write-Host ""
    Write-Host "📊 STATISTIQUES GLOBALES:" -ForegroundColor Cyan
    Write-Host "   • Tests exécutés: $($Global:ValidationResults.Summary.TotalTests)" -ForegroundColor White
    Write-Host "   • Réussites: $($Global:ValidationResults.Summary.PassedTests)" -ForegroundColor Green
    Write-Host "   • Échecs: $($Global:ValidationResults.Summary.FailedTests)" -ForegroundColor Red
    Write-Host "   • Avertissements: $($Global:ValidationResults.Summary.WarningTests)" -ForegroundColor Yellow
    Write-Host "   • Taux de réussite: $passRate%" -ForegroundColor $(if ($passRate -ge 80) { "Green" } else { "Red" })
    
    Write-Host ""
    $statusColor = switch ($Global:ValidationResults.Summary.OverallStatus) {
        "EXCELLENT" { "Green" }
        "BON" { "Cyan" }
        "ACCEPTABLE" { "Yellow" }
        default { "Red" }
    }
    
    Write-Host "🎯 STATUT GLOBAL: $($Global:ValidationResults.Summary.OverallStatus)" -ForegroundColor $statusColor
    
    if ($Global:ValidationResults.Summary.OverallStatus -in @("EXCELLENT", "BON")) {
        Write-Host ""
        Write-Host "🏆 FÉLICITATIONS ! Votre projet E7 est prêt pour la certification !" -ForegroundColor Green
        Write-Host "✅ Infrastructure Azure opérationnelle" -ForegroundColor Green
        Write-Host "✅ Architecture Medallion validée" -ForegroundColor Green
        Write-Host "✅ Données de qualité importées" -ForegroundColor Green
        Write-Host "✅ Prêt pour Power BI" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⚠️  Améliorations recommandées avant certification" -ForegroundColor Yellow
    }
}

function Export-ValidationResults {
    if ($ExportResults) {
        try {
            $Global:ValidationResults | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutputPath -Encoding UTF8
            Write-Host ""
            Write-Host "📄 Résultats exportés vers: $OutputPath" -ForegroundColor Cyan
        } catch {
            Write-Host "❌ Erreur export: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# ==============================================================================
# EXÉCUTION PRINCIPALE
# ==============================================================================

Write-ValidationHeader "E7 CERTIFICATION - VALIDATION COMPLÈTE ET PROFESSIONNELLE"

Write-Host "🔍 Mode: $(if ($Detailed) { 'Détaillé' } else { 'Standard' })" -ForegroundColor Cyan
Write-Host "📅 Date: $($Global:ValidationConfig.ValidationDate)" -ForegroundColor Cyan
if ($ExportResults) {
    Write-Host "📄 Export: $OutputPath" -ForegroundColor Cyan
}

# Exécution des tests
Test-ProjectStructure
Test-AzureSQLConnectivity  
Test-DataQuality
Test-BusinessIntelligence
Test-CertificationCriteria

# Génération du résumé
Generate-ValidationSummary

# Export des résultats
Export-ValidationResults

Write-Host ""
Write-Host ("═" * 90) -ForegroundColor Cyan
Write-Host "Validation terminée - Projet E7 Data Engineer" -ForegroundColor Green
Write-Host ("═" * 90) -ForegroundColor Cyan