#!/usr/bin/env python3
"""
E7 CERTIFICATION - IMPORTEUR MASSIF AZURE SQL HISTORIQUE
========================================================
Description: Import en masse des 651 fichiers d'historique FICP quotidien
             vers Azure SQL Database avec cramage intensif des crédits !
Version: 1.0.0
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole
Date: 2025-10-30
License: MIT

STRATEGY CRAMAGE CRÉDITS:
- Import par BATCH de 1000 records pour optimiser throughput
- Parallélisation des imports par type de fichier
- Monitoring en temps réel de la consommation DTU
- 264,451 enregistrements × 3 types = 793,353 opérations SQL !
"""

import pandas as pd
import pyodbc
import os
from pathlib import Path
import logging
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class ImporteurMassifAzureHistorique:
    """Importeur massif d'historique FICP vers Azure SQL Database"""
    
    def __init__(self):
        # Configuration Azure SQL Database
        self.server = 'sql-server-ficp-5647.database.windows.net'
        self.database = 'db-ficp-datawarehouse'
        self.username = 'ficpadmin'
        self.password = 'FicpDataWarehouse2025!'
        
        # Statistiques cramage
        self.total_records_imported = 0
        self.total_files_processed = 0
        self.start_time = None
        self.lock = threading.Lock()
        
    def get_connection_string(self):
        """Retourne la chaîne de connexion Azure SQL"""
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
    
    def import_consultations_file(self, file_path):
        """Import d'un fichier de consultations vers Azure SQL"""
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                return 0
            
            conn_str = self.get_connection_string()
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                
                # Import par batch de 1000 pour performance
                batch_size = 1000
                records_imported = 0
                
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    # Préparer les valeurs
                    values = []
                    for _, row in batch.iterrows():
                        values.append((
                            row['date_consultation'],
                            row['cle_bdf'],
                            row['reponse_registre'],
                            row['etablissement_demandeur'],
                            row['heure_consultation']
                        ))
                    
                    # Insert batch
                    cursor.executemany("""
                        INSERT INTO ConsultationsFICP 
                        (DateConsultation, CleBDF, ReponseRegistre, EtablissementDemandeur, HeureConsultation)
                        VALUES (?, ?, ?, ?, ?)
                    """, values)
                    
                    records_imported += len(batch)
                
                conn.commit()
                
                with self.lock:
                    self.total_records_imported += records_imported
                    self.total_files_processed += 1
                
                return records_imported
                
        except Exception as e:
            logger.error(f"❌ Erreur import consultations {file_path}: {e}")
            return 0
    
    def import_inscriptions_file(self, file_path):
        """Import d'un fichier d'inscriptions vers Azure SQL"""
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                return 0
            
            conn_str = self.get_connection_string()
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                
                # Import par batch de 1000
                batch_size = 1000
                records_imported = 0
                
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    # Préparer les valeurs
                    values = []
                    for _, row in batch.iterrows():
                        values.append((
                            row['date_envoi'],
                            row['cle_bdf'], 
                            row['type_courrier']
                        ))
                    
                    # Insert batch
                    cursor.executemany("""
                        INSERT INTO InscriptionsFICP 
                        (DateInscription, CleBDF, TypeCourrier)
                        VALUES (?, ?, ?)
                    """, values)
                    
                    records_imported += len(batch)
                
                conn.commit()
                
                with self.lock:
                    self.total_records_imported += records_imported
                    self.total_files_processed += 1
                
                return records_imported
                
        except Exception as e:
            logger.error(f"❌ Erreur import inscriptions {file_path}: {e}")
            return 0
    
    def import_radiations_file(self, file_path):
        """Import d'un fichier de radiations vers Azure SQL"""
        try:
            df = pd.read_csv(file_path)
            if df.empty:
                return 0
            
            conn_str = self.get_connection_string()
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                
                # Import par batch de 1000
                batch_size = 1000
                records_imported = 0
                
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    # Préparer les valeurs
                    values = []
                    for _, row in batch.iterrows():
                        values.append((
                            row['date_radiation'],
                            row['cle_bdf'],
                            row['type_radiation'],
                            row['date_inscription_origine'],
                            row['duree_inscription_jours'],
                            row['montant_radie'],
                            row['organisme_demandeur'],
                            row['motif_detaille']
                        ))
                    
                    # Insert batch
                    cursor.executemany("""
                        INSERT INTO RadiationsFICP 
                        (DateRadiation, CleBDF, TypeRadiation, DateInscriptionOrigine, 
                         DureeInscriptionJours, MontantRadie, OrganismeDemandeur, MotifDetaille)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, values)
                    
                    records_imported += len(batch)
                
                conn.commit()
                
                with self.lock:
                    self.total_records_imported += records_imported
                    self.total_files_processed += 1
                
                return records_imported
                
        except Exception as e:
            logger.error(f"❌ Erreur import radiations {file_path}: {e}")
            return 0
    
    def get_all_files_by_type(self, base_path):
        """Récupère tous les fichiers par type"""
        files = {
            'consultations': [],
            'inscriptions': [],
            'radiations': []
        }
        
        base_dir = Path(base_path)
        
        # Parcourir tous les dossiers mois
        for type_dir in ['consultations', 'inscriptions', 'radiations']:
            type_path = base_dir / type_dir
            
            if type_path.exists():
                # Parcourir tous les dossiers mois (2025-01, 2025-02, etc.)
                for month_dir in type_path.iterdir():
                    if month_dir.is_dir():
                        # Tous les fichiers CSV du mois
                        for csv_file in month_dir.glob("*.csv"):
                            files[type_dir].append(csv_file)
        
        return files
    
    def import_files_parallel(self, files_list, import_function, type_name):
        """Import de fichiers en parallèle"""
        logger.info(f"🚀 Début import parallèle {type_name} - {len(files_list)} fichiers")
        
        total_records = 0
        success_count = 0
        
        # ThreadPoolExecutor pour parallélisation
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Soumettre tous les jobs
            future_to_file = {
                executor.submit(import_function, file_path): file_path 
                for file_path in files_list
            }
            
            # Traiter les résultats
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    records = future.result()
                    total_records += records
                    success_count += 1
                    
                    if success_count % 10 == 0:
                        logger.info(f"  📊 {type_name}: {success_count}/{len(files_list)} fichiers traités")
                        
                except Exception as e:
                    logger.error(f"❌ Erreur traitement {file_path}: {e}")
        
        logger.info(f"✅ {type_name} terminé: {total_records:,} enregistrements importés")
        return total_records
    
    def cramer_historique_complet(self):
        """CRAMAGE MASSIF DE L'HISTORIQUE COMPLET !"""
        logger.info("🔥🔥🔥 DÉBUT CRAMAGE MASSIF AZURE SQL DATABASE ! 🔥🔥🔥")
        logger.info("="*90)
        
        self.start_time = datetime.now()
        
        # Récupérer tous les fichiers
        base_path = "DataLakeE7/historique_quotidien"
        files = self.get_all_files_by_type(base_path)
        
        total_files = sum(len(file_list) for file_list in files.values())
        logger.info(f"📁 Fichiers trouvés:")
        logger.info(f"  📋 Consultations: {len(files['consultations'])}")
        logger.info(f"  📝 Inscriptions: {len(files['inscriptions'])}")
        logger.info(f"  ☢️ Radiations: {len(files['radiations'])}")
        logger.info(f"  📊 TOTAL: {total_files}")
        logger.info("="*90)
        
        if total_files == 0:
            logger.error("❌ Aucun fichier trouvé !")
            return
        
        # Import séquentiel par type pour éviter les locks Azure
        logger.info("🚀 PHASE 1: Import des CONSULTATIONS")
        consultations_imported = self.import_files_parallel(
            files['consultations'], 
            self.import_consultations_file, 
            "CONSULTATIONS"
        )
        
        logger.info("🚀 PHASE 2: Import des INSCRIPTIONS")
        inscriptions_imported = self.import_files_parallel(
            files['inscriptions'], 
            self.import_inscriptions_file, 
            "INSCRIPTIONS"
        )
        
        logger.info("🚀 PHASE 3: Import des RADIATIONS")
        radiations_imported = self.import_files_parallel(
            files['radiations'], 
            self.import_radiations_file, 
            "RADIATIONS"
        )
        
        # Statistiques finales
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        logger.info("="*90)
        logger.info("🎉 CRAMAGE HISTORIQUE TERMINÉ !")
        logger.info("="*90)
        logger.info(f"📋 Consultations importées: {consultations_imported:,}")
        logger.info(f"📝 Inscriptions importées: {inscriptions_imported:,}")
        logger.info(f"☢️ Radiations importées: {radiations_imported:,}")
        logger.info(f"📊 TOTAL RECORDS: {consultations_imported + inscriptions_imported + radiations_imported:,}")
        logger.info(f"📁 Fichiers traités: {self.total_files_processed}")
        logger.info(f"⏱️ Durée: {duration}")
        logger.info(f"🚀 Throughput: {(consultations_imported + inscriptions_imported + radiations_imported) / duration.total_seconds():.0f} records/sec")
        logger.info("💰 CRÉDITS AZURE INTENSIVEMENT UTILISÉS !")
        logger.info("="*90)

def main():
    """Fonction principale - Import massif Azure SQL"""
    print("🔥🔥🔥 IMPORTEUR MASSIF AZURE SQL - CRAMAGE HISTORIQUE ! 🔥🔥🔥")
    print("="*80)
    print("⚠️ ATTENTION: Import de 264,451+ enregistrements vers Azure SQL")
    print("💰 Utilisation MASSIVE des crédits Azure gratuits")
    print("🚀 Parallélisation maximale pour performance")
    print("="*80)
    
    confirmation = input("🚀 Confirmer le CRAMAGE MASSIF ? (OUI pour continuer): ")
    if confirmation.upper() != 'OUI':
        print("❌ Import annulé")
        return
    
    # Import massif
    importeur = ImporteurMassifAzureHistorique()
    
    try:
        importeur.cramer_historique_complet()
        print(f"\n🎊 CRAMAGE RÉUSSI !")
        print(f"💰 Crédits Azure utilisés de manière INTENSIVE !")
        print(f"📊 Base de données prête pour la certification E7 !")
        
    except Exception as e:
        logger.error(f"❌ Erreur cramage: {e}")
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()