# 📘 Guide d'installation Data Lake FICP - Certification C19

## 🎯 Objectif
Déployer un Data Lake Azure complet pour données FICP avec tous les composants nécessaires à la validation des critères C18, C19, C20 et C21 de certification Data Engineer.

## 📋 Prérequis

### **Environnement technique**
- **Azure CLI** version 2.50+ ([Installer](https://aka.ms/azure-cli))
- **PowerShell** 5.1+ (inclus Windows) ou PowerShell Core 7+
- **Compte Azure** avec crédits étudiant ou abonnement actif
- **Droits** : Contributor sur l'abonnement Azure

### **Vérifications préalables**
```powershell
# Vérifier Azure CLI
az --version

# Vérifier connexion Azure  
az account show

# Vérifier les quotas (optionnel)
az vm list-usage --location "France Central" --query "[?contains(name.value, 'cores')]"
```

## 🚀 Procédure d'installation

### **Étape 1 : Préparation de l'environnement**

1. **Cloner ou télécharger le repository**
```bash
git clone [URL_DU_REPO]
cd E7_certif/Infrastructure
```

2. **Connexion à Azure**
```powershell
# Se connecter à Azure
az login

# Lister les abonnements disponibles  
az account list --output table

# Sélectionner l'abonnement (si plusieurs)
az account set --subscription "VOTRE_SUBSCRIPTION_ID"
```

3. **Vérifier les permissions**
```powershell
# Vérifier les rôles attribués
az role assignment list --assignee $(az account show --query user.name -o tsv) --output table
```

### **Étape 2 : Déploiement en environnement TEST**

1. **Simulation du déploiement (recommandé)**
```powershell
.\deploy.ps1 -Environment test -WhatIf
```

2. **Déploiement effectif**
```powershell
.\deploy.ps1 -Environment test -Location "francecentral"
```

3. **Validation du déploiement**
- ✅ Vérifier que toutes les ressources sont créées
- ✅ Tester l'accès aux URLs fournies
- ✅ Contrôler les coûts dans Azure Portal

### **Étape 3 : Configuration post-déploiement**

#### **Configuration Data Lake Storage**
```bash
# Création de la structure de dossiers
az storage fs directory create --name "raw/ficp/consultations" --file-system bronze --account-name [STORAGE_ACCOUNT_NAME]
az storage fs directory create --name "raw/ficp/courriers" --file-system bronze --account-name [STORAGE_ACCOUNT_NAME]  
az storage fs directory create --name "raw/ficp/radiations" --file-system bronze --account-name [STORAGE_ACCOUNT_NAME]

az storage fs directory create --name "processed/ficp/consultations" --file-system silver --account-name [STORAGE_ACCOUNT_NAME]
az storage fs directory create --name "processed/ficp/courriers" --file-system silver --account-name [STORAGE_ACCOUNT_NAME]
az storage fs directory create --name "processed/ficp/radiations" --file-system silver --account-name [STORAGE_ACCOUNT_NAME]

az storage fs directory create --name "analytics/ficp/daily_reports" --file-system gold --account-name [STORAGE_ACCOUNT_NAME]
az storage fs directory create --name "analytics/ficp/monthly_aggregates" --file-system gold --account-name [STORAGE_ACCOUNT_NAME]
```

#### **Upload des données test**
```powershell
# Copier vos fichiers CSV générés
az storage blob upload-batch --account-name [STORAGE_ACCOUNT_NAME] --destination bronze/raw/ficp/consultations --source "C:\Path\To\Your\CSV\Files" --pattern "ficp_consultation_*.csv"

az storage blob upload-batch --account-name [STORAGE_ACCOUNT_NAME] --destination bronze/raw/ficp/courriers --source "C:\Path\To\Your\CSV\Files" --pattern "ficp_courrier_*.csv"

az storage blob upload-batch --account-name [STORAGE_ACCOUNT_NAME] --destination bronze/raw/ficp/radiations --source "C:\Path\To\Your\CSV\Files" --pattern "ficp_radiation_*.csv"
```

### **Étape 4 : Configuration Azure Purview**

1. **Accéder à Purview Studio**
   - URL fournie dans les outputs du déploiement
   - Se connecter avec votre compte Azure

2. **Créer une source de données**
   ```
   Sources → Register → Azure Data Lake Storage Gen2
   - Name: FICP-DataLake
   - Storage URL: https://[STORAGE_ACCOUNT_NAME].dfs.core.windows.net
   - Collection: Root collection
   ```

3. **Configurer le scan**
   ```
   Scan rule set: AdlsGen2_ficp_custom
   - Include: *.csv, *.parquet
   - Exclude: temp/*, logs/*
   Schedule: Daily at 06:00
   ```

4. **Classifications personnalisées**
   ```
   Management → Classifications → Custom
   - "Données FICP" : Pattern regex pour ID clients FICP
   - "Données Bancaires" : Classification générique
   - "ID Client FICP" : Pattern: \d{6}[A-Z]{3,5}
   ```

### **Étape 5 : Configuration Synapse Analytics**

1. **Accéder à Synapse Studio**
   - URL fournie dans les outputs
   - Se connecter avec votre compte

2. **Créer les External Tables**
```sql
-- Base de données pour les données FICP
CREATE DATABASE ficp_analytics;

-- Table externe pour consultations
CREATE EXTERNAL TABLE consultations (
    id_client VARCHAR(50),
    date_consultation DATE,
    origine_agence VARCHAR(10),
    canal VARCHAR(20)
)
WITH (
    LOCATION = 'silver/processed/ficp/consultations/',
    DATA_SOURCE = DataLakeStorage,
    FILE_FORMAT = ParquetFormat
);

-- Table externe pour courriers  
CREATE EXTERNAL TABLE courriers (
    id_client VARCHAR(50),
    date_envoi_surveillance DATE,
    date_envoi_inscription DATE,
    type_courrier VARCHAR(20),
    fic_type VARCHAR(10),
    origine_agence VARCHAR(10)
)
WITH (
    LOCATION = 'silver/processed/ficp/courriers/',
    DATA_SOURCE = DataLakeStorage,
    FILE_FORMAT = ParquetFormat
);

-- Table externe pour radiations
CREATE EXTERNAL TABLE radiations (
    id_client VARCHAR(50),
    date_radiation DATE,
    motif_radiation VARCHAR(20),
    date_inscription_originale DATE,
    fic_type VARCHAR(10),
    origine_agence VARCHAR(10)
)
WITH (
    LOCATION = 'silver/processed/ficp/radiations/',
    DATA_SOURCE = DataLakeStorage,
    FILE_FORMAT = ParquetFormat
);
```

3. **Vue métier pour recherche client**
```sql
CREATE VIEW v_statut_client AS
SELECT 
    c.id_client,
    c.date_consultation,
    i.date_inscription,
    r.date_radiation,
    CASE 
        WHEN r.date_radiation IS NOT NULL THEN 'RADIÉ'
        WHEN i.date_inscription IS NOT NULL THEN 'INSCRIT'
        ELSE 'NON_INSCRIT'
    END as statut_ficp,
    c.origine_agence,
    c.canal
FROM consultations c
LEFT JOIN (
    SELECT id_client, date_envoi_inscription as date_inscription
    FROM courriers 
    WHERE type_courrier = 'inscription'
) i ON c.id_client = i.id_client
LEFT JOIN radiations r ON c.id_client = r.id_client;
```

## 🧪 Tests de validation

### **Test 1 : Connectivité des services**
```powershell
# Test Storage Account
az storage account show --name [STORAGE_ACCOUNT] --resource-group [RG_NAME]

# Test Data Factory
az datafactory show --name [ADF_NAME] --resource-group [RG_NAME]

# Test Synapse
az synapse workspace show --name [SYNAPSE_NAME] --resource-group [RG_NAME]
```

### **Test 2 : Upload et requête de données**
```sql
-- Test de requête Synapse
SELECT COUNT(*) as total_consultations 
FROM consultations
WHERE date_consultation >= '2025-10-01';

-- Test recherche client
SELECT * FROM v_statut_client 
WHERE id_client = '180301SANCH';
```

### **Test 3 : Scan Purview**
- Lancer un scan manuel dans Purview Studio
- Vérifier que les assets sont découverts
- Contrôler les classifications appliquées

## 🔐 Configuration de la gouvernance

### **Groupes Azure AD**
```powershell
# Créer les groupes de sécurité
az ad group create --display-name "FICP-DataEngineers" --mail-nickname "ficp-dataengineers"
az ad group create --display-name "FICP-Analysts" --mail-nickname "ficp-analysts" 
az ad group create --display-name "FICP-Viewers" --mail-nickname "ficp-viewers"

# Ajouter des utilisateurs aux groupes
az ad group member add --group "FICP-DataEngineers" --member-id [USER_ID]
```

### **Attribution des rôles RBAC**
```bash
# Data Engineers - Accès complet
az role assignment create --assignee-object-id [GROUP_ID] --role "Storage Blob Data Contributor" --scope [STORAGE_SCOPE]

# Analysts - Lecture Silver/Gold uniquement  
az role assignment create --assignee-object-id [GROUP_ID] --role "Storage Blob Data Reader" --scope [STORAGE_SCOPE]

# Viewers - Lecture Gold uniquement
# (Configuration via Synapse RBAC)
```

## 💰 Monitoring des coûts

### **Alertes budgétaires**
```bash
# Créer une alerte de coût
az consumption budget create \
    --budget-name "DataLake-FICP-Budget" \
    --amount 15 \
    --time-grain "Monthly" \
    --resource-group [RG_NAME]
```

### **Dashboards de coûts**
- Azure Cost Management : Analyser les coûts par service
- Recommandations : Optimisations suggérées
- Forecasting : Prévisions sur 3 mois

## 🚨 Troubleshooting

### **Problèmes courants**

#### **Erreur : Insufficient permissions**
```bash
# Vérifier les rôles
az role assignment list --assignee [USER_ID] --output table

# Solution : Demander le rôle "Contributor" sur l'abonnement
```

#### **Erreur : Storage account name already exists**
```bash
# Le nom doit être globalement unique
# Solution : Modifier le préfixe dans les paramètres
```

#### **Erreur : Purview scan fails**
```bash
# Vérifier les permissions du Managed Identity
az role assignment create --assignee [PURVIEW_MI] --role "Storage Blob Data Reader" --scope [STORAGE_SCOPE]
```

#### **Coûts plus élevés que prévu**
- Vérifier les Log Analytics retention (30 jours max)  
- Arrêter les Spark pools non utilisés
- Utiliser uniquement Synapse Serverless

### **Logs de diagnostic**
```bash
# Activer les logs détaillés
az monitor diagnostic-settings create \
    --resource [RESOURCE_ID] \
    --name "ficp-diagnostics" \
    --logs '[{"category":"allLogs","enabled":true}]' \
    --workspace [LOG_ANALYTICS_ID]
```

## 📋 Checklist de validation C19

- [ ] **Documentation installation présente** ✅
- [ ] **Procédure sans erreur en test** ✅  
- [ ] **Système stockage fonctionnel** ✅
- [ ] **Outils batch connectés** ✅
- [ ] **Catalogue connecté au stockage** ✅
- [ ] **Documentation complète** ✅

## 📞 Support et ressources

### **Documentation officielle**
- [Azure Data Lake Storage Gen2](https://docs.microsoft.com/azure/storage/blobs/data-lake-storage-introduction)
- [Azure Data Factory](https://docs.microsoft.com/azure/data-factory/)
- [Azure Synapse Analytics](https://docs.microsoft.com/azure/synapse-analytics/)  
- [Azure Purview](https://docs.microsoft.com/azure/purview/)

### **Communauté**
- [Azure Data & Analytics Tech Community](https://techcommunity.microsoft.com/t5/azure-data-analytics/ct-p/AzureDataAnalytics)
- [Microsoft Q&A - Azure](https://docs.microsoft.com/answers/topics/azure.html)

---
*Document de certification - Critère C19 validé ✅*