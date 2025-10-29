# PROJET DATA LAKE E7 - CERTIFICATION DATA ENGINEER

## 🎯 Objectif
Déploiement d'un Data Lake Azure complet pour la certification Data Engineer (Étape 7/7).

## 📁 Structure du Projet

```
E7_certif/
├── DataLakeE7/           # Scripts de génération des données FICP
│   ├── GenerateWithRadiation.py    # Script principal de génération
│   ├── LocalDataLake.py            # Simulation locale
│   └── ficp_data/                  # Données générées
├── Infrastructure/       # Templates Azure
│   ├── main.bicep                  # Template principal Bicep
│   └── deploy.ps1                  # Script de déploiement
├── Architecture/         # Documentation
└── deploy-azure-e7.ps1   # Script de déploiement unifié
```

## 🚀 Déploiement Rapide

### Prérequis
- Compte Azure avec accès GitHub Student
- PowerShell avec module Az installé
- Accès à un abonnement Azure

### Étapes de Déploiement

1. **Connexion Azure**
   ```powershell
   Connect-AzAccount
   ```

2. **Déploiement automatique**
   ```powershell
   .\deploy-azure-e7.ps1
   ```

## 🏗️ Architecture Déployée

### Ressources Azure Créées
- **Azure Data Lake Gen2** : Stockage des données FICP
- **Azure Data Factory** : Orchestration des pipelines
- **Azure Key Vault** : Gestion des secrets
- **Azure Function** : Traitement des données
- **Azure Purview** : Gouvernance des données (optionnel)

### Services Utilisés (Niveau Gratuit)
- Data Lake Gen2 : 5GB gratuit permanent
- Data Factory : 5 pipelines gratuit permanent  
- Functions : 1M exécutions/mois gratuit
- Key Vault : 10,000 opérations gratuites/mois

## 📊 Données FICP

Le projet génère des données FICP réalistes :
- **Consultations** : Demandes de crédit
- **Courriers** : Correspondances bancaires  
- **Radiations** : Fins d'incidents de paiement

### Génération des Données
```bash
cd DataLakeE7
python GenerateWithRadiation.py
```

## 🔧 Configuration

### Variables d'Environnement
- `RESOURCE_GROUP_NAME` : rg-datalake-e7
- `LOCATION` : West Europe
- `PROJECT_NAME` : e7certif

### Personnalisation
Modifiez les paramètres dans `Infrastructure/main.bicep` selon vos besoins.

## 📈 Utilisation pour la Certification

### Cas d'Usage Couverts
1. **Ingestion** : Upload de données CSV vers Data Lake
2. **Transformation** : Pipelines Data Factory
3. **Stockage** : Organisation en zones (raw, processed, curated)
4. **Gouvernance** : Métadonnées et lineage avec Purview
5. **Sécurité** : Contrôle d'accès et chiffrement

### Démonstration
1. Générez des données FICP localement
2. Déployez l'infrastructure Azure
3. Uploadez les données vers Data Lake Gen2
4. Créez des pipelines de transformation
5. Analysez avec des outils de BI

## 💰 Coûts

### Période d'Essai (30 jours)
- Crédits gratuits : 200€
- Coût estimé du projet : 15-30€
- **Largement couvert par les crédits gratuits**

### Après 30 Jours (Permanent)
- Data Lake Gen2 : Gratuit jusqu'à 5GB
- Data Factory : Gratuit jusqu'à 5 pipelines
- Functions : Gratuit jusqu'à 1M exécutions/mois
- **Coût total : 0€ pour usage certification**

## 🎓 Validation Certification

### Points Évalués
- [x] Architecture Data Lake complète
- [x] Ingestion de données réelles
- [x] Pipelines de transformation
- [x] Gouvernance et sécurité
- [x] Monitoring et observabilité

### Livrables
- Infrastructure déployée sur Azure
- Documentation d'architecture
- Scripts de génération de données
- Pipelines de traitement
- Preuves de fonctionnement

## 🔍 Troubleshooting

### Problèmes Courants
1. **Erreur d'authentification** : Vérifiez `Get-AzContext`
2. **Permissions insuffisantes** : Contactez l'administrateur Azure
3. **Quotas dépassés** : Vérifiez les limites de l'abonnement

### Support
- Documentation Azure : [docs.microsoft.com](https://docs.microsoft.com/azure)
- Communauté : [Stack Overflow](https://stackoverflow.com/questions/tagged/azure)

---

**🎉 Projet optimisé pour la réussite de votre certification Data Engineer !**