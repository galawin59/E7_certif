# GUIDE POWER BI POUR DATA WAREHOUSE FICP
# Connexion et utilisation de la base SQLite

## 📊 CONNEXION POWER BI DESKTOP

### Étape 1 : Ouvrir Power BI Desktop
1. Lancez Power BI Desktop
2. Cliquez sur "Obtenir des données" → "Plus..."
3. Recherchez "SQLite" ou sélectionnez "Base de données" → "Base de données SQLite"

### Étape 2 : Connexion à la base
**Chemin de la base de données :**
```
C:\Users\Galawin\Documents\GitHub\E7_certif\DataLakeE7\ficp_datawarehouse.db
```

### Étape 3 : Sélection des tables
**Tables principales à importer :**
- ✅ `ConsultationsFICP` (76,740 enregistrements)
- ✅ `InscriptionsFICP` (15,082 enregistrements)  
- ✅ `RadiationsFICP` (3,454 enregistrements)
- ✅ `KPIDashboardFICP` (1 enregistrement)

**Vues d'analyse à importer :**
- ✅ `VW_ConsultationsMonsuelles`
- ✅ `VW_AnalyseSecteurs`
- ✅ `VW_RisquesRegion`
- ✅ `VW_PowerBI_Consultations` (vue optimisée)
- ✅ `VW_PowerBI_Entreprises` (table de dimension)

---

## 🎯 MODELE DE DONNEES RECOMMANDE

### Relations entre tables
```
ConsultationsFICP (1) ←→ (N) InscriptionsFICP [NumeroSIREN]
ConsultationsFICP (1) ←→ (N) RadiationsFICP [NumeroSIREN]
InscriptionsFICP (1) ←→ (N) RadiationsFICP [NumeroSIREN]
```

### Colonnes clés pour les relations
- **Clé primaire :** `NumeroSIREN` (dans toutes les tables)
- **Dates :** `DateConsultation`, `DateInscription`, `DateRadiation`
- **Montants :** `MontantDemande`, `MontantIncident`, `MontantRembourse`

---

## 📈 MESURES DAX RECOMMANDEES

### KPI Principaux
```dax
// Nombre total de consultations
Total Consultations = COUNTROWS(ConsultationsFICP)

// Montant total des demandes
Montant Total Demandes = SUM(ConsultationsFICP[MontantDemande])

// Taux d'acceptation
Taux Acceptation = 
DIVIDE(
    COUNTROWS(FILTER(ConsultationsFICP, ConsultationsFICP[StatutDemande] = "Favorable")),
    COUNTROWS(ConsultationsFICP)
) * 100

// Score risque moyen
Score Risque Moyen = AVERAGE(ConsultationsFICP[ScoreRisque])

// Montant moyen par consultation
Montant Moyen = AVERAGE(ConsultationsFICP[MontantDemande])
```

### Mesures temporelles
```dax
// Consultations mois précédent
Consultations Mois Précédent = 
CALCULATE(
    COUNTROWS(ConsultationsFICP),
    DATEADD(ConsultationsFICP[DateConsultation], -1, MONTH)
)

// Évolution mensuelle
Evolution Mensuelle = 
VAR ConsultationsActuelles = COUNTROWS(ConsultationsFICP)
VAR ConsultationsPrecedentes = [Consultations Mois Précédent]
RETURN
DIVIDE(ConsultationsActuelles - ConsultationsPrecedentes, ConsultationsPrecedentes) * 100

// Moyenne mobile 7 jours
Moyenne Mobile 7j = 
AVERAGEX(
    LAST(7, ALLSELECTED(ConsultationsFICP[DateConsultation])),
    COUNTROWS(ConsultationsFICP)
)
```

---

## 🎨 VISUALISATIONS RECOMMANDEES

### Page 1 : Dashboard Exécutif
1. **KPI Cards :**
   - Total Consultations
   - Montant Total Demandes (€)
   - Taux Acceptation (%)
   - Score Risque Moyen

2. **Graphiques temporels :**
   - Ligne : Évolution mensuelle des consultations
   - Barres : Montants par mois
   - Aire : Taux d'acceptation dans le temps

3. **Répartitions :**
   - Secteurs Camembert : Types de crédit
   - Barres horizontales : Top régions

### Page 2 : Analyse des Risques
1. **Distribution des scores :**
   - Histogramme : Distribution des scores de risque
   - Scatter : Score vs Montant demandé
   
2. **Heatmap :**
   - Matrice : Région × Secteur × Taux de refus

3. **Funnel :**
   - Entonnoir : Consultation → Acceptation → Inscription

### Page 3 : Analyse Sectorielle
1. **Performance par secteur :**
   - Table : Détail par secteur d'activité
   - Treemap : Répartition des montants
   
2. **Comparaisons :**
   - Barres groupées : Acceptation vs Refus par secteur
   - Waterfall : Impact de chaque secteur

### Page 4 : Suivi des Incidents
1. **Lifecycle des incidents :**
   - Sankey : Consultation → Inscription → Radiation
   
2. **Analyses temporelles :**
   - Timeline : Durée moyenne des inscriptions
   - Calendrier : Pic d'activité par jour

---

## 🔍 FILTRES ET SLICERS RECOMMANDES

### Filtres temporels
- **Année** (dropdown)
- **Trimestre** (boutons)
- **Mois** (slider)
- **Période personnalisée** (date range)

### Filtres business
- **Région Entreprise** (multiple select)
- **Secteur Activité** (hierarchy)
- **Type Crédit** (checkboxes)
- **Catégorie Montant** (buttons)
- **Statut Demande** (toggle)

### Filtres avancés
- **Score Risque** (range slider : 0-1000)
- **Montant Demande** (range slider)
- **Nom Entreprise** (search box)

---

## 📊 REQUETES SQL POUR POWER BI

### Table de faits optimisée
```sql
-- Utiliser cette requête comme source personnalisée
SELECT 
    c.*,
    strftime('%Y', c.DateConsultation) as Annee,
    strftime('%m', c.DateConsultation) as Mois,
    CASE 
        WHEN c.MontantDemande < 5000 THEN 'Petit'
        WHEN c.MontantDemande < 50000 THEN 'Moyen'
        WHEN c.MontantDemande < 200000 THEN 'Gros'
        ELSE 'Très Gros'
    END as Categorie_Montant
FROM ConsultationsFICP c
```

### Dimensions enrichies
```sql
-- Table des entreprises avec historique
SELECT DISTINCT
    NumeroSIREN,
    NomEntreprise,
    RegionEntreprise,
    SecteurActivite,
    COUNT(*) as Nb_Consultations,
    AVG(MontantDemande) as Montant_Moyen,
    AVG(ScoreRisque) as Score_Moyen
FROM ConsultationsFICP
GROUP BY NumeroSIREN, NomEntreprise, RegionEntreprise, SecteurActivite
```

---

## ⚡ OPTIMISATIONS PERFORMANCE

### Paramètres Power BI
1. **Actualisation :**
   - Mode DirectQuery pour données temps réel
   - Import pour meilleures performances

2. **Modélisation :**
   - Créer table de dates dédiée
   - Utiliser les vues pré-agrégées
   - Index sur les colonnes de jointure

3. **Visualisations :**
   - Limiter le nombre de visuels par page
   - Utiliser des agrégations
   - Paginer les grandes tables

### Requêtes optimisées
```sql
-- Top N avec LIMIT pour performance
SELECT * FROM VW_AnalyseSecteurs LIMIT 20;

-- Agrégations pré-calculées
SELECT * FROM KPIDashboardFICP;

-- Filtres sur dates indexées
SELECT * FROM ConsultationsFICP 
WHERE DateConsultation >= '2025-01-01';
```

---

## 🚀 DEPLOIEMENT ET PARTAGE

### Power BI Service
1. **Publication :**
   - Publier vers workspace dédié
   - Configurer actualisation automatique
   - Paramétrer sécurité ligne par ligne

2. **Partage :**
   - Créer des applications Power BI
   - Configurer RLS (Row Level Security)
   - Exporter vers SharePoint/Teams

### Alertes et abonnements
```dax
// Alerte si taux acceptation < 60%
Alerte Taux Acceptation = 
IF([Taux Acceptation] < 60, "🔴 CRITIQUE", "✅ NORMAL")

// Alerte volume quotidien anormal
Alerte Volume = 
IF([Total Consultations] < [Moyenne Mobile 7j] * 0.7, "⚠️ FAIBLE", "📈 NORMAL")
```

---

## 💡 CONSEILS AVANCES

### Sécurité des données
- Masquer colonnes sensibles (scores détaillés)
- RLS par région/secteur selon utilisateur
- Audit trail des accès aux données

### Analyses prédictives
- Utiliser Python/R dans Power BI pour ML
- Prédiction des défauts de paiement
- Scoring automatique des nouvelles demandes

### Intégrations
- API REST pour données temps réel  
- Connexion Azure SQL Database
- Synchronisation avec CRM/ERP

---

## 🎯 RESULTATS ATTENDUS

**Votre Data Warehouse SQLite professionnel permet :**
- 📊 **95,277 enregistrements** dans de vraies tables relationnelles
- 🔍 **Requêtes SQL complexes** avec jointures et agrégations
- 📈 **Power BI natif** avec relations automatiques
- ⚡ **Performances optimales** grâce aux index
- 🎨 **Dashboards interactifs** avec drill-down
- 📱 **Compatible mobile** via Power BI apps

**C'est un vrai Data Warehouse prêt pour la production ! 🚀**