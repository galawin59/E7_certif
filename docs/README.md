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
