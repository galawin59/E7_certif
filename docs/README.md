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

## Générer les données
PowerShell:
```
python scripts\generate_ficp_data.py
```

## Lancer les tests
PowerShell:
```
python -m pytest -q
```

## Gouvernance (extrait)
- RGPD: cle_bdf pseudonymisées
- Cycle de vie: fichiers quotidiens immutables, régénération idempotente
- Accès: lecture seule pour BI, écriture via processus contrôlé
