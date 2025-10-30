# CREATION AZURE SQL DATABASE AVEC AZURE REST API
# Deploiement d'une vraie base de donnees SQL dans le cloud
# Sans Azure CLI - Utilise les API REST Azure directement

param(
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "rg-datalake-ficp",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "francecentral",
    
    [Parameter(Mandatory=$false)]
    [string]$SqlServerName = "sql-server-ficp-$(Get-Random -Maximum 9999)",
    
    [Parameter(Mandatory=$false)]
    [string]$DatabaseName = "db-ficp-datawarehouse",
    
    [Parameter(Mandatory=$false)]
    [string]$AdminLogin = "ficpadmin",
    
    [Parameter(Mandatory=$false)]
    [string]$AdminPassword = "FicpDataWarehouse2025!"
)

Write-Host "================================================" -ForegroundColor Green
Write-Host "   CREATION AZURE SQL DATABASE - METHODE PRO" -ForegroundColor Green  
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

Write-Host "🎯 OBJECTIF: Vraie base SQL dans le cloud Azure" -ForegroundColor Cyan
Write-Host "📊 Donnees: 95,277 enregistrements repartis en 4 tables" -ForegroundColor Gray
Write-Host "💰 Cout: ~5-10 EUR/mois (Basic/S0 tier)" -ForegroundColor Gray
Write-Host ""

# Fonction pour obtenir le token d'access Azure
function Get-AzureAccessToken {
    try {
        # Essayer de recuperer le token via Azure PowerShell
        $context = Get-AzContext -ErrorAction SilentlyContinue
        if ($context) {
            $token = [Microsoft.Azure.Commands.Common.Authentication.AzureSession]::Instance.AuthenticationFactory.Authenticate($context.Account, $context.Environment, $context.Tenant.Id, $null, "Never", $null, "https://management.azure.com/").AccessToken
            return $token
        }
        return $null
    } catch {
        return $null
    }
}

# Configuration
Write-Host "CONFIGURATION AZURE SQL DATABASE:" -ForegroundColor Yellow
Write-Host "-> Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "-> SQL Server: $SqlServerName" -ForegroundColor White  
Write-Host "-> Database: $DatabaseName" -ForegroundColor White
Write-Host "-> Admin Login: $AdminLogin" -ForegroundColor White
Write-Host "-> Location: $Location" -ForegroundColor White
Write-Host ""

# Verification des prerequis
Write-Host "1. Verification des prerequis..." -ForegroundColor Yellow

# Test connexion Azure
try {
    $azContext = Get-AzContext -ErrorAction SilentlyContinue
    if (-not $azContext) {
        Write-Host "   ❌ Non connecte a Azure" -ForegroundColor Red
        Write-Host ""
        Write-Host "SOLUTION: Connectez-vous d'abord:" -ForegroundColor Cyan
        Write-Host "1. Install-Module Az -Force" -ForegroundColor Gray
        Write-Host "2. Connect-AzAccount" -ForegroundColor Gray
        Write-Host "3. Relancez ce script" -ForegroundColor Gray
        Write-Host ""
        
        # Proposition de connexion automatique
        $connect = Read-Host "Voulez-vous vous connecter maintenant ? (o/N)"
        if ($connect -eq "o" -or $connect -eq "O") {
            try {
                Import-Module Az -Force -ErrorAction SilentlyContinue
                Connect-AzAccount
                $azContext = Get-AzContext
            } catch {
                Write-Host "Erreur lors de la connexion: $($_.Exception.Message)" -ForegroundColor Red
                exit 1
            }
        } else {
            exit 1
        }
    }
    
    Write-Host "   ✅ Connecte a Azure: $($azContext.Account.Id)" -ForegroundColor Green
    
    # Obtenir subscription si non fournie
    if (-not $SubscriptionId) {
        $SubscriptionId = $azContext.Subscription.Id
    }
    Write-Host "   ✅ Subscription: $SubscriptionId" -ForegroundColor Green
    
} catch {
    Write-Host "   ❌ Erreur verification Azure: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Creation via Azure PowerShell (plus fiable que REST API)
Write-Host ""
Write-Host "2. Creation du serveur SQL Azure..." -ForegroundColor Yellow

try {
    # Import du module SQL
    Import-Module Az.Sql -Force -ErrorAction SilentlyContinue
    
    # Verification que le resource group existe
    $rg = Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue
    if (-not $rg) {
        Write-Host "   ⚠️  Resource Group n'existe pas, creation..." -ForegroundColor Yellow
        New-AzResourceGroup -Name $ResourceGroupName -Location $Location | Out-Null
        Write-Host "   ✅ Resource Group cree: $ResourceGroupName" -ForegroundColor Green
    } else {
        Write-Host "   ✅ Resource Group existe: $ResourceGroupName" -ForegroundColor Green
    }
    
    # Creation du serveur SQL
    Write-Host "   Creation du serveur SQL..." -ForegroundColor Gray
    
    $securePassword = ConvertTo-SecureString $AdminPassword -AsPlainText -Force
    $credentials = New-Object System.Management.Automation.PSCredential($AdminLogin, $securePassword)
    
    $sqlServer = New-AzSqlServer -ResourceGroupName $ResourceGroupName `
                                -ServerName $SqlServerName `
                                -Location $Location `
                                -SqlAdministratorCredentials $credentials
    
    Write-Host "   ✅ Serveur SQL cree: $SqlServerName" -ForegroundColor Green
    
} catch {
    if ($_.Exception.Message -like "*already exists*") {
        Write-Host "   ⚠️  Serveur existe deja, tentative avec nom different..." -ForegroundColor Yellow
        $SqlServerName = "sql-server-ficp-$(Get-Random -Maximum 99999)"
        try {
            $sqlServer = New-AzSqlServer -ResourceGroupName $ResourceGroupName `
                                        -ServerName $SqlServerName `
                                        -Location $Location `
                                        -SqlAdministratorCredentials $credentials
            Write-Host "   ✅ Serveur SQL cree: $SqlServerName" -ForegroundColor Green
        } catch {
            Write-Host "   ❌ Erreur creation serveur: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "   ❌ Erreur creation serveur: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Configuration du firewall
Write-Host ""
Write-Host "3. Configuration du firewall..." -ForegroundColor Yellow

try {
    # Autoriser les services Azure
    New-AzSqlServerFirewallRule -ResourceGroupName $ResourceGroupName `
                               -ServerName $SqlServerName `
                               -FirewallRuleName "AllowAzureServices" `
                               -StartIpAddress "0.0.0.0" `
                               -EndIpAddress "0.0.0.0" | Out-Null
    
    # Obtenir et autoriser IP locale
    $myIP = (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 10).Trim()
    New-AzSqlServerFirewallRule -ResourceGroupName $ResourceGroupName `
                               -ServerName $SqlServerName `
                               -FirewallRuleName "AllowMyIP" `
                               -StartIpAddress $myIP `
                               -EndIpAddress $myIP | Out-Null
    
    Write-Host "   ✅ Firewall configure (IP autorisee: $myIP)" -ForegroundColor Green
    
} catch {
    Write-Host "   ⚠️  Erreur firewall: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   ℹ️  Vous pourrez configurer manuellement via le portail Azure" -ForegroundColor Gray
}

# Creation de la base de donnees
Write-Host ""
Write-Host "4. Creation de la base de donnees..." -ForegroundColor Yellow

try {
    $database = New-AzSqlDatabase -ResourceGroupName $ResourceGroupName `
                                 -ServerName $SqlServerName `
                                 -DatabaseName $DatabaseName `
                                 -Edition "Basic" `
                                 -RequestedServiceObjectiveName "Basic"
    
    Write-Host "   ✅ Base de donnees creee: $DatabaseName" -ForegroundColor Green
    
} catch {
    Write-Host "   ❌ Erreur creation database: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Succes - Affichage des informations de connexion
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "   ✅ AZURE SQL DATABASE CREEE AVEC SUCCES !" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

$serverFQDN = "$SqlServerName.database.windows.net"
$connectionString = "Server=tcp:$serverFQDN,1433;Initial Catalog=$DatabaseName;Persist Security Info=False;User ID=$AdminLogin;Password=$AdminPassword;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"

Write-Host "📋 INFORMATIONS DE CONNEXION:" -ForegroundColor Cyan
Write-Host "-> Serveur: $serverFQDN" -ForegroundColor White
Write-Host "-> Database: $DatabaseName" -ForegroundColor White  
Write-Host "-> Login: $AdminLogin" -ForegroundColor White
Write-Host "-> Password: $AdminPassword" -ForegroundColor White
Write-Host ""

Write-Host "🔗 CONNECTION STRING:" -ForegroundColor Yellow
Write-Host $connectionString -ForegroundColor Gray
Write-Host ""

# Sauvegarde des informations
$connectionInfo = @{
    ServerName = $serverFQDN
    ServerNameShort = $SqlServerName
    DatabaseName = $DatabaseName
    AdminLogin = $AdminLogin
    AdminPassword = $AdminPassword
    ConnectionString = $connectionString
    CreationDate = (Get-Date).ToString()
    ResourceGroup = $ResourceGroupName
    Location = $Location
    Edition = "Basic"
    Status = "Created"
}

$connectionInfo | ConvertTo-Json -Depth 2 | Out-File -FilePath "sql-connection-info.json" -Encoding UTF8
Write-Host "💾 Infos sauvegardees: sql-connection-info.json" -ForegroundColor Green

Write-Host ""
Write-Host "🚀 PROCHAINES ETAPES:" -ForegroundColor White
Write-Host "1. ✅ Azure SQL Database creee et operationnelle"
Write-Host "2. 🔨 Creer les tables (schema-sql-datawarehouse.sql)"  
Write-Host "3. 📊 Importer les donnees (import-csv-to-sql.py)"
Write-Host "4. 📈 Connecter Power BI"
Write-Host ""

Write-Host "💡 COMMANDES SUIVANTES:" -ForegroundColor Cyan
Write-Host "# Creer les tables:"
Write-Host "python create-tables-azure.py" -ForegroundColor Gray
Write-Host ""
Write-Host "# Importer les donnees:"  
Write-Host "python import-csv-to-sql.py" -ForegroundColor Gray
Write-Host ""

$continue = Read-Host "Voulez-vous continuer avec la creation des tables ? (o/N)"
if ($continue -eq "o" -or $continue -eq "O") {
    Write-Host ""
    Write-Host "Lancement de la creation des tables..." -ForegroundColor Green
    # Le script suivant sera lance
    python create-tables-azure.py
}