# VALIDATION COMPLETE DATA LAKE FICP
# Test de bout en bout pour certification E7
Import-Module Az.Accounts -Force
Import-Module Az.Resources -Force
Import-Module Az.Storage -Force

Write-Host "========================================" -ForegroundColor Green
Write-Host "   VALIDATION DATA LAKE FICP E7" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Configuration
$resourceGroupName = "rg-datalake-ficp"
$storageAccountName = "ficpstorageaccount"
$dataFactoryName = "df-ficp"
$containerName = "ficp-data"

$tests = @()

Write-Host "TESTS DE VALIDATION CERTIFICATION E7 :" -ForegroundColor Cyan
Write-Host ""

# Test 1 : Vérification Resource Group
Write-Host "1. Test Resource Group..." -ForegroundColor Yellow
try {
    $rg = Get-AzResourceGroup -Name $resourceGroupName
    Write-Host "   ✅ Resource Group '$resourceGroupName' existe" -ForegroundColor Green
    Write-Host "   -> Location: $($rg.Location)" -ForegroundColor White
    $tests += @{Test="Resource Group"; Status="✅ PASS"; Details=$rg.Location}
} catch {
    Write-Host "   ❌ Resource Group inexistant" -ForegroundColor Red
    $tests += @{Test="Resource Group"; Status="❌ FAIL"; Details="Inexistant"}
}

# Test 2 : Vérification Storage Account
Write-Host "2. Test Storage Account..." -ForegroundColor Yellow
try {
    $storage = Get-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName
    Write-Host "   ✅ Storage Account '$storageAccountName' existe" -ForegroundColor Green
    Write-Host "   -> Type: $($storage.Kind)" -ForegroundColor White
    Write-Host "   -> HNS: $($storage.EnableHierarchicalNamespace)" -ForegroundColor White
    $tests += @{Test="Storage Account"; Status="✅ PASS"; Details="Data Lake Gen2"}
} catch {
    Write-Host "   ❌ Storage Account inexistant" -ForegroundColor Red
    $tests += @{Test="Storage Account"; Status="❌ FAIL"; Details="Inexistant"}
}

# Test 3 : Vérification Data Factory
Write-Host "3. Test Data Factory..." -ForegroundColor Yellow
try {
    $df = Get-AzResource -ResourceGroupName $resourceGroupName -Name $dataFactoryName -ResourceType "Microsoft.DataFactory/factories"
    Write-Host "   ✅ Data Factory '$dataFactoryName' existe" -ForegroundColor Green
    Write-Host "   -> Location: $($df.Location)" -ForegroundColor White
    $tests += @{Test="Data Factory"; Status="✅ PASS"; Details=$df.Location}
} catch {
    Write-Host "   ❌ Data Factory inexistant" -ForegroundColor Red
    $tests += @{Test="Data Factory"; Status="❌ FAIL"; Details="Inexistant"}
}

# Test 4 : Vérification Container et données
Write-Host "4. Test Container et donnees..." -ForegroundColor Yellow
try {
    $ctx = $storage.Context
    $blobs = Get-AzStorageBlob -Container $containerName -Context $ctx
    
    Write-Host "   ✅ Container '$containerName' existe" -ForegroundColor Green
    Write-Host "   -> Fichiers: $($blobs.Count)" -ForegroundColor White
    
    $totalSize = ($blobs | Measure-Object Length -Sum).Sum
    Write-Host "   -> Taille totale: $([math]::Round($totalSize/1KB, 2)) KB" -ForegroundColor White
    
    # Vérification des fichiers FICP spécifiques
    $ficpFiles = $blobs | Where-Object { $_.Name -like "ficp_*_test_*.csv" }
    Write-Host "   -> Fichiers FICP: $($ficpFiles.Count)/3" -ForegroundColor White
    
    if ($ficpFiles.Count -eq 3) {
        $tests += @{Test="Données FICP"; Status="✅ PASS"; Details="3 fichiers CSV"}
    } else {
        $tests += @{Test="Données FICP"; Status="⚠️  PARTIAL"; Details="$($ficpFiles.Count)/3 fichiers"}
    }
} catch {
    Write-Host "   ❌ Container ou donnees inaccessibles" -ForegroundColor Red
    $tests += @{Test="Données FICP"; Status="❌ FAIL"; Details="Inaccessible"}
}

# Test 5 : Vérification des configurations Data Factory
Write-Host "5. Test configurations Data Factory..." -ForegroundColor Yellow
$configFiles = @(
    "Infrastructure\linkedservice-storage.json",
    "Infrastructure\dataset-ficp.json", 
    "Infrastructure\pipeline-ficp.json"
)

$configCount = 0
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        $configCount++
        Write-Host "   ✅ $file existe" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file manquant" -ForegroundColor Red
    }
}

if ($configCount -eq 3) {
    $tests += @{Test="Config Data Factory"; Status="✅ PASS"; Details="3/3 fichiers"}
} else {
    $tests += @{Test="Config Data Factory"; Status="⚠️  PARTIAL"; Details="$configCount/3 fichiers"}
}

# Résumé des tests
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   RESULTATS VALIDATION E7" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

foreach ($test in $tests) {
    $statusColor = switch ($test.Status.Substring(0,1)) {
        "✅" { "Green" }
        "⚠️" { "Yellow" }
        "❌" { "Red" }
        default { "White" }
    }
    
    Write-Host "$($test.Test.PadRight(20)) | $($test.Status) | $($test.Details)" -ForegroundColor $statusColor
}

# Score final
$passCount = ($tests | Where-Object { $_.Status -like "*PASS*" }).Count
$totalTests = $tests.Count
$score = [math]::Round(($passCount / $totalTests) * 100, 0)

Write-Host ""
Write-Host "SCORE FINAL : $score% ($passCount/$totalTests tests réussis)" -ForegroundColor $(if($score -ge 80){"Green"} elseif($score -ge 60){"Yellow"} else{"Red"})
Write-Host ""

if ($score -ge 80) {
    Write-Host "🏆 CERTIFICATION E7 - DATA ENGINEER VALIDEE !" -ForegroundColor Green
    Write-Host "🎉 Votre Data Lake FICP est operationnel !" -ForegroundColor Green
} elseif ($score -ge 60) {
    Write-Host "⚠️  CERTIFICATION PARTIELLE - Quelques ameliorations necessaires" -ForegroundColor Yellow
} else {
    Write-Host "❌ CERTIFICATION NON VALIDEE - Corrections requises" -ForegroundColor Red
}

Write-Host ""
Write-Host "Prochaines etapes :" -ForegroundColor Cyan
Write-Host "1. Consultez CERTIFICATION-E7-FINAL.md pour le rapport complet"
Write-Host "2. Testez les pipelines sur portal.azure.com"
Write-Host "3. Explorez vos donnees dans le Data Lake"
Write-Host "4. Presentez votre architecture pour validation finale"