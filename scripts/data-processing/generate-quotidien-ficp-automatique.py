#!/usr/bin/env python3
"""
E7 CERTIFICATION - GÉNÉRATEUR QUOTIDIEN FICP AUTOMATIQUE
=========================================================
Description: Génération quotidienne automatique avec respect strict
             du taux de conformité réglementaire ≤ 9.6%
Version: 1.0.0
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole
Date: 2025-10-30
License: MIT

CONTRAINTES RÉGLEMENTAIRES STRICTES:
- Taux non-conformité ≤ 9.6% (seuil maximum acceptable)
- Respect délais 31-37 jours pour 90.4% minimum des inscriptions
- Surveillance obligatoire AVANT inscription avec délai conforme
- Simulation production réaliste avec sécurité juridique
"""

import pandas as pd
import random
from datetime import datetime, timedelta, date
from pathlib import Path
import logging
import json
from collections import defaultdict

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class GenerateurQuotidienFICPAutomatique:
    """Générateur quotidien FICP avec conformité réglementaire stricte"""
    
    def __init__(self):
        # Paramètres production réalistes
        self.consultations_par_jour = (800, 1000)
        self.inscriptions_par_jour = (200, 300)
        self.radiations_par_jour = (50, 80)
        
        # CONTRAINTE RÉGLEMENTAIRE CRITIQUE
        self.taux_non_conformite_max = 0.096  # 9.6% maximum !
        
        # Organismes autorisés uniquement
        self.organismes = ['CA', 'SOF', 'LCL']
        
        # Base clients pour cohérence
        self.clients_database = {}  # cle_bdf -> infos
        self.clients_surveillances = defaultdict(list)  # cle_bdf -> [dates]
        self.clients_inscriptions = defaultdict(list)   # cle_bdf -> [dates]
        
        # Noms/prénoms sans accents
        self.noms = [
            'MARTIN', 'BERNARD', 'THOMAS', 'PETIT', 'ROBERT', 'RICHARD', 'DURAND', 
            'DUBOIS', 'MOREAU', 'LAURENT', 'SIMON', 'MICHEL', 'LEFEBVRE', 'LEROY',
            'ROUX', 'DAVID', 'BERTRAND', 'MOREL', 'FOURNIER', 'GIRARD', 'BONNET',
            'DUPONT', 'LAMBERT', 'FONTAINE', 'ROUSSEAU', 'VINCENT', 'MULLER', 'LEFEVRE'
        ]
        
        self.prenoms = [
            'JEAN', 'MARIE', 'PIERRE', 'MICHEL', 'ALAIN', 'PHILIPPE', 'DANIEL',
            'BERNARD', 'CHRISTOPHE', 'PATRICK', 'NICOLAS', 'CLAUDE', 'FRANCOIS',
            'STEPHANE', 'LAURENT', 'THIERRY', 'DAVID', 'PASCAL', 'ERIC', 'JEROME',
            'FREDERIC', 'SEBASTIEN', 'DIDIER', 'BRUNO', 'CHRISTIAN', 'OLIVIER'
        ]
        
        # Types radiations avec probabilités
        self.types_radiations = {
            'REGULARISATION_VOLONTAIRE': 0.70,
            'FIN_DELAI_LEGAL': 0.25,
            'ERREUR_CONTESTATION': 0.05
        }
    
    def generer_cle_bdf(self, nom, prenom, date_naissance):
        """Génère une clé BDF réaliste (13 caractères, sans accents)"""
        def nettoyer(texte):
            replacements = {
                'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A', 'Å': 'A',
                'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
                'Ì': 'I', 'Í': 'I', 'Î': 'I', 'Ï': 'I',
                'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
                'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
                'Ý': 'Y', 'Ÿ': 'Y', 'Ç': 'C', 'Ñ': 'N'
            }
            result = texte.upper()
            for old, new in replacements.items():
                result = result.replace(old, new)
            return ''.join(c for c in result if c.isalnum())
        
        nom_clean = nettoyer(nom)[:6].ljust(6, 'X')
        prenom_clean = nettoyer(prenom)[:4].ljust(4, 'X')
        
        # Date de naissance AAMMJJ
        try:
            if isinstance(date_naissance, str):
                if len(date_naissance) == 8:
                    year, month, day = date_naissance[:4], date_naissance[4:6], date_naissance[6:8]
                else:
                    year, month, day = date_naissance.split('-')
            else:
                year, month, day = str(date_naissance.year), f"{date_naissance.month:02d}", f"{date_naissance.day:02d}"
            date_part = year[2:] + month + day
        except:
            date_part = "251030"
        
        # Clé de 13 caractères exactement
        cle_base = nom_clean + prenom_clean + date_part
        if len(cle_base) > 13:
            cle_base = cle_base[:13]
        elif len(cle_base) < 13:
            cle_base = cle_base.ljust(13, 'X')
        
        return cle_base
    
    def generer_client_fictif(self, date_reference):
        """Génère un client fictif"""
        nom = random.choice(self.noms)
        prenom = random.choice(self.prenoms)
        
        # Date naissance (18-80 ans)
        age_jours = random.randint(18*365, 80*365)
        date_naissance = date_reference - timedelta(days=age_jours)
        
        cle_bdf = self.generer_cle_bdf(nom, prenom, date_naissance)
        
        # Stocker
        self.clients_database[cle_bdf] = {
            'nom': nom,
            'prenom': prenom,
            'date_naissance': date_naissance,
            'organisme_principal': random.choice(self.organismes)
        }
        
        return cle_bdf
    
    def generer_consultations_jour(self, date_jour):
        """Génère consultations du jour"""
        nb_consultations = random.randint(*self.consultations_par_jour)
        consultations = []
        
        for i in range(nb_consultations):
            # Client (nouveau ou existant)
            if random.random() < 0.95 or not self.clients_database:
                cle_bdf = self.generer_client_fictif(date_jour)
            else:
                cle_bdf = random.choice(list(self.clients_database.keys()))
            
            # Réponse (15% inscrits)
            reponse = 'INSCRIT' if random.random() < 0.15 else 'NON_INSCRIT'
            
            # Organisme
            if cle_bdf in self.clients_database and random.random() < 0.70:
                organisme = self.clients_database[cle_bdf]['organisme_principal']
            else:
                organisme = random.choice(self.organismes)
            
            # Heure (8h-18h)
            heure = f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}"
            
            consultations.append({
                'id_consultation': f"FICP_{date_jour.strftime('%Y%m%d')}_{i+1:04d}",
                'date_consultation': date_jour.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'reponse_registre': reponse,
                'etablissement_demandeur': organisme,
                'heure_consultation': heure
            })
        
        return consultations
    
    def generer_inscriptions_jour_conforme(self, date_jour):
        """
        GÉNÉRATION AVEC CONFORMITÉ RÉGLEMENTAIRE STRICTE ≤ 9.6%
        """
        nb_inscriptions = random.randint(*self.inscriptions_par_jour)
        inscriptions = []
        
        nb_surveillances = int(nb_inscriptions * 0.80)  # 80% surveillances
        nb_inscriptions_reelles = nb_inscriptions - nb_surveillances
        
        # === SURVEILLANCES (toujours conformes) ===
        for i in range(nb_surveillances):
            if self.clients_database and random.random() < 0.60:
                cle_bdf = random.choice(list(self.clients_database.keys()))
            else:
                cle_bdf = self.generer_client_fictif(date_jour)
            
            # Stocker surveillance
            self.clients_surveillances[cle_bdf].append(date_jour)
            
            inscriptions.append({
                'date_envoi': date_jour.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'type_courrier': 'SURVEILLANCE'
            })
        
        # === INSCRIPTIONS AVEC CONTRÔLE STRICT ===
        nb_non_conformes_autorisees = int(nb_inscriptions_reelles * self.taux_non_conformite_max)
        nb_conformes_obligatoires = nb_inscriptions_reelles - nb_non_conformes_autorisees
        
        logger.info(f"  📊 Inscriptions {date_jour}: {nb_conformes_obligatoires} conformes + {nb_non_conformes_autorisees} non-conformes (max {self.taux_non_conformite_max*100:.1f}%)")
        
        # INSCRIPTIONS CONFORMES (90.4% minimum)
        for i in range(nb_conformes_obligatoires):
            # Chercher client avec surveillance antérieure
            clients_avec_surveillance = [
                cle for cle, dates in self.clients_surveillances.items()
                if any((date_jour - d).days >= 31 for d in dates)
            ]
            
            if clients_avec_surveillance and random.random() < 0.80:
                cle_bdf = random.choice(clients_avec_surveillance)
                
                # Trouver surveillance conforme (31-37 jours avant)
                surveillances_valides = [
                    d for d in self.clients_surveillances[cle_bdf]
                    if 31 <= (date_jour - d).days <= 37
                ]
                
                if not surveillances_valides:
                    # Créer surveillance conforme
                    delai_conforme = random.randint(31, 37)
                    date_surveillance = date_jour - timedelta(days=delai_conforme)
                    # Éviter weekends
                    while date_surveillance.weekday() >= 5:
                        date_surveillance -= timedelta(days=1)
                    self.clients_surveillances[cle_bdf].append(date_surveillance)
            else:
                # Nouveau client avec surveillance conforme automatique
                cle_bdf = self.generer_client_fictif(date_jour)
                delai_conforme = random.randint(31, 37)
                date_surveillance = date_jour - timedelta(days=delai_conforme)
                while date_surveillance.weekday() >= 5:
                    date_surveillance -= timedelta(days=1)
                self.clients_surveillances[cle_bdf].append(date_surveillance)
            
            # Stocker inscription
            self.clients_inscriptions[cle_bdf].append(date_jour)
            
            inscriptions.append({
                'date_envoi': date_jour.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'type_courrier': 'INSCRIPTION'
            })
        
        # INSCRIPTIONS NON-CONFORMES (≤ 9.6% seulement)
        for i in range(nb_non_conformes_autorisees):
            if self.clients_database and random.random() < 0.70:
                cle_bdf = random.choice(list(self.clients_database.keys()))
            else:
                cle_bdf = self.generer_client_fictif(date_jour)
            
            # Surveillance non-conforme (délais incorrects volontairement)
            if random.random() < 0.5:
                # Trop tôt (< 31 jours)
                delai_incorrect = random.randint(1, 30)
            else:
                # Trop tard (> 37 jours)
                delai_incorrect = random.randint(38, 60)
            
            date_surveillance = date_jour - timedelta(days=delai_incorrect)
            while date_surveillance.weekday() >= 5:
                date_surveillance -= timedelta(days=1)
            
            self.clients_surveillances[cle_bdf].append(date_surveillance)
            self.clients_inscriptions[cle_bdf].append(date_jour)
            
            inscriptions.append({
                'date_envoi': date_jour.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'type_courrier': 'INSCRIPTION'
            })
        
        return inscriptions
    
    def generer_radiations_jour(self, date_jour):
        """Génère radiations du jour"""
        nb_radiations = random.randint(*self.radiations_par_jour)
        radiations = []
        
        for i in range(nb_radiations):
            # Client avec inscription antérieure
            clients_inscrits = [
                cle for cle, dates in self.clients_inscriptions.items()
                if any((date_jour - d).days >= 90 for d in dates)
            ]
            
            if clients_inscrits and random.random() < 0.70:
                cle_bdf = random.choice(clients_inscrits)
                # Inscription la plus ancienne
                date_inscription = min(self.clients_inscriptions[cle_bdf])
            else:
                # Nouveau client (radiation historique)
                cle_bdf = self.generer_client_fictif(date_jour)
                jours_avant = random.randint(90, 1825)
                date_inscription = date_jour - timedelta(days=jours_avant)
            
            # Type radiation
            rand = random.random()
            cumul = 0
            type_radiation = 'REGULARISATION_VOLONTAIRE'
            for type_rad, prob in self.types_radiations.items():
                cumul += prob
                if rand <= cumul:
                    type_radiation = type_rad
                    break
            
            # Durée et montant
            duree_jours = (date_jour - date_inscription).days
            if type_radiation == 'FIN_DELAI_LEGAL':
                duree_jours = 1825
                date_inscription = date_jour - timedelta(days=1825)
            
            montant = 0 if type_radiation == 'ERREUR_CONTESTATION' else random.randint(500, 15000)
            organisme = random.choice(self.organismes)
            
            # Motifs sans accents
            motifs = {
                'REGULARISATION_VOLONTAIRE': [
                    'Remboursement integral de la creance',
                    'Accord amiable avec etablissement',
                    'Paiement echelonne respecte'
                ],
                'FIN_DELAI_LEGAL': [
                    'Delai legal de 5 ans ecoule',
                    'Radiation automatique reglementaire'
                ],
                'ERREUR_CONTESTATION': [
                    'Erreur de saisie corrigee',
                    'Contestation fondee acceptee'
                ]
            }
            
            motif = random.choice(motifs[type_radiation])
            
            radiations.append({
                'date_radiation': date_jour.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'type_radiation': type_radiation,
                'date_inscription_origine': date_inscription.strftime('%Y-%m-%d'),
                'duree_inscription_jours': duree_jours,
                'montant_radie': montant,
                'organisme_demandeur': organisme,
                'motif_detaille': motif
            })
        
        return radiations
    
    def sauvegarder_fichier_quotidien(self, donnees, type_fichier, date_jour, dossier_base):
        """Sauvegarde fichier quotidien"""
        if not donnees:
            return None
        
        # Structure par mois
        annee_mois = date_jour.strftime('%Y-%m')
        dossier_mois = dossier_base / annee_mois
        dossier_mois.mkdir(parents=True, exist_ok=True)
        
        nom_fichier = f"{type_fichier}_{date_jour.strftime('%Y%m%d')}.csv"
        chemin_fichier = dossier_mois / nom_fichier
        
        df = pd.DataFrame(donnees)
        df.to_csv(chemin_fichier, index=False, encoding='utf-8')
        
        return chemin_fichier
    
    def generer_jour_automatique(self, date_jour, dossier_base):
        """
        GÉNÉRATION QUOTIDIENNE AUTOMATIQUE AVEC CONFORMITÉ ≤ 9.6%
        """
        if date_jour.weekday() >= 5:  # Weekend
            logger.info(f"⏭️ {date_jour} (Weekend) - Pas de génération")
            return None
        
        logger.info(f"🗓️ Génération automatique {date_jour} (Conformité ≤ 9.6%)")
        
        dossier_base = Path(dossier_base)
        
        # 1. Consultations
        consultations = self.generer_consultations_jour(date_jour)
        fichier_consult = self.sauvegarder_fichier_quotidien(
            consultations, 'consultations', date_jour, 
            dossier_base / "consultations"
        )
        
        # 2. Inscriptions CONFORMES
        inscriptions = self.generer_inscriptions_jour_conforme(date_jour)
        fichier_inscr = self.sauvegarder_fichier_quotidien(
            inscriptions, 'inscriptions', date_jour,
            dossier_base / "inscriptions"
        )
        
        # 3. Radiations
        radiations = self.generer_radiations_jour(date_jour)
        fichier_rad = self.sauvegarder_fichier_quotidien(
            radiations, 'radiations', date_jour,
            dossier_base / "radiations"
        )
        
        logger.info(f"  ✅ {len(consultations)} consultations, {len(inscriptions)} inscriptions, {len(radiations)} radiations")
        
        return {
            'consultations': len(consultations),
            'inscriptions': len(inscriptions), 
            'radiations': len(radiations)
        }

def main():
    """Test générateur quotidien automatique"""
    print("🤖 GÉNÉRATEUR QUOTIDIEN FICP AUTOMATIQUE")
    print("="*50)
    print("⚖️ Conformité réglementaire ≤ 9.6% garantie")
    print("🔄 Génération automatique quotidienne")
    print("="*50)
    
    generateur = GenerateurQuotidienFICPAutomatique()
    base_path = "DataLakeE7/historique_quotidien"
    
    # Test sur aujourd'hui
    date_test = date.today()
    
    try:
        stats = generateur.generer_jour_automatique(date_test, base_path)
        
        if stats:
            print(f"\n🎊 Génération {date_test} réussie !")
            print(f"📊 {stats['consultations']} consultations")
            print(f"📝 {stats['inscriptions']} inscriptions (≤9.6% non-conformes)") 
            print(f"☢️ {stats['radiations']} radiations")
            print(f"⚖️ Conformité réglementaire respectée !")
        else:
            print(f"\n⏭️ {date_test} est un weekend - Pas de génération")
            
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()