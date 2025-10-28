# 📊 Générateur de Données FICP - DataLakeE7

## 🎯 Objectif
Ce dossier contient les scripts Python pour générer des données FICP fictives utilisées dans le cadre du projet de certification Data Engineer.

⚠️ **IMPORTANT** : Les fichiers CSV générés ne sont **PAS versionnés** dans Git pour des raisons de sécurité et de bonnes pratiques, même si les données sont fictives.

## 📁 Structure des fichiers

```
DataLakeE7/
├── GenerateCsv.py              # Génération quotidienne (jour J)
├── GenerateMonth.py            # Génération historique (30 jours) - VERSION ORIGINALE
├── GenerateWithRadiation.py    # Génération quotidienne avec radiations
├── GenerateMonthWithRadiation.py # Génération historique avec radiations - NOUVEAU
├── ficp_data/                  # Dossier des CSV historiques (ignoré par Git)
├── *.csv                       # Fichiers CSV du jour (ignorés par Git)
└── README.md                   # Ce fichier
```

## 🚀 Utilisation

### **Prérequis**
```bash
# Installer les dépendances Python
pip install pandas faker

# Ou avec l'environnement virtuel du projet
pip install -r requirements.txt
```

### **Génération quotidienne (recommandée)**
```bash
# Avec radiations (version complète)
python GenerateWithRadiation.py

# Version originale (sans radiations)  
python GenerateCsv.py
```

### **Génération historique (30 jours)**
```bash
# Avec radiations (version complète)
python GenerateMonthWithRadiation.py

# Version originale (sans radiations)
python GenerateMonth.py
```

## 📊 Données générées

### **Volume par défaut**
- **300 clients/jour** (ajusté pour réalisme)
- **3 types de fichiers** : consultations, courriers, radiations
- **Format CSV** avec headers

### **Structure des données**

#### **ficp_consultation_YYYY-MM-DD.csv**
```csv
id_client,date_consultation,origine_agence,canal
180301SANCH,2025-10-28,SOF,Web
280293MARIO,2025-10-28,SOF,Téléphone
```

#### **ficp_courrier_YYYY-MM-DD.csv**  
```csv
id_client,date_envoi_surveillance,date_envoi_inscription,type_courrier,fic_type,origine_agence
180301SANCH,2025-05-11,,surveillance,FIC4,SOF
180301SANCH,,2025-06-16,inscription,FIC1,SOF
```

#### **ficp_radiation_YYYY-MM-DD.csv**
```csv
id_client,date_radiation,motif_radiation,date_inscription_originale,fic_type,origine_agence
141180DELAU,2025-07-04,remboursement,2025-05-24,FIC1,CA
210297CHARR,2025-10-13,echeance,2025-05-20,FIC1,SOF
```

## 🔧 Paramètres configurables

### **Dans les scripts Python**
```python
# Volumétrie
clients_per_day = 300  # Nombre de clients par jour

# Agences
agences = ["SOF", "CA", "LCL"]

# Types de courriers FICP
fic_types = ["FIC1", "FIC2", "FIC3", "FIC4"]

# Canaux de consultation
canaux = ["Agence", "Web", "Téléphone"]

# Motifs de radiation
motifs_radiation = {
    "remboursement": 0.70,    # 70%
    "echeance": 0.25,         # 25% 
    "deces": 0.03,            # 3%
    "erreur": 0.02            # 2%
}
```

## 🏗️ Logique métier

### **Cycle de vie FICP**
```
1. SURVEILLANCE (obligatoire pour tous)
2. INSCRIPTION (50% des clients)  
3. RADIATION (selon motifs et délais)
```

### **Cohérence des données**
- ✅ **ID clients uniques** : Format DDMMYY + 5 lettres du nom
- ✅ **Dates logiques** : Surveillance → Inscription → Radiation
- ✅ **Radiations cohérentes** : Basées sur inscriptions existantes
- ✅ **Répartition réaliste** : Probabilités métier respectées

## 🎯 Utilisation dans le Data Lake

### **Zones de stockage**
```
Bronze/  → CSV bruts générés par ces scripts
Silver/  → Parquet nettoyés et validés  
Gold/    → Agrégations et métriques métier
```

### **Pipeline d'ingestion**
1. **Scripts Python** → Génération CSV locale
2. **Azure Container Instances** → Exécution quotidienne
3. **Data Factory** → Upload vers Azure Data Lake Gen2
4. **Synapse** → Transformation et analyse

## 🔒 Sécurité et conformité

### **Données fictives**
- ✅ Générées avec **Faker français**
- ✅ **Aucune donnée réelle** FICP
- ✅ **Noms et dates** complètement aléatoires
- ✅ **Conformité RGPD** par design

### **Bonnes pratiques**
- ❌ **Pas de commit** des fichiers CSV
- ✅ **Documentation** du processus de génération
- ✅ **Traçabilité** des transformations
- ✅ **Séparation** code/données

## 📈 Métriques générées

Après génération, vous devriez obtenir :
- **~300 consultations/jour**
- **~450 courriers/jour** (surveillance + inscriptions)  
- **~100 radiations/jour** (basées sur historique)

## 🐛 Troubleshooting

### **Erreur : Module not found**
```bash
pip install pandas faker
```

### **Erreur : Permission denied**
```bash
# Vérifier les droits d'écriture dans le dossier
chmod 755 .
```

### **Pas de radiations générées**
- ✅ Vérifier qu'il existe des inscriptions dans `ficp_data/`
- ✅ Lancer d'abord `GenerateMonthWithRadiation.py` pour créer l'historique
- ✅ Les radiations nécessitent 30+ jours d'ancienneté

## 🔄 Régénération

Pour régénérer toutes les données :
```bash
# Supprimer les données existantes
rm -rf ficp_data/
rm *.csv

# Régénérer l'historique complet
python GenerateMonthWithRadiation.py

# Générer les données du jour
python GenerateWithRadiation.py
```

---
*Générateur FICP pour projet de certification Data Engineer*