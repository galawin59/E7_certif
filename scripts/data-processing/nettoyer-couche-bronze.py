#!/usr/bin/env python3
"""
E7 CERTIFICATION - NETTOYEUR COUCHE BRONZE
==========================================
Description: Nettoyage intelligent de la couche Bronze
             - GARDE l'architecture Medallion
             - SUPPRIME les anciennes données incohérentes
             - PRÉPARE pour les nouvelles données propres
Version: 1.0.0
Author: E7 Data Engineering Team
Date: 2025-10-30

STRATÉGIE NETTOYAGE:
- Conservation de la structure des dossiers
- Suppression de tous les CSV existants (données de mauvaise qualité)
- Préparation pour import des 651 nouveaux fichiers cohérents
"""

import os
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class NettoyeurCoucheBronze:
    """Nettoyeur intelligent de la couche Bronze"""
    
    def __init__(self):
        self.base_path = Path("DataLakeE7/historique_quotidien")
        self.types_donnees = ['consultations', 'inscriptions', 'radiations']
        self.mois = ['2025-01', '2025-02', '2025-03', '2025-04', '2025-05', 
                    '2025-06', '2025-07', '2025-08', '2025-09', '2025-10']
    
    def analyser_etat_actuel(self):
        """Analyse l'état actuel de la couche Bronze"""
        logger.info("🔍 Analyse de l'état actuel de la couche Bronze...")
        
        stats = {}
        total_fichiers = 0
        total_taille = 0
        
        for type_donnee in self.types_donnees:
            chemin_type = self.base_path / type_donnee
            
            if chemin_type.exists():
                fichiers_csv = list(chemin_type.rglob("*.csv"))
                taille_type = sum(f.stat().st_size for f in fichiers_csv)
                
                stats[type_donnee] = {
                    'fichiers': len(fichiers_csv),
                    'taille_mb': round(taille_type / (1024*1024), 2)
                }
                
                total_fichiers += len(fichiers_csv)
                total_taille += taille_type
                
                logger.info(f"  📊 {type_donnee}: {len(fichiers_csv)} fichiers ({stats[type_donnee]['taille_mb']} MB)")
            else:
                stats[type_donnee] = {'fichiers': 0, 'taille_mb': 0}
                logger.warning(f"  ⚠️ Dossier {type_donnee} introuvable")
        
        logger.info(f"📊 TOTAL: {total_fichiers} fichiers ({round(total_taille/(1024*1024), 2)} MB)")
        return stats, total_fichiers, total_taille
    
    def verifier_structure_dossiers(self):
        """Vérifie que la structure des dossiers est correcte"""
        logger.info("🏗️ Vérification de la structure des dossiers...")
        
        structure_ok = True
        
        # Vérifier dossier racine
        if not self.base_path.exists():
            logger.error(f"❌ Dossier racine manquant: {self.base_path}")
            return False
        
        # Vérifier dossiers par type
        for type_donnee in self.types_donnees:
            chemin_type = self.base_path / type_donnee
            
            if not chemin_type.exists():
                logger.warning(f"⚠️ Création du dossier: {chemin_type}")
                chemin_type.mkdir(parents=True, exist_ok=True)
            
            # Vérifier dossiers par mois
            for mois in self.mois:
                chemin_mois = chemin_type / mois
                
                if not chemin_mois.exists():
                    logger.info(f"📁 Création du dossier: {chemin_mois}")
                    chemin_mois.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ Structure des dossiers vérifiée/créée")
        return True
    
    def supprimer_anciens_csv(self):
        """Supprime tous les anciens fichiers CSV"""
        logger.info("🗑️ Suppression des anciens fichiers CSV...")
        
        fichiers_supprimes = 0
        taille_liberee = 0
        
        for type_donnee in self.types_donnees:
            chemin_type = self.base_path / type_donnee
            
            if chemin_type.exists():
                fichiers_csv = list(chemin_type.rglob("*.csv"))
                
                for fichier in fichiers_csv:
                    try:
                        taille_fichier = fichier.stat().st_size
                        fichier.unlink()
                        
                        fichiers_supprimes += 1
                        taille_liberee += taille_fichier
                        
                        if fichiers_supprimes % 50 == 0:
                            logger.info(f"  🗑️ {fichiers_supprimes} fichiers supprimés...")
                            
                    except Exception as e:
                        logger.error(f"❌ Erreur suppression {fichier}: {e}")
        
        logger.info(f"✅ {fichiers_supprimes} fichiers CSV supprimés")
        logger.info(f"💾 {round(taille_liberee/(1024*1024), 2)} MB libérés")
        
        return fichiers_supprimes, taille_liberee
    
    def verifier_nettoyage(self):
        """Vérifie que le nettoyage s'est bien passé"""
        logger.info("🔍 Vérification après nettoyage...")
        
        for type_donnee in self.types_donnees:
            chemin_type = self.base_path / type_donnee
            fichiers_restants = list(chemin_type.rglob("*.csv"))
            
            if len(fichiers_restants) == 0:
                logger.info(f"  ✅ {type_donnee}: Aucun fichier CSV restant")
            else:
                logger.error(f"  ❌ {type_donnee}: {len(fichiers_restants)} fichiers restants!")
                return False
        
        # Vérifier que les dossiers existent toujours
        dossiers_manquants = 0
        for type_donnee in self.types_donnees:
            for mois in self.mois:
                chemin_mois = self.base_path / type_donnee / mois
                if not chemin_mois.exists():
                    logger.error(f"❌ Dossier manquant: {chemin_mois}")
                    dossiers_manquants += 1
        
        if dossiers_manquants == 0:
            logger.info("✅ Structure des dossiers préservée")
            return True
        else:
            logger.error(f"❌ {dossiers_manquants} dossiers manquants")
            return False
    
    def nettoyage_complet(self):
        """Nettoyage complet de la couche Bronze"""
        logger.info("🧹🧹🧹 NETTOYAGE COUCHE BRONZE 🧹🧹🧹")
        logger.info("="*80)
        logger.info("🎯 STRATÉGIE: Conservation architecture + Suppression données")
        logger.info("🗑️ Suppression des anciens CSV de mauvaise qualité")
        logger.info("📁 Conservation de la structure Medallion Bronze")
        logger.info("="*80)
        
        debut = datetime.now()
        
        # 1. Analyse état actuel
        stats_avant, total_fichiers, total_taille = self.analyser_etat_actuel()
        
        if total_fichiers == 0:
            logger.info("✅ Couche Bronze déjà vide - Pas de nettoyage nécessaire")
            return True
        
        # 2. Confirmation
        print("\n" + "="*60)
        print("🗑️ SUPPRESSION DES DONNÉES DE MAUVAISE QUALITÉ")
        print("="*60)
        for type_donnee, stats in stats_avant.items():
            if stats['fichiers'] > 0:
                print(f"  📊 {type_donnee}: {stats['fichiers']} fichiers ({stats['taille_mb']} MB)")
        print(f"  🎯 TOTAL: {total_fichiers} fichiers ({round(total_taille/(1024*1024), 2)} MB)")
        print("="*60)
        print("✅ CONSERVATION: Structure des dossiers Medallion")
        print("🚀 PRÉPARATION: Pour 651 nouveaux fichiers cohérents")
        print("="*60)
        
        confirmation = input("🚨 Confirmer le NETTOYAGE ? (OUI pour confirmer): ")
        if confirmation.upper() != "OUI":
            logger.info("❌ Nettoyage annulé par l'utilisateur")
            return False
        
        # 3. Vérification structure
        if not self.verifier_structure_dossiers():
            logger.error("❌ Erreur structure des dossiers")
            return False
        
        # 4. Suppression des anciens CSV
        fichiers_supprimes, taille_liberee = self.supprimer_anciens_csv()
        
        # 5. Vérification finale
        if not self.verifier_nettoyage():
            logger.error("❌ Erreur lors de la vérification finale")
            return False
        
        # 6. Statistiques finales
        fin = datetime.now()
        duree = fin - debut
        
        logger.info("="*80)
        logger.info("🎊 NETTOYAGE COUCHE BRONZE TERMINÉ !")
        logger.info("="*80)
        logger.info(f"🗑️ Fichiers supprimés: {fichiers_supprimes}")
        logger.info(f"💾 Espace libéré: {round(taille_liberee/(1024*1024), 2)} MB")
        logger.info(f"📁 Structure préservée: {len(self.types_donnees)} types × {len(self.mois)} mois")
        logger.info(f"⏱️ Durée: {duree}")
        logger.info("✅ Couche Bronze prête pour les nouvelles données cohérentes")
        logger.info("🚀 Prochaine étape: Génération + Import des 651 nouveaux fichiers")
        logger.info("="*80)
        
        return True

def main():
    """Fonction principale - Nettoyage couche Bronze"""
    print("🧹 NETTOYEUR COUCHE BRONZE - PRÉPARATION DONNÉES PROPRES")
    print("="*70)
    print("🎯 OBJECTIF: Nettoyer les anciennes données incohérentes")
    print("📁 CONSERVATION: Architecture Medallion Bronze intacte")
    print("🚀 PRÉPARATION: Pour import des données réglementaires")
    print("="*70)
    
    # Nettoyage
    nettoyeur = NettoyeurCoucheBronze()
    
    try:
        succes = nettoyeur.nettoyage_complet()
        
        if succes:
            print(f"\n🎊 NETTOYAGE RÉUSSI !")
            print(f"✅ Couche Bronze nettoyée et prête !")
            print(f"📁 Architecture Medallion préservée !")
            print(f"🚀 Prêt pour les 651 nouveaux fichiers cohérents !")
        else:
            print(f"\n❌ ERREUR LORS DU NETTOYAGE !")
            print(f"🔧 Vérifier les logs et relancer si nécessaire")
            
    except Exception as e:
        logger.error(f"❌ Erreur critique: {e}")
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()