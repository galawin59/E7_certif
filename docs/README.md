# FICP Data Lake simulé (E7 Bloc 4)

Ce projet génère un data lake simulé FICP avec 3 flux quotidiens (consultation, inscription, radiation) du 01/01/2025 au 13/11/2025.

## Arborescence
```
ficp_data_lake/
  consultation/YYYY-MM-DD.csv
  inscription/YYYY-MM-DD.csv
  radiation/YYYY-MM-DD.csv
```

## Schémas
- consultation.csv: cle_bdf, date_consultation, statut_ficp, date_surveillance, date_inscription
- inscription.csv: cle_bdf, statut_ficp, type_incident, date_surveillance, date_inscription
- radiation.csv: cle_bdf, date_inscription, date_radiation, type_incident

## Règles métier
- INSCRIT (PAIEMENT) après SURVEILLANCE entre J+31 et J+37
- SURENDETTEMENT => INSCRIT direct (pas de SURVEILLANCE)
- Pas de SURVEILLANCE avec type_incident = SURENDETTEMENT
- Radiation (70%) ~20 jours après inscription

## Exécution Azure quotidienne sans Azure Functions (Azure Automation)
Nous utilisons un Runbook Azure Automation (pas de Logic App requise) planifié à 06:30 (CET).

Résumé:
1. Runbook PowerShell (`scripts/automation/runbook_ficp_daily_azure.ps1`) génère les 3 CSV du jour et les pousse dans ADLS Gen2.
2. Identité managée du compte Automation avec rôle "Storage Blob Data Contributor" sur le compte de stockage.
3. Un schedule Automation démarre le runbook tous les jours à 06:30.

Provisioning en une commande (voir détails dans `docs/AZURE-DEPLOYMENT.md`):
```
powershell -ExecutionPolicy Bypass -File scripts\automation\provision_automation_account_cli.ps1 `
  -ResourceGroup rg-datalake-ficp -PreferredLocation northeurope `
  -AutomationAccountName aa-ficp-daily -RunbookName ficp-daily -ScheduleName ficp-daily-0630 `
  -RunbookPath scripts/automation/runbook_ficp_daily_azure.ps1 `
  -StorageAccountName stficpdata330940 -ContainerName ficp
```

Déclenchement manuel:
```
az automation runbook start --automation-account-name aa-ficp-daily --resource-group rg-datalake-ficp --name ficp-daily `
  --parameters StorageAccountName=stficpdata330940 ContainerName=ficp Overwrite=true
```

## Exploitation quotidienne (Azure Automation)

### Relancer manuellement un jour précis

Dans Cloud Shell ou ton terminal (après `az login`), pour regénérer les fichiers d'une date donnée et les pousser dans le data lake :

```powershell
$d = '2025-11-23'  # date cible au format YYYY-MM-DD
az automation runbook start `
  --automation-account-name aa-ficp-daily `
  --resource-group rg-datalake-ficp `
  --name ficp-daily `
  --parameters TargetDate=$d
```

Le runbook va :
- générer 3 fichiers CSV dans le répertoire temporaire de la VM d'exécution ;
- uploader les 3 fichiers vers le compte de stockage `stficpdata330940`, conteneur `ficp` ;
- écrire dans les logs les résumés suivants :
  - `SUMMARY LOCAL <date> -> consultations=... inscriptions=... radiations=... size_bytes_total=...`
  - `SUMMARY SIZES <date> -> consult=... inscr=... rad=...`
  - `SUMMARY REMOTE <date> -> consultations=... inscriptions=... radiations=... size_bytes_total=...`
  - `SUMMARY DURATION <date> -> seconds=...`

### Vérifier les derniers jobs et résumés

Lister les derniers jobs Automation :

```powershell
az automation job list `
  --automation-account-name aa-ficp-daily `
  --resource-group rg-datalake-ficp `
  --query "[].{name:name, status:status, start:startTime, end:endTime}" -o table
```

Récupérer les résumés pour un job précis via l’API REST :

```powershell
$subId  = az account show --query id -o tsv
$jobRes = 'REPLACE_WITH_JOB_RESOURCE_NAME'  # ex: 10046919-4264-43ef-89e0-e4f0845f36c6
$base   = "https://management.azure.com/subscriptions/$subId/resourceGroups/rg-datalake-ficp/providers/Microsoft.Automation/automationAccounts/aa-ficp-daily/jobs/$jobRes"

az rest --method get --url "$base/streams?api-version=2023-11-01"
```

Dans la réponse JSON, les champs `properties.summary` des streams de type `Output` contiennent les lignes `SUMMARY ...` décrivant le volume généré, la taille totale et la durée.

## Gouvernance (extrait)
- RGPD: cle_bdf pseudonymisées
- Cycle de vie: fichiers quotidiens immutables, régénération idempotente
- Accès: lecture seule pour BI, écriture via processus contrôlé

## Rapport E7 Bloc 4 – Plan des captures d'écran

Cette section te sert de guide pour ton dossier E7. Tu peux imprimer ce plan et simplement insérer les captures d'écran demandées au bon endroit.

### 1. Architecture globale du data lake
- **Texte à mettre** :
  - "Le data lake FICP est hébergé sur Azure Data Lake Storage Gen2, avec un conteneur unique `ficp` partitionné en trois zones métier : `consultation`, `inscription`, `radiation`. Les fichiers sont datés au format `YYYY-MM-DD.csv`."
- **Capture 1** – *Arborescence ADLS* :
  - Portail Azure → compte de stockage `stficpdata330940` → Explorateur de stockage → conteneur `ficp` montrant les dossiers `consultation/`, `inscription/`, `radiation/`.
<img width="1867" height="497" alt="image" src="https://github.com/user-attachments/assets/28524d06-f531-4e97-bd87-72464b85480e" />
<img width="962" height="825" alt="image" src="https://github.com/user-attachments/assets/0b93c7a3-07c1-4baa-a5f9-40e80e44c4b4" />


### 2. Génération quotidienne (Azure Automation)
- **Texte à mettre** :
  - "La génération quotidienne est orchestrée par un runbook PowerShell dans Azure Automation (`aa-ficp-daily`, runbook `ficp-daily`). Un schedule déclenche le runbook chaque jour à 06:30 (CET), sans intervention utilisateur ni poste allumé."
- **Capture 2** – *Automation Account* :
  - Vue d'ensemble de `aa-ficp-daily` avec la liste des runbooks et le runbook `ficp-daily` visible.
 <img width="1853" height="519" alt="image" src="https://github.com/user-attachments/assets/497e6ff6-ca67-4308-b0ca-aae0badd92fa" />



- **Capture 3** – *Détail du runbook* :
  - Onglet "Runbooks" → `ficp-daily` → onglet "Edit" ou "View" montrant rapidement le début du script (nom du fichier `runbook_ficp_daily_azure.ps1`).
 
<img width="1866" height="960" alt="image" src="https://github.com/user-attachments/assets/8fd49e25-c3d5-4669-af07-b9616a060e4d" />

- **Capture 4** – *Schedule quotidien* :
  - Sur `aa-ficp-daily`, onglet "Schedules" montrant le schedule lié au runbook (heure, récurrence quotidienne).
<img width="1867" height="806" alt="image" src="https://github.com/user-attachments/assets/2679e986-e8de-4a4b-9c82-58709a10d5cf" />

### 3. Suivi des traitements (résumés SUMMARY)
- **Texte à mettre** :
  - "Chaque exécution du runbook produit des résumés standardisés dans les logs (SUMMARY LOCAL / SIZES / REMOTE / DURATION) permettant de vérifier rapidement le volume généré, la taille totale et la durée du traitement."
- **Capture 5** – *Historique des jobs* :
  - Azure Automation → `aa-ficp-daily` → "Jobs" avec quelques exécutions `Completed`.
 <img width="1854" height="667" alt="image" src="https://github.com/user-attachments/assets/be09be48-fc14-4e68-a93d-8c394dcd4dc3" />

    
- **Capture 6** – *Détail d'un job* :
  - Détail d'un job → onglet "Logs" / "Output" avec les lignes du type :
    - `SUMMARY LOCAL 2025-.. -> consultations=... inscriptions=... radiations=...`
    - `SUMMARY REMOTE ...`
<img width="1854" height="613" alt="image" src="https://github.com/user-attachments/assets/667eb3c9-803b-46ea-880e-db88a7a598eb" />

### 4. Données générées (exemple concret)
- **Texte à mettre** :
  - "Les fichiers sont générés de manière déterministe selon des règles métier (délais PAIEMENT, probabilité de radiation, etc.). Un exemple de fichier permet d’illustrer la structure réelle des données."
- **Capture 7** – *Aperçu CSV* :
  - Dans le portail ou dans VS Code, un extrait de `consultation/2025-03-15.csv` (quelques lignes) montrant les colonnes et valeurs.
<img width="665" height="600" alt="image" src="https://github.com/user-attachments/assets/37dbe75b-a321-42f4-99ac-777066d2c328" />
<img width="606" height="598" alt="image" src="https://github.com/user-attachments/assets/c86a6182-26cb-4cde-b19c-0c531246cd9d" />
<img width="501" height="614" alt="image" src="https://github.com/user-attachments/assets/16f02137-26be-4c91-8abe-833e2b3e396e" />


### 5. Catalogue et gouvernance (Microsoft Purview)
- **Texte à mettre** :
  - "Un compte Microsoft Purview (`pv-ficp-e7`) est connecté au data lake `stficpdata330940`. Un scan Purview a été configuré pour analyser le conteneur `ficp` et alimenter automatiquement un catalogue technique des datasets FICP (consultation, inscription, radiation). L'accès au stockage est sécurisé via Azure Key Vault et une identité managée dédiée au compte Purview."
- **Capture 8** – *Source de données Purview* :
  - Governance Portal → Data sources → source `FICP-DataLake` avec au moins un scan `Succeeded` visible.
    <img width="1867" height="717" alt="image" src="https://github.com/user-attachments/assets/8d33a3b8-4aec-4f58-b75a-03f1d854a48e" />

- **Capture 9** – *Résultat de scan* :
  - Écran récapitulatif de la source montrant le dernier scan (nom, date, statut Succeeded).
- **Capture 10** – *Catalogue par collection* :
  - Data catalog → Browse → collection `pv-ficp-e7` montrant le nombre total d'assets (comme ta capture avec "Assets = 9").
    <img width="1865" height="405" alt="image" src="https://github.com/user-attachments/assets/c25fc527-773b-4e24-987e-8d01f2ff0499" />

- **Capture 11** – *Détails d'un dataset métier* :
  - Data catalog → recherche `ficp radiation` → ouvrir l'asset `radiation` (Resource Set) pour afficher :
    - le chemin `https://stficpdata330940.dfs.core.windows.net/ficp/radiation/{Year}-{Month}-{Day}.csv` ;
    - les colonnes détectées (statut_ficp, ficp, date_radiation, etc.).
    <img width="1870" height="546" alt="image" src="https://github.com/user-attachments/assets/6acc6077-f000-4421-aa77-c56fa145f9ed" />
    <img width="1855" height="567" alt="image" src="https://github.com/user-attachments/assets/4ac95014-89ec-463c-b13c-bd1cc5c8ade7" />
    <img width="1861" height="575" alt="image" src="https://github.com/user-attachments/assets/9ebbcc5a-0bf8-4094-9ed7-8fa8bc605c51" />



### 6. Synthèse gouvernance (C20–C21)
- **Texte à mettre** :
  - "Le couple Automation + Purview illustre la mise en conditions opérationnelles d’un data lake FICP :
    - alimentation quotidienne automatisée et vérifiable (résumés SUMMARY, logs de jobs) ;
    - stockage structuré et partitionné par flux métier ;
    - gouvernance via Microsoft Purview (catalogue centralisé des datasets, métadonnées techniques, historisation des scans) ;
    - sécurisation des accès par rôles RBAC et secrets gérés dans Key Vault."
- **Capture 12** – *Vue d'ensemble architecture* (optionnelle mais recommandée) :
  - Un schéma (PowerPoint ou dessiné à la main) montrant :
    - "Runbook Azure Automation" → "Data Lake ADLS Gen2 (ficp)" → "Microsoft Purview (catalogue)".
<img width="545" height="446" alt="image" src="https://github.com/user-attachments/assets/32ebefef-4eda-431c-bcbb-27a4630a8739" />

Avec ces 10–12 captures et les textes associés, tu peux raconter l’ensemble du projet sans avoir besoin d’un accès en direct à Azure le jour de la soutenance.
