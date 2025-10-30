# 🚀 GUIDE DE DÉMARRAGE RAPIDE - E7 CERTIFICATION

## ⚡ **INSTALLATION EXPRESS (5 MINUTES)**

### **1️⃣ Prérequis Rapides**
```powershell
# Vérification PowerShell (requis: 5.1+)
$PSVersionTable.PSVersion

# Installation Python (si nécessaire)
# Télécharger: https://www.python.org/downloads/

# Installation Azure CLI (optionnel)
# Télécharger: https://docs.microsoft.com/cli/azure/install-azure-cli
```

### **2️⃣ Installation Automatique**
```powershell
# Cloner le projet
git clone <repository-url>
cd E7_certif

# Installation complète automatique
.\Install-E7Certification.ps1 -Mode all

# OU installation étape par étape
.\Install-E7Certification.ps1 -Mode setup     # Dépendances
.\Install-E7Certification.ps1 -Mode deploy    # Azure
.\Install-E7Certification.ps1 -Mode import    # Données
.\Install-E7Certification.ps1 -Mode validate  # Tests
```

### **3️⃣ Validation Rapide**
```powershell
# Test de l'installation
.\scripts\validation\Invoke-E7ValidationComplete.ps1

# Vérification Azure SQL
Invoke-Sqlcmd -ServerInstance "sql-server-ficp-5647.database.windows.net" `
              -Database "db-ficp-datawarehouse" `
              -Username "ficpadmin" `
              -Password "FicpDataWarehouse2025!" `
              -Query "SELECT COUNT(*) FROM ConsultationsFICP"
```

---

## 🎯 **POINTS DE CONTRÔLE CERTIFICATION**

### **✅ Architecture Medallion**
- [ ] Dossiers Bronze/Silver/Gold créés
- [ ] Pipeline ETL fonctionnel  
- [ ] Données de qualité importées

### **✅ Infrastructure Azure**
- [ ] Azure SQL Database déployée
- [ ] Storage Account configuré
- [ ] Connexions validées

### **✅ Business Intelligence**
- [ ] Tables optimisées pour Power BI
- [ ] Requêtes complexes testées
- [ ] KPIs calculés automatiquement

### **✅ Documentation**
- [ ] README complet
- [ ] Architecture documentée
- [ ] Guide Power BI disponible

---

## 🔗 **CONNEXIONS ESSENTIELLES**

### **Azure SQL Database**
- **Serveur**: `sql-server-ficp-5647.database.windows.net`
- **Base**: `db-ficp-datawarehouse`  
- **Login**: `ficpadmin` / `FicpDataWarehouse2025!`

### **Tables Principales**
- `ConsultationsFICP` : Demandes de crédit
- `InscriptionsFICP` : Incidents de paiement
- `RadiationsFICP` : Résolutions d'incidents
- `KPIDashboardFICP` : Métriques consolidées

---

## 🆘 **DÉPANNAGE RAPIDE**

### **Erreur de Connexion Azure SQL**
```powershell
# Test de connectivité
Test-NetConnection sql-server-ficp-5647.database.windows.net -Port 1433

# Réinstallation module SQL
Install-Module SqlServer -Force -AllowClobber
```

### **Erreur Python**
```bash
# Réactivation environnement virtuel
.\.venv\Scripts\Activate.ps1

# Réinstallation dépendances
pip install -r requirements.txt
```

### **Données Non Importées**
```python
# Import manuel
python scripts\data-processing\import-azure-professional.py

# Génération nouvelles données
python DataLakeE7\GenerateProfessionalData.py
```

---

## 📞 **SUPPORT ET RESSOURCES**

- 📖 **Documentation**: `docs/`
- 🔧 **Scripts**: `scripts/`
- ⚙️ **Configuration**: `config/`
- 📊 **Guide Power BI**: `docs/GUIDE-POWER-BI.md`

**🎉 EN CAS DE SUCCÈS : Votre projet E7 est prêt pour la certification !**