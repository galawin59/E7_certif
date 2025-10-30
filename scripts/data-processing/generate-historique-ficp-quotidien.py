#!/usr/bin/env python3
"""
E7 CERTIFICATION - GÉNÉRATEUR D'HISTORIQUE FICP QUOTIDIEN
=========================================================
Description: Génère 10 mois d'historique FICP (janvier-octobre 2025)
             avec fichiers quotidiens séparés pour simulation production
Version: 1.0.0
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole
Date: 2025-10-30
License: MIT

PRODUCTION RÉALISTE:
- 800-1000 consultations/jour
- 200-300 inscriptions/jour (80% surveillance, 20% inscription)
- 50-80 radiations/jour
- 1 fichier CSV par jour et par type
"""

import pandas as pd
import random
from datetime import datetime, timedelta, date
from pathlib import Path
import logging
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class GenerateurHistoriqueFICPQuotidien:
    """Générateur d'historique FICP avec fichiers quotidiens réalistes"""
    
    def __init__(self):
        # Paramètres production réalistes
        self.consultations_par_jour = (800, 1000)  # Min, Max
        self.inscriptions_par_jour = (200, 300)    # Min, Max
        self.radiations_par_jour = (50, 80)        # Min, Max
        
        # Organismes UNIQUEMENT CA/SOF/LCL
        self.organismes = ['CA', 'SOF', 'LCL']
        
        # Noms/prénoms français
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
        
        # Types de radiations avec probabilités
        self.types_radiations = {
            'REGULARISATION_VOLONTAIRE': 0.70,
            'FIN_DELAI_LEGAL': 0.25,
            'ERREUR_CONTESTATION': 0.05
        }
        
        # Historique des clients pour cohérence
        self.clients_database = {}  # cle_bdf -> infos client
        self.clients_surveillances = {}  # cle_bdf -> date_surveillance
        self.clients_inscriptions = {}   # cle_bdf -> date_inscription
    
    def generer_cle_bdf(self, nom, prenom, date_naissance):
        """Génère une clé BDF réaliste (13 caractères)"""
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
        """Génère un client fictif avec clé BDF"""
        nom = random.choice(self.noms)
        prenom = random.choice(self.prenoms)
        
        # Date naissance (18-80 ans avant date de référence)
        age_jours = random.randint(18*365, 80*365)
        date_naissance = date_reference - timedelta(days=age_jours)
        
        cle_bdf = self.generer_cle_bdf(nom, prenom, date_naissance)
        
        # Stocker pour cohérence future
        self.clients_database[cle_bdf] = {
            'nom': nom,
            'prenom': prenom,
            'date_naissance': date_naissance,
            'organisme_principal': random.choice(self.organismes)
        }
        
        return cle_bdf
    
    def generer_consultations_jour(self, date_jour):
        """Génère les consultations FICP pour un jour donné"""
        nb_consultations = random.randint(*self.consultations_par_jour)
        consultations = []
        
        logger.info(f"  📋 {nb_consultations} consultations pour {date_jour}")
        
        for i in range(nb_consultations):
            # Client (nouveau ou existant avec faible probabilité)
            if random.random() < 0.95 or not self.clients_database:
                cle_bdf = self.generer_client_fictif(date_jour)
            else:
                cle_bdf = random.choice(list(self.clients_database.keys()))
            
            # Réponse FICP (15% inscrits)
            reponse = 'INSCRIT' if random.random() < 0.15 else 'NON_INSCRIT'
            
            # Organisme demandeur
            if cle_bdf in self.clients_database:
                # 70% chance d'utiliser l'organisme principal du client
                if random.random() < 0.70:
                    organisme = self.clients_database[cle_bdf]['organisme_principal']
                else:
                    organisme = random.choice(self.organismes)
            else:
                organisme = random.choice(self.organismes)
            
            # Heure consultation (heures ouvrables)
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
    
    def generer_inscriptions_jour(self, date_jour):
        """Génère les inscriptions/surveillances FICP pour un jour donné"""
        nb_inscriptions = random.randint(*self.inscriptions_par_jour)
        inscriptions = []
        
        logger.info(f"  📝 {nb_inscriptions} inscriptions/surveillances pour {date_jour}")
        
        for i in range(nb_inscriptions):
            # Client (privilégier clients existants inscrits ou nouveaux)
            if self.clients_database and random.random() < 0.60:
                # 60% chance de prendre un client existant
                cle_bdf = random.choice(list(self.clients_database.keys()))
            else:
                # 40% nouveaux clients (incidents externes)
                cle_bdf = self.generer_client_fictif(date_jour)
            
            # Type de courrier (80% surveillance, 20% inscription)
            if random.random() < 0.80:
                type_courrier = 'SURVEILLANCE'
                # Stocker pour futures inscriptions
                self.clients_surveillances[cle_bdf] = date_jour
            else:
                type_courrier = 'INSCRIPTION'
                # Vérifier norme 31-37 jours après surveillance
                if cle_bdf in self.clients_surveillances:
                    date_surveillance = self.clients_surveillances[cle_bdf]
                    ecart_jours = (date_jour - date_surveillance).days
                    # Si pas dans la norme, ajuster (exceptionnellement)
                    if not (31 <= ecart_jours <= 37):
                        # Garder quand même pour simulation réaliste
                        pass
                
                # Stocker pour futures radiations
                self.clients_inscriptions[cle_bdf] = date_jour
            
            inscriptions.append({
                'date_envoi': date_jour.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'type_courrier': type_courrier
            })
        
        return inscriptions
    
    def generer_radiations_jour(self, date_jour):
        """Génère les radiations FICP pour un jour donné"""
        nb_radiations = random.randint(*self.radiations_par_jour)
        radiations = []
        
        logger.info(f"  ☢️ {nb_radiations} radiations pour {date_jour}")
        
        for i in range(nb_radiations):
            # Client (privilégier clients avec inscriptions anciennes)
            clients_eligible = [
                cle for cle, date_insc in self.clients_inscriptions.items()
                if (date_jour - date_insc).days >= 90  # Au moins 3 mois
            ]
            
            if clients_eligible and random.random() < 0.70:
                # 70% clients avec inscription existante
                cle_bdf = random.choice(clients_eligible)
                date_inscription = self.clients_inscriptions[cle_bdf]
            else:
                # 30% nouveaux clients (radiations historiques)
                cle_bdf = self.generer_client_fictif(date_jour)
                # Date inscription fictive (entre 3 mois et 5 ans avant)
                jours_avant = random.randint(90, 1825)
                date_inscription = date_jour - timedelta(days=jours_avant)
            
            # Type de radiation selon probabilités
            rand = random.random()
            cumul = 0
            type_radiation = 'REGULARISATION_VOLONTAIRE'
            
            for type_rad, prob in self.types_radiations.items():
                cumul += prob
                if rand <= cumul:
                    type_radiation = type_rad
                    break
            
            # Durée inscription selon le type
            duree_jours = (date_jour - date_inscription).days
            if type_radiation == 'FIN_DELAI_LEGAL':
                duree_jours = 1825  # Forcer 5 ans
                date_inscription = date_jour - timedelta(days=1825)
            
            # Montant radié
            if type_radiation == 'ERREUR_CONTESTATION':
                montant = 0
            else:
                montant = random.randint(500, 15000)
            
            # Organisme
            organisme = random.choice(self.organismes)
            
            # Motif sans accents
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
        """Sauvegarde un fichier quotidien"""
        if not donnees:
            return None
        
        # Créer structure de dossiers par mois
        annee_mois = date_jour.strftime('%Y-%m')
        dossier_mois = dossier_base / annee_mois
        dossier_mois.mkdir(parents=True, exist_ok=True)
        
        # Nom du fichier
        nom_fichier = f"{type_fichier}_{date_jour.strftime('%Y%m%d')}.csv"
        chemin_fichier = dossier_mois / nom_fichier
        
        # Sauvegarder
        df = pd.DataFrame(donnees)
        df.to_csv(chemin_fichier, index=False, encoding='utf-8')
        
        return chemin_fichier
    
    def generer_historique_complet(self, date_debut, date_fin):
        """Génère l'historique FICP complet jour par jour"""
        logger.info("🔥 GÉNÉRATION HISTORIQUE FICP COMPLET - CRAMAGE DE CRÉDITS AZURE ! 🔥")
        logger.info("="*90)
        logger.info(f"Période: {date_debut} → {date_fin}")
        
        # Calculer nombre de jours
        nb_jours = (date_fin - date_debut).days + 1
        logger.info(f"Nombre de jours: {nb_jours}")
        
        # Estimation des volumes
        nb_consultations_total = nb_jours * 900  # Moyenne
        nb_inscriptions_total = nb_jours * 250   # Moyenne
        nb_radiations_total = nb_jours * 65      # Moyenne
        
        logger.info(f"Volume estimé:")
        logger.info(f"  📋 Consultations: {nb_consultations_total:,}")
        logger.info(f"  📝 Inscriptions: {nb_inscriptions_total:,}")
        logger.info(f"  ☢️ Radiations: {nb_radiations_total:,}")
        logger.info(f"  📊 TOTAL: {nb_consultations_total + nb_inscriptions_total + nb_radiations_total:,}")
        logger.info("="*90)
        
        # Créer dossiers de base
        dossier_base = Path("DataLakeE7/historique_quotidien")
        
        dossier_consultations = dossier_base / "consultations"
        dossier_inscriptions = dossier_base / "inscriptions"
        dossier_radiations = dossier_base / "radiations"
        
        # Compteurs
        total_consultations = 0
        total_inscriptions = 0
        total_radiations = 0
        fichiers_generes = 0
        
        # Boucle jour par jour
        date_courante = date_debut
        while date_courante <= date_fin:
            if date_courante.weekday() < 5:  # Lundi=0, Vendredi=4 (jours ouvrables)
                logger.info(f"🗓️ Génération {date_courante} ({date_courante.strftime('%A')})")
                
                # 1. Consultations
                consultations = self.generer_consultations_jour(date_courante)
                fichier_consult = self.sauvegarder_fichier_quotidien(
                    consultations, 'consultations', date_courante, dossier_consultations
                )
                if fichier_consult:
                    total_consultations += len(consultations)
                    fichiers_generes += 1
                
                # 2. Inscriptions/Surveillances
                inscriptions = self.generer_inscriptions_jour(date_courante)
                fichier_inscr = self.sauvegarder_fichier_quotidien(
                    inscriptions, 'inscriptions', date_courante, dossier_inscriptions
                )
                if fichier_inscr:
                    total_inscriptions += len(inscriptions)
                    fichiers_generes += 1
                
                # 3. Radiations
                radiations = self.generer_radiations_jour(date_courante)
                fichier_rad = self.sauvegarder_fichier_quotidien(
                    radiations, 'radiations', date_courante, dossier_radiations
                )
                if fichier_rad:
                    total_radiations += len(radiations)
                    fichiers_generes += 1
            
            else:
                logger.info(f"⏭️ {date_courante} ({date_courante.strftime('%A')}) - Weekend, ignoré")
            
            date_courante += timedelta(days=1)
            
            # Affichage progression
            if date_courante.day == 1 or date_courante == date_fin:
                logger.info(f"📊 Progression: {total_consultations:,} consultations, {total_inscriptions:,} inscriptions, {total_radiations:,} radiations")
        
        # Statistiques finales
        logger.info("="*90)
        logger.info("🎉 GÉNÉRATION HISTORIQUE TERMINÉE !")
        logger.info("="*90)
        logger.info(f"📋 Consultations générées: {total_consultations:,}")
        logger.info(f"📝 Inscriptions générées: {total_inscriptions:,}")
        logger.info(f"☢️ Radiations générées: {total_radiations:,}")
        logger.info(f"📁 Fichiers générés: {fichiers_generes}")
        logger.info(f"📊 Total enregistrements: {total_consultations + total_inscriptions + total_radiations:,}")
        logger.info(f"👥 Clients uniques: {len(self.clients_database):,}")
        logger.info("="*90)
        
        return {
            'consultations': total_consultations,
            'inscriptions': total_inscriptions,
            'radiations': total_radiations,
            'fichiers': fichiers_generes,
            'clients': len(self.clients_database)
        }

def main():
    """Fonction principale - Génération historique FICP production"""
    print("🔥🔥🔥 GÉNÉRATEUR HISTORIQUE FICP - CRAMAGE CRÉDITS AZURE ! 🔥🔥🔥")
    print("="*80)
    print("⚠️ ATTENTION: Génération de 10 mois d'historique quotidien")
    print("📅 Période: 1er janvier 2025 → 30 octobre 2025")
    print("💰 Utilisation intensive des crédits Azure gratuits")
    print("="*80)
    
    confirmation = input("🚀 Confirmer le lancement ? (OUI pour continuer): ")
    if confirmation.upper() != 'OUI':
        print("❌ Génération annulée")
        return
    
    # Dates
    date_debut = date(2025, 1, 1)
    date_fin = date(2025, 10, 30)
    
    # Génération
    generateur = GenerateurHistoriqueFICPQuotidien()
    
    try:
        debut = datetime.now()
        stats = generateur.generer_historique_complet(date_debut, date_fin)
        fin = datetime.now()
        
        duree = fin - debut
        
        print(f"\n🎊 GÉNÉRATION RÉUSSIE EN {duree} !")
        print(f"💾 Données prêtes pour import Azure SQL Database")
        print(f"💰 Prochaine étape: Import massif avec les crédits gratuits !")
        
    except Exception as e:
        logger.error(f"❌ Erreur génération: {e}")
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()