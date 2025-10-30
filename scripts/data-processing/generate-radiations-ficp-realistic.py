#!/usr/bin/env python3
"""
E7 CERTIFICATION - GÉNÉRATEUR RADIATIONS FICP RÉALISTES
=======================================================
Description: Génère les radiations FICP avec données métier réalistes
Version: 1.0.0
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole
Date: 2025-10-30
License: MIT

LOGIQUE MÉTIER RADIATIONS FICP:
1. Régularisation volontaire (70% des cas)
2. Fin de délai légal (5 ans automatique)
3. Erreur/contestation (rare, 5%)
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class RadiationsFICPRealistesGenerator:
    """Générateur de radiations FICP avec logique métier réaliste"""
    
    def __init__(self):
        self.radiations = []
        
        # Types de radiation avec probabilités réalistes
        self.types_radiation = {
            'REGULARISATION_VOLONTAIRE': 0.70,  # Client règle sa dette
            'FIN_DELAI_LEGAL': 0.25,           # 5 ans écoulés
            'ERREUR_CONTESTATION': 0.05        # Erreur administrative
        }
        
        # Durées moyennes avant radiation
        self.durees_moyenne = {
            'REGULARISATION_VOLONTAIRE': (30, 180),    # 1-6 mois
            'FIN_DELAI_LEGAL': (1825, 1825),          # Exactement 5 ans
            'ERREUR_CONTESTATION': (15, 90)           # 2 semaines à 3 mois
        }
    
    def generer_cle_bdf(self, nom: str, prenom: str, date_naissance: str) -> str:
        """Génère une clé BDF réaliste (13 caractères)"""
        def normaliser(texte):
            replacements = {
                'à': 'A', 'á': 'A', 'â': 'A', 'ã': 'A', 'ä': 'A', 'å': 'A',
                'è': 'E', 'é': 'E', 'ê': 'E', 'ë': 'E',
                'ì': 'I', 'í': 'I', 'î': 'I', 'ï': 'I',
                'ò': 'O', 'ó': 'O', 'ô': 'O', 'õ': 'O', 'ö': 'O',
                'ù': 'U', 'ú': 'U', 'û': 'U', 'ü': 'U',
                'ý': 'Y', 'ÿ': 'Y', 'ç': 'C', 'ñ': 'N'
            }
            result = texte.upper()
            for old, new in replacements.items():
                result = result.replace(old.upper(), new)
            return ''.join(c for c in result if c.isalnum())
        
        nom_clean = normaliser(nom)[:6].ljust(6, 'X')
        prenom_clean = normaliser(prenom)[:4].ljust(4, 'X')
        
        # Date de naissance format AAMMJJ
        try:
            if '-' in date_naissance:
                year, month, day = date_naissance.split('-')
            else:
                year, month, day = date_naissance[:4], date_naissance[4:6], date_naissance[6:8]
            date_part = year[2:] + month + day
        except:
            date_part = "000101"
        
        # Clé contrôle (1 caractère)
        checksum = sum(ord(c) for c in nom_clean + prenom_clean + date_part) % 10
        
        return nom_clean + prenom_clean + date_part + str(checksum)
    
    def charger_clients_inscrits(self):
        """Charge les clients inscrits depuis les courriers existants"""
        courrier_path = Path("DataLakeE7/tables_finales/TABLE_COURRIERS_FICP_REALISTIC.csv")
        
        clients_inscrits = []
        
        if courrier_path.exists():
            df_courriers = pd.read_csv(courrier_path)
            
            # Clients avec inscription (pas encore radié)
            inscriptions = df_courriers[df_courriers['type_courrier'] == 'INSCRIPTION']
            radiations_existantes = df_courriers[df_courriers['type_courrier'] == 'RADIATION']['cle_bdf'].tolist()
            
            # Clients inscrits mais pas encore radiés
            for _, row in inscriptions.iterrows():
                cle_bdf = row['cle_bdf']
                if cle_bdf not in radiations_existantes:
                    date_inscription = pd.to_datetime(row['date_envoi'])
                    clients_inscrits.append({
                        'cle_bdf': cle_bdf,
                        'date_inscription': date_inscription
                    })
            
            logger.info(f"Clients inscrits à traiter: {len(clients_inscrits)}")
            
        return clients_inscrits
    
    def generer_radiations_historiques(self, nb_radiations: int = 300):
        """Génère des radiations historiques sur les 5 dernières années"""
        logger.info(f"Génération de {nb_radiations} radiations historiques")
        
        noms = ['MARTIN', 'BERNARD', 'THOMAS', 'PETIT', 'ROBERT', 'RICHARD', 'DURAND', 'DUBOIS', 'MOREAU', 'LAURENT']
        prenoms = ['JEAN', 'MARIE', 'PIERRE', 'MICHEL', 'ALAIN', 'PHILIPPE', 'DANIEL', 'BERNARD', 'CHRISTOPHE', 'PATRICK']
        
        for i in range(nb_radiations):
            # Génération identité
            nom = random.choice(noms)
            prenom = random.choice(prenoms)
            date_naissance = datetime(
                random.randint(1960, 1995),
                random.randint(1, 12),
                random.randint(1, 28)
            ).strftime('%Y-%m-%d')
            
            cle_bdf = self.generer_cle_bdf(nom, prenom, date_naissance)
            
            # Type de radiation selon probabilités
            rand = random.random()
            cumul = 0
            type_radiation = 'REGULARISATION_VOLONTAIRE'
            
            for type_rad, prob in self.types_radiation.items():
                cumul += prob
                if rand <= cumul:
                    type_radiation = type_rad
                    break
            
            # Date de radiation selon le type
            if type_radiation == 'FIN_DELAI_LEGAL':
                # Exactement 5 ans après inscription
                date_inscription = datetime.now() - timedelta(days=random.randint(1825, 2190))  # 5-6 ans
                date_radiation = date_inscription + timedelta(days=1825)
            else:
                # Autres types: radiation plus récente
                duree_min, duree_max = self.durees_moyenne[type_radiation]
                duree = random.randint(duree_min, duree_max)
                date_radiation = datetime.now() - timedelta(days=random.randint(0, 365))
                date_inscription = date_radiation - timedelta(days=duree)
            
            # Montant radié (estimation de la dette initiale)
            if type_radiation == 'ERREUR_CONTESTATION':
                montant_radie = 0  # Pas de dette réelle
            else:
                montant_radie = random.randint(500, 15000)
            
            # Organisme qui a demande la radiation - UNIQUEMENT CA/SOF/LCL
            organismes = ['CA', 'SOF', 'LCL']
            organisme = random.choice(organismes)
            
            self.radiations.append({
                'date_radiation': date_radiation.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'type_radiation': type_radiation,
                'date_inscription_origine': date_inscription.strftime('%Y-%m-%d'),
                'duree_inscription_jours': (date_radiation - date_inscription).days,
                'montant_radie': montant_radie,
                'organisme_demandeur': organisme,
                'motif_detaille': self._generer_motif_detaille(type_radiation)
            })
    
    def traiter_clients_inscrits_actuels(self, clients_inscrits: list):
        """Traite les clients actuellement inscrits pour d'éventuelles radiations"""
        logger.info(f"Traitement de {len(clients_inscrits)} clients inscrits actuels")
        
        for client in clients_inscrits:
            cle_bdf = client['cle_bdf']
            date_inscription = client['date_inscription']
            duree_inscription = (datetime.now() - date_inscription).days
            
            # Probabilité de radiation selon la durée d'inscription
            if duree_inscription >= 1825:  # 5 ans: radiation automatique
                prob_radiation = 1.0
                type_radiation = 'FIN_DELAI_LEGAL'
            elif duree_inscription >= 365:  # 1 an: 30% de chance de régularisation
                prob_radiation = 0.30
                type_radiation = 'REGULARISATION_VOLONTAIRE'
            elif duree_inscription >= 180:  # 6 mois: 20% de chance
                prob_radiation = 0.20
                type_radiation = 'REGULARISATION_VOLONTAIRE'
            else:  # Moins de 6 mois: 5% de chance
                prob_radiation = 0.05
                type_radiation = 'REGULARISATION_VOLONTAIRE'
            
            if random.random() < prob_radiation:
                if type_radiation == 'FIN_DELAI_LEGAL':
                    date_radiation = date_inscription + timedelta(days=1825)
                else:
                    date_radiation = datetime.now() - timedelta(days=random.randint(0, 30))
                
                montant_radie = random.randint(1000, 20000)
                organismes = ['CA', 'SOF', 'LCL']
                
                self.radiations.append({
                    'date_radiation': date_radiation.strftime('%Y-%m-%d'),
                    'cle_bdf': cle_bdf,
                    'type_radiation': type_radiation,
                    'date_inscription_origine': date_inscription.strftime('%Y-%m-%d'),
                    'duree_inscription_jours': (date_radiation - date_inscription).days,
                    'montant_radie': montant_radie,
                    'organisme_demandeur': random.choice(organismes),
                    'motif_detaille': self._generer_motif_detaille(type_radiation)
                })
    
    def _generer_motif_detaille(self, type_radiation: str) -> str:
        """Génère un motif détaillé selon le type de radiation"""
        motifs = {
            'REGULARISATION_VOLONTAIRE': [
                'Remboursement integral de la creance',
                'Accord amiable avec etablissement',
                'Paiement echelonne respecte',
                'Regularisation suite negociation'
            ],
            'FIN_DELAI_LEGAL': [
                'Delai legal de 5 ans ecoule',
                'Radiation automatique reglementaire',
                'Fin de periode inscription legale'
            ],
            'ERREUR_CONTESTATION': [
                'Erreur de saisie corrigee',
                'Contestation fondee acceptee',
                'Inscription abusive annulee',
                'Erreur identification rectifiee'
            ]
        }
        
        return random.choice(motifs.get(type_radiation, ['Motif non spécifié']))
    
    def generer_statistiques(self, df_radiations):
        """Génère les statistiques des radiations"""
        stats = df_radiations['type_radiation'].value_counts()
        total = len(df_radiations)
        
        logger.info("=" * 60)
        logger.info("STATISTIQUES RADIATIONS FICP")
        logger.info("=" * 60)
        logger.info(f"Total radiations générées: {total:,}")
        
        for type_rad, count in stats.items():
            pct = (count / total * 100)
            logger.info(f"  • {type_rad}: {count:,} ({pct:.1f}%)")
        
        # Statistiques sur les montants
        montant_moyen = df_radiations['montant_radie'].mean()
        logger.info(f"Montant moyen radié: {montant_moyen:,.0f} €")
        
        # Statistiques sur les durées
        duree_moyenne = df_radiations['duree_inscription_jours'].mean()
        logger.info(f"Durée moyenne inscription: {duree_moyenne:.0f} jours ({duree_moyenne/365:.1f} ans)")
        
        logger.info("=" * 60)

def main():
    """Fonction principale"""
    print("GENERATION RADIATIONS FICP REALISTES")
    print("=" * 50)
    
    # Créer les dossiers nécessaires
    output_dir = Path("DataLakeE7/tables_finales")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Générer les radiations
    generateur = RadiationsFICPRealistesGenerator()
    
    # 1. Charger les clients inscrits actuels
    clients_inscrits = generateur.charger_clients_inscrits()
    
    # 2. Générer des radiations historiques
    generateur.generer_radiations_historiques(300)
    
    # 3. Traiter les clients inscrits actuels
    generateur.traiter_clients_inscrits_actuels(clients_inscrits)
    
    # 4. Créer le DataFrame final
    df_radiations = pd.DataFrame(generateur.radiations)
    
    # Tri par date de radiation
    df_radiations['date_radiation'] = pd.to_datetime(df_radiations['date_radiation'])
    df_radiations = df_radiations.sort_values('date_radiation')
    df_radiations['date_radiation'] = df_radiations['date_radiation'].dt.strftime('%Y-%m-%d')
    
    # 5. Statistiques
    generateur.generer_statistiques(df_radiations)
    
    # 6. Sauvegarde
    output_path = output_dir / "TABLE_RADIATIONS_FICP_REALISTIC.csv"
    df_radiations.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"Fichier genere: {output_path}")
    print(f"Total: {len(df_radiations):,} radiations")
    print("GENERATION TERMINEE !")

if __name__ == "__main__":
    main()