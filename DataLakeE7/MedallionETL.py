#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline ETL Medallion pour Data Lake FICP
Bronze -> Silver -> Gold transformations
Certification E7 - Data Engineer
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

class FICPMedallionETL:
    """Pipeline ETL pour architecture Medallion FICP"""
    
    def __init__(self):
        self.today = datetime.now()
        self.date_str = self.today.strftime('%Y-%m-%d')
        
        # Configuration des chemins locaux (simulation Azure)
        self.bronze_path = "DataLakeE7/bronze"
        self.silver_path = "DataLakeE7/silver" 
        self.gold_path = "DataLakeE7/gold"
        self.logs_path = "DataLakeE7/logs"
        
        # Création des dossiers
        for path in [self.bronze_path, self.silver_path, self.gold_path, self.logs_path]:
            os.makedirs(path, exist_ok=True)
            
        # Configuration logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def bronze_layer_ingestion(self):
        """Ingestion des données brutes dans Bronze Layer"""
        self.logger.info("=== BRONZE LAYER INGESTION ===")
        
        # Déplacement des données existantes vers Bronze
        source_files = [
            f"DataLakeE7/ficp_consultation_test_{self.date_str}.csv",
            f"DataLakeE7/ficp_courrier_test_{self.date_str}.csv",
            f"DataLakeE7/ficp_radiation_test_{self.date_str}.csv"
        ]
        
        bronze_files = []
        for source_file in source_files:
            if os.path.exists(source_file):
                # Nom du fichier en Bronze avec partitioning par date
                base_name = os.path.basename(source_file)
                data_type = base_name.split('_')[1]  # consultation, courrier, radiation
                
                bronze_file = f"{self.bronze_path}/{data_type}/year={self.today.year}/month={self.today.month:02d}/day={self.today.day:02d}/{base_name}"
                
                # Création des dossiers de partitioning
                os.makedirs(os.path.dirname(bronze_file), exist_ok=True)
                
                # Copie vers Bronze (simulation du mouvement Azure)
                df = pd.read_csv(source_file)
                df.to_csv(bronze_file, index=False)
                bronze_files.append(bronze_file)
                
                self.logger.info(f"Bronze ingestion: {bronze_file}")
                
        return bronze_files
    
    def silver_layer_transformation(self, bronze_files):
        """Transformation et nettoyage pour Silver Layer"""
        self.logger.info("=== SILVER LAYER TRANSFORMATION ===")
        
        silver_files = []
        
        for bronze_file in bronze_files:
            try:
                df = pd.read_csv(bronze_file)
                data_type = bronze_file.split('/')[-5]  # consultation, courrier, radiation
                
                # Transformations spécifiques par type
                if data_type == 'consultation':
                    df = self._clean_consultations(df)
                elif data_type == 'courrier':
                    df = self._clean_courriers(df)
                elif data_type == 'radiation':
                    df = self._clean_radiations(df)
                
                # Ajout de colonnes metadata
                df['processed_date'] = self.today
                df['data_quality_score'] = self._calculate_quality_score(df)
                df['source_file'] = os.path.basename(bronze_file)
                
                # Sauvegarde en Silver (Parquet simulation)
                silver_file = f"{self.silver_path}/{data_type}_cleaned/year={self.today.year}/month={self.today.month:02d}/{data_type}_cleaned_{self.date_str}.parquet"
                os.makedirs(os.path.dirname(silver_file), exist_ok=True)
                
                # Simulation Parquet avec CSV pour compatibilité
                df.to_csv(silver_file.replace('.parquet', '.csv'), index=False)
                silver_files.append(silver_file.replace('.parquet', '.csv'))
                
                self.logger.info(f"Silver transformation: {silver_file}")
                
            except Exception as e:
                self.logger.error(f"Erreur Silver transformation {bronze_file}: {e}")
                
        return silver_files
    
    def gold_layer_aggregation(self, silver_files):
        """Agrégation business pour Gold Layer"""
        self.logger.info("=== GOLD LAYER AGGREGATION ===")
        
        gold_files = []
        
        # KPI 1: Résumé mensuel des consultations
        consultations_files = [f for f in silver_files if 'consultation' in f]
        if consultations_files:
            kpi_consultations = self._create_consultation_kpis(consultations_files)
            gold_file = f"{self.gold_path}/kpi_consultations_monthly/kpi_consultations_{self.today.year}_{self.today.month:02d}.csv"
            os.makedirs(os.path.dirname(gold_file), exist_ok=True)
            kpi_consultations.to_csv(gold_file, index=False)
            gold_files.append(gold_file)
            self.logger.info(f"Gold KPI consultations: {gold_file}")
        
        # KPI 2: Dashboard incidents FICP
        all_data = []
        for silver_file in silver_files:
            df = pd.read_csv(silver_file)
            df['data_type'] = silver_file.split('/')[-3].replace('_cleaned', '')
            all_data.append(df)
        
        if all_data:
            dashboard_data = self._create_ficp_dashboard(all_data)
            gold_file = f"{self.gold_path}/reporting_ficp_dashboard/ficp_dashboard_{self.date_str}.csv"
            os.makedirs(os.path.dirname(gold_file), exist_ok=True)
            dashboard_data.to_csv(gold_file, index=False)
            gold_files.append(gold_file)
            self.logger.info(f"Gold dashboard: {gold_file}")
        
        return gold_files
    
    def _clean_consultations(self, df):
        """Nettoyage spécifique des consultations"""
        # Standardisation des montants
        df['montant_demande'] = pd.to_numeric(df['montant_demande'], errors='coerce')
        # Nettoyage des dates
        df['date_consultation'] = pd.to_datetime(df['date_consultation'], errors='coerce')
        # Validation SIREN (9 chiffres)
        df['siren_valide'] = df['numero_siren'].str.len() == 9
        return df.dropna(subset=['date_consultation'])
    
    def _clean_courriers(self, df):
        """Nettoyage spécifique des courriers"""
        df['date_envoi'] = pd.to_datetime(df['date_envoi'], errors='coerce')
        df['objet_clean'] = df['objet'].str.strip()
        return df.dropna(subset=['date_envoi'])
    
    def _clean_radiations(self, df):
        """Nettoyage spécifique des radiations"""
        df['date_radiation'] = pd.to_datetime(df['date_radiation'], errors='coerce')
        df['montant_solde'] = pd.to_numeric(df['montant_solde'], errors='coerce')
        return df.dropna(subset=['date_radiation'])
    
    def _calculate_quality_score(self, df):
        """Calcule un score de qualité des données"""
        non_null_ratio = df.count().sum() / (len(df) * len(df.columns))
        return round(non_null_ratio * 100, 2)
    
    def _create_consultation_kpis(self, files):
        """Crée les KPI mensuels des consultations"""
        all_consultations = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
        
        kpis = pd.DataFrame({
            'periode': [f"{self.today.year}-{self.today.month:02d}"],
            'nb_consultations_total': [len(all_consultations)],
            'nb_consultations_favorables': [len(all_consultations[all_consultations['resultat'] == 'Favorable'])],
            'montant_moyen_demande': [all_consultations['montant_demande'].mean()],
            'taux_acceptation': [len(all_consultations[all_consultations['resultat'] == 'Favorable']) / len(all_consultations) * 100],
            'qualite_donnees_moyenne': [all_consultations['data_quality_score'].mean()]
        })
        
        return kpis
    
    def _create_ficp_dashboard(self, data_list):
        """Crée les données du dashboard FICP"""
        combined_df = pd.concat(data_list, ignore_index=True)
        
        dashboard = pd.DataFrame({
            'date_rapport': [self.today],
            'total_enregistrements': [len(combined_df)],
            'types_donnees': [combined_df['data_type'].nunique()],
            'score_qualite_global': [combined_df['data_quality_score'].mean()],
            'periode_couverte': [f"{combined_df['processed_date'].min()} à {combined_df['processed_date'].max()}"]
        })
        
        return dashboard
    
    def create_execution_log(self, bronze_files, silver_files, gold_files):
        """Crée le log d'exécution"""
        execution_log = {
            'execution_date': self.today.isoformat(),
            'pipeline_version': '1.0',
            'bronze_files_processed': len(bronze_files),
            'silver_files_created': len(silver_files),
            'gold_files_created': len(gold_files),
            'status': 'SUCCESS',
            'files_detail': {
                'bronze': bronze_files,
                'silver': silver_files,
                'gold': gold_files
            }
        }
        
        log_file = f"{self.logs_path}/pipeline_execution_{self.date_str}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(execution_log, f, indent=2, default=str)
        
        self.logger.info(f"Log d'execution cree: {log_file}")
        return log_file
    
    def run_full_pipeline(self):
        """Exécute le pipeline ETL complet"""
        self.logger.info("=== DEBUT PIPELINE ETL MEDALLION FICP ===")
        
        try:
            # Bronze Layer
            bronze_files = self.bronze_layer_ingestion()
            
            # Silver Layer  
            silver_files = self.silver_layer_transformation(bronze_files)
            
            # Gold Layer
            gold_files = self.gold_layer_aggregation(silver_files)
            
            # Logs
            log_file = self.create_execution_log(bronze_files, silver_files, gold_files)
            
            self.logger.info("=== PIPELINE ETL TERMINE AVEC SUCCES ===")
            
            return {
                'status': 'SUCCESS',
                'bronze_files': len(bronze_files),
                'silver_files': len(silver_files), 
                'gold_files': len(gold_files),
                'log_file': log_file
            }
            
        except Exception as e:
            self.logger.error(f"ERREUR PIPELINE: {e}")
            return {'status': 'FAILED', 'error': str(e)}

if __name__ == "__main__":
    # Exécution du pipeline ETL
    etl = FICPMedallionETL()
    result = etl.run_full_pipeline()
    
    print("\n" + "="*50)
    print("RESULTATS PIPELINE ETL MEDALLION")
    print("="*50)
    print(f"Status: {result['status']}")
    if result['status'] == 'SUCCESS':
        print(f"Bronze files: {result['bronze_files']}")
        print(f"Silver files: {result['silver_files']}")
        print(f"Gold files: {result['gold_files']}")
        print("ARCHITECTURE MEDALLION COMPLETE !")
    else:
        print(f"Erreur: {result.get('error', 'Inconnue')}")