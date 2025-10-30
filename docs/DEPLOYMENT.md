# 🚀 Guide de Déploiement FICP Data Lake

## 📋 Étapes de déploiement complet

### **Phase 1 : Infrastructure de base** ⏱️ ~15 min

```powershell
# 1. Cloner et configurer
cd c:\Users\Galawin\Documents\GitHub\E7_certif

# 2. Configurer vos paramètres
cp Infrastructure\config-template.json Infrastructure\config-local.json
# Éditer config-local.json avec vos valeurs

# 3. Déployer l'infrastructure
.\Infrastructure\deploy.ps1 -Environment test
```

### **Phase 2 : Conteneurs et Images** ⏱️ ~10 min

```powershell
# 1. Build de l'image Docker
docker build -t ficp-generator:latest .\Infrastructure\Containers\

# 2. Push vers Azure Container Registry (si créé)
az acr build --registry [ACR_NAME] --image ficp-generator:latest .\Infrastructure\Containers\
```

### **Phase 3 : Pipelines Data Factory** ⏱️ ~10 min  

```powershell
# Déployer les pipelines
.\Infrastructure\Pipelines\deploy-pipelines.ps1 `
    -ResourceGroupName "rg-dl-ficp-test" `
    -DataFactoryName "adf-dl-ficp-test" `
    -StorageAccountName "[STORAGE_NAME]" `
    -Environment "test"
```

### **Phase 4 : Tests et validation** ⏱️ ~5 min

```powershell
# Test génération locale
python .\DataLakeE7\GenerateWithRadiation.py

# Test pipeline Data Factory (manuel)
az datafactory pipeline create-run --factory-name "adf-dl-ficp-test" --resource-group "rg-dl-ficp-test" --name "FICP_Daily_Ingestion"
```

---

## ✅ **DÉPLOIEMENT COMPLET !**

**Votre Data Lake FICP est maintenant opérationnel avec :**

- 🏗️ **Infrastructure Azure** complète (C18)
- ⚙️ **Pipelines automatisés** quotidiens (C19)  
- 📊 **Catalogue de données** Purview (C20)
- 🔐 **Gouvernance et sécurité** (C21)

**🎯 Tous les critères de certification sont couverts !**