# E7 CERTIFICATION - DOCUMENTATION SCRIPTS FICP

## 📋 SCRIPTS DISPONIBLES

### 🎯 Script Principal
**`run-ficp-manager.bat`** - Script principal avec menu interactif
- Active automatiquement l'environnement virtuel
- Vérifie et installe les dépendances
- Lance le gestionnaire FICP avec menu

### 🛠️ Scripts de Traitement

#### **`scripts/data-processing/ficp-manager.py`**
Gestionnaire principal avec menu interactif :
1. Générer données FICP réalistes
2. Tester connexion Azure  
3. Importer consultations (1000)
4. Importer courriers (500)
5. Import complet
6. Statistiques Azure
7. Quitter

#### **`scripts/data-processing/generate-ficp-realistic.py`**
- Génère consultations FICP réalistes basées sur l'expérience Crédit Agricole
- Structure : `date_consultation`, `cle_bdf`, `reponse_registre`, `etablissement_demandeur`
- Clés BDF 13 caractères (algorithmique basé sur nom+prénom+date_naissance)
- Taux inscription réaliste : ~15%

#### **`scripts/data-processing/generate-courriers-ficp-realistic.py`**
- Génère courriers FICP avec workflow métier réaliste
- Types : SURVEILLANCE → INSCRIPTION → RADIATION
- Processus : 70% régularisent sous 30 jours, 30% passent en inscription
- Structure : `date_envoi`, `cle_bdf`, `type_courrier`

#### **`scripts/data-processing/import-azure-simple.py`**
- Import simple et robuste vers Azure SQL Database
- Limité à 100 consultations pour tests
- Gestion d'erreurs basique

## 🚀 UTILISATION RAPIDE

### Lancement Simple
```bash
# Double-clic ou en ligne de commande :
.\run-ficp-manager.bat
```

### Utilisation Script Principal
1. **Première utilisation :**
   - Option 1 : Générer données FICP réalistes
   - Option 2 : Tester connexion Azure

2. **Import vers Azure :**
   - Option 5 : Import complet (recommandé)
   - Ou Options 3+4 : Import séparé consultations/courriers

3. **Suivi :**
   - Option 6 : Statistiques Azure

## ⚙️ CONFIGURATION

### Prérequis
- Python 3.7+ avec environnement virtuel dans `.venv/`
- PowerShell avec module SqlServer
- Accès Azure SQL Database configuré dans `config/project-config.json`

### Configuration Azure
Le script utilise la configuration dans `config/project-config.json` :
```json
"sqlDatabase": {
  "serverName": "sql-server-ficp-5647",
  "databaseName": "db-ficp-datawarehouse", 
  "adminLogin": "ficpadmin",
  "adminPassword": "FicpDataWarehouse2025!"
}
```

### Gestion Pare-feu Azure
Le script peut planter si votre IP n'est pas autorisée. Solutions :
1. **Automatique :** Se connecter à Azure via PowerShell
   ```powershell
   Connect-AzAccount
   New-AzSqlServerFirewallRule -ResourceGroupName 'rg-datalake-ficp' -ServerName 'sql-server-ficp-5647' -FirewallRuleName 'AutoIP-Daily' -StartIpAddress 'VOTRE_IP' -EndIpAddress 'VOTRE_IP'
   ```

2. **Manuel :** Aller sur portal.azure.com et ajouter votre IP dans le pare-feu du serveur SQL

## 📊 DONNÉES GÉNÉRÉES

### Consultations FICP Réalistes
- **Fichier :** `DataLakeE7/tables_finales/TABLE_CONSULTATIONS_FICP_REALISTIC.csv`
- **Volume :** ~2,700 consultations/mois
- **Établissements :** Crédit Agricole, LCL, Sofinco, BNP Paribas, Société Générale
- **Taux inscription :** 15.1% (réaliste selon expérience CA)

### Courriers FICP Réalistes  
- **Fichier :** `DataLakeE7/tables_finales/TABLE_COURRIERS_FICP_REALISTIC.csv`
- **Volume :** ~400 courriers (200 surveillance + 60 inscription + 140 radiation)
- **Workflow :** Respecte le processus métier réel Crédit Agricole

## 🔧 DÉPANNAGE

### Problèmes Courants

**"ModuleNotFoundError: No module named 'pandas'"**
- Solution : Le script batch installe automatiquement les dépendances
- Ou manuellement : `pip install -r requirements.txt`

**"Erreur connexion Azure SQL"**
- Vérifier votre IP dans le pare-feu Azure
- Tester avec Option 2 du menu

**"Le venv a sauté"**
- Le script batch réactive automatiquement l'environnement
- Ou manuellement : `.venv\Scripts\activate`

## 📁 STRUCTURE PROPRE

```
E7_certif/
├── run-ficp-manager.bat           # 🚀 Script principal
├── scripts/data-processing/
│   ├── ficp-manager.py            # 🎯 Gestionnaire principal
│   ├── generate-ficp-realistic.py # 📋 Générateur consultations
│   ├── generate-courriers-ficp-realistic.py # 📮 Générateur courriers
│   └── import-azure-simple.py     # ⬆️ Import simple Azure
├── DataLakeE7/tables_finales/     # 📊 Données générées
├── config/project-config.json     # ⚙️ Configuration
└── requirements.txt               # 📦 Dépendances
```

## ✅ SCRIPTS SUPPRIMÉS (NETTOYAGE)

Scripts supprimés car défectueux/redondants :
- ❌ `fix-azure-connection.py` - Dependencies manquantes
- ❌ `update-azure-ip.py` - Problème encoding
- ❌ `import-azure-hybrid.py` - Trop complexe, plantait
- ❌ `import-azure-professional.py` - Redondant
- ❌ `import-local-test.py` - Pas nécessaire
- ❌ `import-ficp-realistic.py` - Redondant
- ❌ `run-import-azure.ps1/.bat` - Problèmes encoding/redondants

La solution est maintenant propre, fonctionnelle et facile à utiliser ! 🎉