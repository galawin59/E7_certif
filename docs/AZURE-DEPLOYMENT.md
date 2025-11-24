# Azure deployment – Automation for daily FICP lake

Ce document décrit le déploiement de l’automatisation quotidienne avec Azure Automation (sans Azure Functions), pour générer et déposer chaque jour 3 CSV (consultation, inscription, radiation) dans ADLS Gen2.

Prerequisites:
- Azure CLI installé et connecté: `az login`
- Resource group: `rg-datalake-ficp`
- Compte de stockage existant: `stficpdata330940` (container `ficp` créé automatiquement par le runbook si absent)

## Provisioning en une commande (recommandé)
Depuis la racine du repo:
```
powershell -ExecutionPolicy Bypass -File scripts\automation\provision_automation_account_cli.ps1 `
  -ResourceGroup rg-datalake-ficp `
  -PreferredLocation northeurope `
  -AutomationAccountName aa-ficp-daily `
  -RunbookName ficp-daily `
  -ScheduleName ficp-daily-0630 `
  -RunbookPath scripts/automation/runbook_ficp_daily_azure.ps1 `
  -TimeZone "Central European Standard Time" `
  -StorageAccountName stficpdata330940 `
  -ContainerName ficp
```
Ce script effectue:
1) Création (ou vérification) de l’Automation Account (régions autorisées Free/Student gérées: eastus/eastus2/westus/northeurope/southeastasia/japanwest)
2) Activation de l’identité managée + rôle "Storage Blob Data Contributor" sur le compte de stockage
3) Import + publication du runbook `runbook_ficp_daily_azure.ps1`
4) Création du schedule quotidien 06:30 (CET)
5) Lien runbook ↔ schedule avec paramètres (StorageAccountName, ContainerName)

Validation:
```
az automation job list --automation-account-name aa-ficp-daily --resource-group rg-datalake-ficp
```
Le schedule crée un job chaque jour à 06:30. Vous pouvez aussi déclencher manuellement:
```
az automation runbook start --automation-account-name aa-ficp-daily --resource-group rg-datalake-ficp `
  --name ficp-daily --parameters StorageAccountName=stficpdata330940 ContainerName=ficp Overwrite=true
```

## Détails du runbook
Le runbook PowerShell génère les CSV du jour de manière déterministe (hash -> délais/probas), écrit localement puis uploade vers `stficpdata330940/f icp` via Az.Storage. En Automation il s’authentifie via identité managée.

Paramètres utiles:
- `TargetDate` (yyyy-MM-dd) pour rattrapage
- `Overwrite` pour régénérer un jour existant
- `SkipUpload` pour un test logique sans envoi

## Anciennes approches (legacy)
- Azure Function (Timer): supprimée (problèmes de trigger)
- Logic App: non nécessaire; la planification est assurée par le schedule d’Automation

## Dépannage rapide
- Erreur de région à la création de l’Automation Account: le script bascule automatiquement vers une région autorisée.
- Droits Blob manquants: vérifier IAM du compte de stockage (rôle Storage Blob Data Contributor) sur l’identité du compte Automation.
- Fichiers non visibles: vérifier l’horaire local/zone, l’historique des jobs Automation et les messages du runbook.
