#!/usr/bin/env python3
"""
E7 CERTIFICATION - NETTOYEUR AZURE SQL DATABASE
===============================================
Description: Nettoyage complet des tables Azure avant import massif
             Suppression de toutes les anciennes données de test
Version: 1.0.0
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole
Date: 2025-10-30
License: MIT

NETTOYAGE COMPLET:
- Suppression de toutes les données existantes
- Vérification de l'état des tables
- Remise à zéro des compteurs IDENTITY
- Base propre pour import massif des 264,451 nouveaux enregistrements
"""

import pyodbc
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class NettoyeurAzureSQL:
    """Nettoyeur complet des tables Azure SQL Database"""
    
    def __init__(self):
        # Configuration Azure SQL Database
        self.server = 'sql-server-ficp-5647.database.windows.net'
        self.database = 'db-ficp-datawarehouse'
        self.username = 'ficpadmin'
        self.password = 'FicpDataWarehouse2025!'
        
        # Tables à nettoyer
        self.tables = [
            'ConsultationsFICP',
            'InscriptionsFICP', 
            'RadiationsFICP'
        ]
    
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
    
    def test_connexion(self):
        """Test de connexion Azure SQL"""
        try:
            logger.info("🔍 Test de connexion Azure SQL...")
            conn_str = self.get_connection_string()
            
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                
                logger.info("✅ Connexion Azure SQL réussie")
                logger.info(f"📊 Version: {version[:100]}...")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur connexion Azure SQL: {e}")
            return False
    
    def compter_enregistrements_avant(self):
        """Compte les enregistrements avant nettoyage"""
        try:
            logger.info("📊 Comptage des enregistrements existants...")
            conn_str = self.get_connection_string()
            
            stats_avant = {}
            
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                
                for table in self.tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        stats_avant[table] = count
                        logger.info(f"  📋 {table}: {count:,} enregistrements")
                    except Exception as e:
                        logger.warning(f"  ⚠️ Erreur comptage {table}: {e}")
                        stats_avant[table] = 0
            
            total_avant = sum(stats_avant.values())
            logger.info(f"📊 TOTAL AVANT NETTOYAGE: {total_avant:,} enregistrements")
            
            return stats_avant
            
        except Exception as e:
            logger.error(f"❌ Erreur comptage: {e}")
            return {}
    
    def nettoyer_table(self, table_name):
        """Nettoie une table spécifique"""
        try:
            logger.info(f"🧹 Nettoyage de la table {table_name}...")
            conn_str = self.get_connection_string()
            
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                
                # 1. Supprimer toutes les données
                cursor.execute(f"DELETE FROM {table_name}")
                rows_deleted = cursor.rowcount
                
                # 2. Remettre à zéro les compteurs IDENTITY
                cursor.execute(f"DBCC CHECKIDENT('{table_name}', RESEED, 0)")
                
                conn.commit()
                
                logger.info(f"  ✅ {table_name}: {rows_deleted:,} enregistrements supprimés")
                logger.info(f"  🔄 {table_name}: Compteur IDENTITY remis à zéro")
                
                return rows_deleted
                
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage {table_name}: {e}")
            return 0
    
    def verifier_apres_nettoyage(self):
        """Vérifie que les tables sont vides après nettoyage"""
        try:
            logger.info("🔍 Vérification après nettoyage...")
            conn_str = self.get_connection_string()
            
            with pyodbc.connect(conn_str) as conn:
                cursor = conn.cursor()
                
                for table in self.tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    
                    if count == 0:
                        logger.info(f"  ✅ {table}: VIDE (OK)")
                    else:
                        logger.error(f"  ❌ {table}: {count} enregistrements restants !")
                        return False
            
            logger.info("🎉 TOUTES LES TABLES SONT VIDES !")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification: {e}")
            return False
    
    def nettoyage_complet(self):
        """Nettoyage complet de toutes les tables"""
        logger.info("🧹🧹🧹 NETTOYAGE COMPLET AZURE SQL DATABASE 🧹🧹🧹")
        logger.info("="*80)
        logger.info("⚠️ SUPPRESSION DE TOUTES LES DONNÉES EXISTANTES")
        logger.info("🎯 Préparation pour import massif des 264,451 nouveaux enregistrements")
        logger.info("="*80)
        
        debut = datetime.now()
        
        # 1. Test de connexion
        if not self.test_connexion():
            logger.error("❌ Impossible de se connecter à Azure SQL")
            return False
        
        # 2. Comptage avant nettoyage
        stats_avant = self.compter_enregistrements_avant()
        
        if sum(stats_avant.values()) == 0:
            logger.info("✅ Tables déjà vides - Pas de nettoyage nécessaire")
            return True
        
        # 3. Confirmation
        print("\n" + "="*60)
        print("⚠️ ATTENTION: SUPPRESSION DÉFINITIVE DES DONNÉES !")
        print("="*60)
        for table, count in stats_avant.items():
            print(f"  🗑️ {table}: {count:,} enregistrements seront SUPPRIMÉS")
        print("="*60)
        
        confirmation = input("🚨 Confirmer la SUPPRESSION TOTALE ? (SUPPRIMER pour confirmer): ")
        if confirmation != "SUPPRIMER":
            logger.info("❌ Nettoyage annulé par l'utilisateur")
            return False
        
        # 4. Nettoyage table par table
        total_supprime = 0
        
        for table in self.tables:
            supprime = self.nettoyer_table(table)
            total_supprime += supprime
        
        # 5. Vérification finale
        if not self.verifier_apres_nettoyage():
            logger.error("❌ Erreur lors de la vérification finale")
            return False
        
        # 6. Statistiques finales
        fin = datetime.now()
        duree = fin - debut
        
        logger.info("="*80)
        logger.info("🎊 NETTOYAGE COMPLET TERMINÉ !")
        logger.info("="*80)
        logger.info(f"🗑️ Enregistrements supprimés: {total_supprime:,}")
        logger.info(f"📊 Tables nettoyées: {len(self.tables)}")
        logger.info(f"⏱️ Durée: {duree}")
        logger.info("✅ Base de données prête pour import massif des 264,451 nouveaux enregistrements")
        logger.info("="*80)
        
        return True

def main():
    """Fonction principale - Nettoyage Azure SQL"""
    print("🧹 NETTOYEUR AZURE SQL DATABASE - PRÉPARATION IMPORT MASSIF")
    print("="*70)
    print("⚠️ SUPPRESSION de toutes les données existantes")
    print("🎯 Préparation pour 264,451 nouveaux enregistrements cohérents")
    print("💰 Optimisation pour utilisation des crédits Azure gratuits")
    print("="*70)
    
    # Nettoyage
    nettoyeur = NettoyeurAzureSQL()
    
    try:
        succes = nettoyeur.nettoyage_complet()
        
        if succes:
            print(f"\n🎊 NETTOYAGE RÉUSSI !")
            print(f"✅ Base Azure SQL prête pour import massif !")
            print(f"🚀 Prochaine étape: Import des 264,451 enregistrements !")
        else:
            print(f"\n❌ ERREUR LORS DU NETTOYAGE !")
            print(f"🔧 Vérifier les logs et relancer si nécessaire")
            
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}")
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()