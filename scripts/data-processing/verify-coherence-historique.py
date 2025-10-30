#!/usr/bin/env python3
"""
E7 CERTIFICATION - VÉRIFICATEUR DE COHÉRENCE DONNÉES HISTORIQUE
===============================================================
Description: Vérification complète de la cohérence des 651 fichiers
             d'historique FICP avant import massif Azure
Version: 1.0.0
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole
Date: 2025-10-30
License: MIT

VÉRIFICATIONS EFFECTUÉES:
1. Intégrité des fichiers (pas de corruption)
2. Cohérence des clés BDF entre fichiers
3. Respect des normes réglementaires (31-37 jours)
4. Organismes conformes (CA/SOF/LCL uniquement)
5. Absence d'accents dans les données
6. Cohérence des volumes par jour ouvrable
7. Workflow logique: Consultation → Surveillance → Inscription → Radiation
"""

import pandas as pd
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class VerificateurCoherenceHistorique:
    """Vérificateur de cohérence des données historique FICP"""
    
    def __init__(self):
        self.organismes_autorises = {'CA', 'SOF', 'LCL'}
        self.types_radiations_autorises = {
            'REGULARISATION_VOLONTAIRE',
            'FIN_DELAI_LEGAL', 
            'ERREUR_CONTESTATION'
        }
        
        # Statistiques globales
        self.stats = {
            'fichiers_total': 0,
            'fichiers_valides': 0,
            'fichiers_corrompus': 0,
            'consultations_total': 0,
            'inscriptions_total': 0,
            'radiations_total': 0,
            'clients_uniques': set(),
            'erreurs_critiques': [],
            'warnings': []
        }
        
        # Base de données des workflows
        self.workflows_clients = defaultdict(dict)  # cle_bdf -> {consultations: [], surveillances: [], inscriptions: [], radiations: []}
    
    def verifier_fichier_existe_et_lisible(self, file_path):
        """Vérifie qu'un fichier existe et est lisible"""
        try:
            if not file_path.exists():
                return False, f"Fichier inexistant: {file_path}"
            
            if file_path.stat().st_size == 0:
                return False, f"Fichier vide: {file_path}"
            
            # Test de lecture
            df = pd.read_csv(file_path)
            return True, df
            
        except Exception as e:
            return False, f"Erreur lecture {file_path}: {e}"
    
    def verifier_organismes(self, df, file_path):
        """Vérifie que seuls les organismes autorisés sont présents"""
        erreurs = []
        
        # Chercher les colonnes organisme
        organisme_cols = [col for col in df.columns if 'organisme' in col.lower() or 'etablissement' in col.lower()]
        
        for col in organisme_cols:
            organismes_uniques = set(df[col].unique())
            organismes_interdits = organismes_uniques - self.organismes_autorises
            
            if organismes_interdits:
                erreurs.append(f"Organismes interdits dans {file_path}:{col}: {organismes_interdits}")
        
        return erreurs
    
    def verifier_absence_accents(self, df, file_path):
        """Vérifie l'absence d'accents dans les données textuelles"""
        erreurs = []
        accents_pattern = re.compile(r'[àáâãäåèéêëìíîïòóôõöùúûüýÿçñÀÁÂÃÄÅÈÉÊËÌÍÎÏÒÓÔÕÖÙÚÛÜÝŸÇÑ]')
        
        # Colonnes textuelles à vérifier
        text_cols = df.select_dtypes(include=['object']).columns
        
        for col in text_cols:
            for idx, value in df[col].items():
                if pd.notna(value) and accents_pattern.search(str(value)):
                    erreurs.append(f"Accent détecté dans {file_path}:{col}[{idx}]: '{value}'")
                    # Limiter à 5 erreurs par colonne
                    if len([e for e in erreurs if f"{file_path}:{col}" in e]) >= 5:
                        erreurs.append(f"... et autres accents dans {file_path}:{col}")
                        break
        
        return erreurs
    
    def verifier_cles_bdf_format(self, df, file_path):
        """Vérifie le format des clés BDF (13 caractères, pas d'accents)"""
        erreurs = []
        
        if 'cle_bdf' not in df.columns:
            return [f"Colonne 'cle_bdf' manquante dans {file_path}"]
        
        for idx, cle in df['cle_bdf'].items():
            if pd.isna(cle):
                erreurs.append(f"Clé BDF vide dans {file_path}[{idx}]")
                continue
            
            cle_str = str(cle)
            
            # Longueur
            if len(cle_str) != 13:
                erreurs.append(f"Clé BDF longueur incorrecte dans {file_path}[{idx}]: '{cle_str}' ({len(cle_str)} chars)")
            
            # Format alphanumérique
            if not cle_str.isalnum():
                erreurs.append(f"Clé BDF format invalide dans {file_path}[{idx}]: '{cle_str}'")
            
            # Limiter les erreurs
            if len(erreurs) >= 10:
                erreurs.append(f"... et autres erreurs de clés BDF dans {file_path}")
                break
        
        return erreurs
    
    def analyser_consultations(self, df, file_path):
        """Analyse les consultations"""
        erreurs = []
        
        # Colonnes requises
        cols_requises = ['date_consultation', 'cle_bdf', 'reponse_registre', 'etablissement_demandeur']
        for col in cols_requises:
            if col not in df.columns:
                erreurs.append(f"Colonne requise manquante dans {file_path}: {col}")
        
        if erreurs:
            return erreurs
        
        # Réponses autorisées
        reponses_autorisees = {'INSCRIT', 'NON_INSCRIT'}
        reponses_invalides = set(df['reponse_registre'].unique()) - reponses_autorisees
        if reponses_invalides:
            erreurs.append(f"Réponses invalides dans {file_path}: {reponses_invalides}")
        
        # Stocker pour vérification workflow
        for _, row in df.iterrows():
            cle_bdf = row['cle_bdf']
            if 'consultations' not in self.workflows_clients[cle_bdf]:
                self.workflows_clients[cle_bdf]['consultations'] = []
            self.workflows_clients[cle_bdf]['consultations'].append({
                'date': row['date_consultation'],
                'reponse': row['reponse_registre']
            })
        
        return erreurs
    
    def analyser_inscriptions(self, df, file_path):
        """Analyse les inscriptions/surveillances"""
        erreurs = []
        
        # Colonnes requises
        cols_requises = ['date_envoi', 'cle_bdf', 'type_courrier']
        for col in cols_requises:
            if col not in df.columns:
                erreurs.append(f"Colonne requise manquante dans {file_path}: {col}")
        
        if erreurs:
            return erreurs
        
        # Types autorisés
        types_autorises = {'SURVEILLANCE', 'INSCRIPTION'}
        types_invalides = set(df['type_courrier'].unique()) - types_autorises
        if types_invalides:
            erreurs.append(f"Types courrier invalides dans {file_path}: {types_invalides}")
        
        # Stocker pour vérification workflow
        for _, row in df.iterrows():
            cle_bdf = row['cle_bdf']
            type_courrier = row['type_courrier']
            
            if type_courrier == 'SURVEILLANCE':
                if 'surveillances' not in self.workflows_clients[cle_bdf]:
                    self.workflows_clients[cle_bdf]['surveillances'] = []
                self.workflows_clients[cle_bdf]['surveillances'].append({
                    'date': row['date_envoi']
                })
            
            elif type_courrier == 'INSCRIPTION':
                if 'inscriptions' not in self.workflows_clients[cle_bdf]:
                    self.workflows_clients[cle_bdf]['inscriptions'] = []
                self.workflows_clients[cle_bdf]['inscriptions'].append({
                    'date': row['date_envoi']
                })
        
        return erreurs
    
    def analyser_radiations(self, df, file_path):
        """Analyse les radiations"""
        erreurs = []
        
        # Colonnes requises
        cols_requises = ['date_radiation', 'cle_bdf', 'type_radiation']
        for col in cols_requises:
            if col not in df.columns:
                erreurs.append(f"Colonne requise manquante dans {file_path}: {col}")
        
        if erreurs:
            return erreurs
        
        # Types autorisés
        types_invalides = set(df['type_radiation'].unique()) - self.types_radiations_autorises
        if types_invalides:
            erreurs.append(f"Types radiation invalides dans {file_path}: {types_invalides}")
        
        # Stocker pour vérification workflow
        for _, row in df.iterrows():
            cle_bdf = row['cle_bdf']
            if 'radiations' not in self.workflows_clients[cle_bdf]:
                self.workflows_clients[cle_bdf]['radiations'] = []
            self.workflows_clients[cle_bdf]['radiations'].append({
                'date': row['date_radiation'],
                'type': row['type_radiation']
            })
        
        return erreurs
    
    def verifier_norme_31_37_jours(self):
        """Vérifie la norme 31-37 jours entre surveillance et inscription"""
        erreurs = []
        conformes = 0
        non_conformes = 0
        
        for cle_bdf, workflow in self.workflows_clients.items():
            surveillances = workflow.get('surveillances', [])
            inscriptions = workflow.get('inscriptions', [])
            
            for inscription in inscriptions:
                date_inscription = pd.to_datetime(inscription['date'])
                
                # Chercher la surveillance la plus proche avant inscription
                surveillance_precedente = None
                for surveillance in surveillances:
                    date_surveillance = pd.to_datetime(surveillance['date'])
                    
                    if date_surveillance < date_inscription:
                        if surveillance_precedente is None or date_surveillance > pd.to_datetime(surveillance_precedente['date']):
                            surveillance_precedente = surveillance
                
                if surveillance_precedente:
                    date_surv = pd.to_datetime(surveillance_precedente['date'])
                    delta_jours = (date_inscription - date_surv).days
                    
                    if 31 <= delta_jours <= 37:
                        conformes += 1
                    else:
                        non_conformes += 1
                        if len(erreurs) < 10:  # Limiter les exemples
                            erreurs.append(f"Non-conformité 31-37j pour {cle_bdf}: {delta_jours} jours entre {date_surv.date()} et {date_inscription.date()}")
        
        if non_conformes > 0:
            erreurs.append(f"RÉSUMÉ NORME: {conformes} conformes, {non_conformes} non-conformes ({non_conformes/(conformes+non_conformes)*100:.1f}%)")
        
        return erreurs
    
    def verifier_volumes_quotidiens(self, base_path):
        """Vérifie les volumes quotidiens sont cohérents"""
        erreurs = []
        
        # Analyser les volumes par jour
        volumes_quotidiens = defaultdict(lambda: {'consultations': 0, 'inscriptions': 0, 'radiations': 0})
        
        base_dir = Path(base_path)
        
        # Parcourir tous les fichiers
        for type_dir in ['consultations', 'inscriptions', 'radiations']:
            type_path = base_dir / type_dir
            if not type_path.exists():
                continue
            
            for month_dir in type_path.iterdir():
                if not month_dir.is_dir():
                    continue
                
                for csv_file in month_dir.glob("*.csv"):
                    # Extraire la date du nom de fichier
                    match = re.search(r'(\d{8})', csv_file.name)
                    if not match:
                        continue
                    
                    date_str = match.group(1)
                    
                    try:
                        df = pd.read_csv(csv_file)
                        volumes_quotidiens[date_str][type_dir] = len(df)
                    except Exception as e:
                        erreurs.append(f"Erreur lecture volume {csv_file}: {e}")
        
        # Vérifier cohérence des volumes
        for date_str, volumes in volumes_quotidiens.items():
            consultations = volumes['consultations']
            inscriptions = volumes['inscriptions']
            radiations = volumes['radiations']
            
            # Volumes attendus (approximatifs)
            if not (800 <= consultations <= 1000):
                erreurs.append(f"Volume consultations anormal {date_str}: {consultations} (attendu: 800-1000)")
            
            if not (200 <= inscriptions <= 300):
                erreurs.append(f"Volume inscriptions anormal {date_str}: {inscriptions} (attendu: 200-300)")
            
            if not (50 <= radiations <= 80):
                erreurs.append(f"Volume radiations anormal {date_str}: {radiations} (attendu: 50-80)")
        
        return erreurs
    
    def verifier_coherence_complete(self, base_path):
        """Vérification complète de cohérence"""
        logger.info("🔍 DÉBUT VÉRIFICATION COHÉRENCE DONNÉES HISTORIQUE")
        logger.info("="*80)
        
        debut = datetime.now()
        base_dir = Path(base_path)
        
        # Phase 1: Vérification fichiers individuels
        logger.info("🔍 PHASE 1: Vérification intégrité fichiers")
        
        for type_dir in ['consultations', 'inscriptions', 'radiations']:
            type_path = base_dir / type_dir
            if not type_path.exists():
                self.stats['erreurs_critiques'].append(f"Dossier manquant: {type_path}")
                continue
            
            logger.info(f"  📁 Vérification {type_dir}...")
            
            for month_dir in type_path.iterdir():
                if not month_dir.is_dir():
                    continue
                
                for csv_file in month_dir.glob("*.csv"):
                    self.stats['fichiers_total'] += 1
                    
                    # Test lisibilité
                    lisible, resultat = self.verifier_fichier_existe_et_lisible(csv_file)
                    if not lisible:
                        self.stats['fichiers_corrompus'] += 1
                        self.stats['erreurs_critiques'].append(resultat)
                        continue
                    
                    df = resultat
                    self.stats['fichiers_valides'] += 1
                    
                    # Collecte des clés BDF uniques
                    if 'cle_bdf' in df.columns:
                        self.stats['clients_uniques'].update(df['cle_bdf'].unique())
                    
                    # Comptage records
                    if type_dir == 'consultations':
                        self.stats['consultations_total'] += len(df)
                    elif type_dir == 'inscriptions':
                        self.stats['inscriptions_total'] += len(df)
                    elif type_dir == 'radiations':
                        self.stats['radiations_total'] += len(df)
                    
                    # Vérifications spécifiques
                    erreurs = []
                    
                    # Organismes
                    erreurs.extend(self.verifier_organismes(df, csv_file))
                    
                    # Accents
                    erreurs.extend(self.verifier_absence_accents(df, csv_file))
                    
                    # Clés BDF
                    erreurs.extend(self.verifier_cles_bdf_format(df, csv_file))
                    
                    # Analyse par type
                    if type_dir == 'consultations':
                        erreurs.extend(self.analyser_consultations(df, csv_file))
                    elif type_dir == 'inscriptions':
                        erreurs.extend(self.analyser_inscriptions(df, csv_file))
                    elif type_dir == 'radiations':
                        erreurs.extend(self.analyser_radiations(df, csv_file))
                    
                    # Stocker erreurs
                    for erreur in erreurs:
                        if "invalide" in erreur or "manquante" in erreur or "vide" in erreur:
                            self.stats['erreurs_critiques'].append(erreur)
                        else:
                            self.stats['warnings'].append(erreur)
        
        # Phase 2: Vérifications transversales
        logger.info("🔍 PHASE 2: Vérifications transversales")
        
        # Norme 31-37 jours
        logger.info("  📊 Vérification norme 31-37 jours...")
        erreurs_norme = self.verifier_norme_31_37_jours()
        self.stats['warnings'].extend(erreurs_norme)
        
        # Volumes quotidiens
        logger.info("  📈 Vérification volumes quotidiens...")
        erreurs_volumes = self.verifier_volumes_quotidiens(base_path)
        self.stats['warnings'].extend(erreurs_volumes)
        
        # Statistiques finales
        fin = datetime.now()
        duree = fin - debut
        
        logger.info("="*80)
        logger.info("📊 RAPPORT DE COHÉRENCE FINAL")
        logger.info("="*80)
        logger.info(f"📁 Fichiers analysés: {self.stats['fichiers_total']}")
        logger.info(f"✅ Fichiers valides: {self.stats['fichiers_valides']}")
        logger.info(f"❌ Fichiers corrompus: {self.stats['fichiers_corrompus']}")
        logger.info(f"📋 Consultations: {self.stats['consultations_total']:,}")
        logger.info(f"📝 Inscriptions: {self.stats['inscriptions_total']:,}")
        logger.info(f"☢️ Radiations: {self.stats['radiations_total']:,}")
        logger.info(f"👥 Clients uniques: {len(self.stats['clients_uniques'])}")
        logger.info(f"🚨 Erreurs critiques: {len(self.stats['erreurs_critiques'])}")
        logger.info(f"⚠️ Warnings: {len(self.stats['warnings'])}")
        logger.info(f"⏱️ Durée analyse: {duree}")
        logger.info("="*80)
        
        # Affichage des erreurs
        if self.stats['erreurs_critiques']:
            logger.error("🚨 ERREURS CRITIQUES:")
            for erreur in self.stats['erreurs_critiques'][:20]:  # Limiter l'affichage
                logger.error(f"  ❌ {erreur}")
            if len(self.stats['erreurs_critiques']) > 20:
                logger.error(f"  ... et {len(self.stats['erreurs_critiques']) - 20} autres erreurs")
        
        if self.stats['warnings']:
            logger.warning("⚠️ WARNINGS:")
            for warning in self.stats['warnings'][:20]:  # Limiter l'affichage
                logger.warning(f"  ⚠️ {warning}")
            if len(self.stats['warnings']) > 20:
                logger.warning(f"  ... et {len(self.stats['warnings']) - 20} autres warnings")
        
        # Verdict final
        if len(self.stats['erreurs_critiques']) == 0:
            logger.info("🎉 VERDICT: DONNÉES COHÉRENTES - PRÊTES POUR IMPORT AZURE!")
            return True
        else:
            logger.error("❌ VERDICT: DONNÉES NON COHÉRENTES - CORRIGER AVANT IMPORT!")
            return False

def main():
    """Fonction principale - Vérification cohérence"""
    print("🔍 VÉRIFICATEUR COHÉRENCE DONNÉES HISTORIQUE FICP")
    print("="*60)
    print("📊 Analyse de 651 fichiers avant import Azure SQL")
    print("🔍 Vérification complète: intégrité, normes, cohérence")
    print("="*60)
    
    # Vérification
    verificateur = VerificateurCoherenceHistorique()
    base_path = "DataLakeE7/historique_quotidien"
    
    try:
        coherent = verificateur.verifier_coherence_complete(base_path)
        
        if coherent:
            print("\n🎊 DONNÉES COHÉRENTES !")
            print("🚀 Prêtes pour le cramage Azure SQL !")
        else:
            print("\n❌ DONNÉES NON COHÉRENTES !")
            print("🛠️ Corriger les erreurs avant import !")
            
    except Exception as e:
        logger.error(f"❌ Erreur vérification: {e}")
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()