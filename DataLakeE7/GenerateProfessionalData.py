#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de données FICP professionnelles - Période complète 2025
Données du 1er janvier 2025 au 29 octobre 2025 (10 mois)
Certification E7 - Data Engineer
"""

import pandas as pd
from datetime import datetime, timedelta, date
import random
import os
from faker import Faker
import logging

class FICPProfessionalGenerator:
    """Générateur de données FICP professionnelles sur 10 mois"""
    
    def __init__(self):
        self.fake = Faker('fr_FR')
        self.output_dir = "DataLakeE7"
        self.start_date = date(2025, 1, 1)
        self.end_date = date(2025, 10, 29)
        
        # Établissements bancaires réels
        self.etablissements = [
            'BNP Paribas', 'Credit Agricole', 'Societe Generale', 'LCL',
            'Banque Postale', 'Credit Mutuel', 'HSBC France', 'Caisse Epargne',
            'Credit Lyonnais', 'Banque Populaire', 'Axa Banque', 'ING Direct',
            'Boursorama', 'Hello Bank', 'Monabanq', 'Fortuneo'
        ]
        
        # Configuration logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_full_year_data(self):
        """Génère toutes les données de janvier à octobre 2025"""
        self.logger.info("=== GENERATION DONNEES FICP PROFESSIONNELLES ===")
        self.logger.info(f"Periode: {self.start_date} au {self.end_date}")
        
        current_date = self.start_date
        total_files = 0
        total_records = 0
        
        while current_date <= self.end_date:
            # Volume variable selon le jour de la semaine et le mois
            day_multiplier = self._get_day_multiplier(current_date)
            month_multiplier = self._get_month_multiplier(current_date.month)
            
            # Calcul des volumes quotidiens (plus réalistes)
            base_consultations = random.randint(80, 120)
            base_courriers = random.randint(40, 70)
            base_radiations = random.randint(8, 20)
            
            nb_consultations = int(base_consultations * day_multiplier * month_multiplier)
            nb_courriers = int(base_courriers * day_multiplier * month_multiplier)
            nb_radiations = int(base_radiations * day_multiplier * month_multiplier)
            
            # Génération des données du jour
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Consultations
            consultations_df = self._generate_professional_consultations(nb_consultations, current_date)
            consultations_file = f'{self.output_dir}/ficp_consultation_{date_str}.csv'
            consultations_df.to_csv(consultations_file, index=False, encoding='utf-8')
            
            # Courriers
            courriers_df = self._generate_professional_courriers(nb_courriers, current_date)
            courriers_file = f'{self.output_dir}/ficp_courrier_{date_str}.csv'
            courriers_df.to_csv(courriers_file, index=False, encoding='utf-8')
            
            # Radiations
            radiations_df = self._generate_professional_radiations(nb_radiations, current_date)
            radiations_file = f'{self.output_dir}/ficp_radiation_{date_str}.csv'
            radiations_df.to_csv(radiations_file, index=False, encoding='utf-8')
            
            total_files += 3
            total_records += len(consultations_df) + len(courriers_df) + len(radiations_df)
            
            # Log périodique
            if current_date.day == 1 or current_date == self.end_date:
                self.logger.info(f"Mois {current_date.strftime('%Y-%m')} genere: C={nb_consultations}, R={nb_courriers}, D={nb_radiations}")
            
            current_date += timedelta(days=1)
        
        self.logger.info(f"=== GENERATION TERMINEE ===")
        self.logger.info(f"Total fichiers: {total_files}")
        self.logger.info(f"Total enregistrements: {total_records:,}")
        self.logger.info(f"Periode couverte: {(self.end_date - self.start_date).days + 1} jours")
        
        return {
            'total_files': total_files,
            'total_records': total_records,
            'start_date': self.start_date,
            'end_date': self.end_date
        }
    
    def _get_day_multiplier(self, date_obj):
        """Multiplieur selon le jour de semaine (moins d'activité weekend)"""
        weekday = date_obj.weekday()  # 0=Lundi, 6=Dimanche
        
        if weekday < 5:  # Lundi-Vendredi
            return random.uniform(0.9, 1.1)
        elif weekday == 5:  # Samedi
            return random.uniform(0.3, 0.6)
        else:  # Dimanche
            return random.uniform(0.1, 0.3)
    
    def _get_month_multiplier(self, month):
        """Multiplieur selon la saisonnalité des crédits"""
        # Janvier: Après fêtes, besoins trésorerie
        # Septembre: Rentrée, nouveaux projets
        # Décembre: Préparation fêtes
        seasonal_multipliers = {
            1: 1.3,   # Janvier - Post fêtes
            2: 0.9,   # Février - Calme
            3: 1.1,   # Mars - Reprise
            4: 1.0,   # Avril - Normal
            5: 1.2,   # Mai - Projets été
            6: 1.0,   # Juin - Normal
            7: 0.8,   # Juillet - Vacances
            8: 0.7,   # Août - Vacances
            9: 1.3,   # Septembre - Rentrée
            10: 1.1,  # Octobre - Projets automne
            11: 1.2,  # Novembre - Préparation fêtes
            12: 1.4   # Décembre - Fêtes
        }
        return seasonal_multipliers.get(month, 1.0)
    
    def _generate_professional_consultations(self, count, date_obj):
        """Génère les consultations FICP professionnelles"""
        consultations = []
        
        for i in range(count):
            # Score FICP réaliste (300-850 comme score crédit)
            score_ficp = random.randint(300, 850)
            
            # Montant selon le type de crédit (plus réaliste)
            type_credit = random.choices([
                'Credit immobilier', 'Credit consommation', 'Credit auto',
                'Credit renouvelable', 'Pret personnel', 'Rachat credit',
                'Credit travaux', 'Pret etudiant'
            ], weights=[25, 20, 15, 10, 12, 8, 7, 3])[0]
            
            # Montants réalistes selon le type
            if type_credit == 'Credit immobilier':
                montant = random.randint(80000, 500000)
            elif type_credit == 'Credit auto':
                montant = random.randint(8000, 45000)
            elif type_credit == 'Credit travaux':
                montant = random.randint(5000, 80000)
            elif type_credit == 'Pret etudiant':
                montant = random.randint(1000, 15000)
            else:
                montant = random.randint(1000, 25000)
            
            # Résultat selon le score FICP
            if score_ficp >= 750:
                resultat = random.choices(['Favorable', 'A etudier'], weights=[85, 15])[0]
            elif score_ficp >= 650:
                resultat = random.choices(['Favorable', 'A etudier', 'Defavorable'], weights=[60, 25, 15])[0]
            elif score_ficp >= 500:
                resultat = random.choices(['Favorable', 'A etudier', 'Defavorable'], weights=[30, 40, 30])[0]
            else:
                resultat = random.choices(['Defavorable', 'A etudier'], weights=[70, 30])[0]
            
            consultation = {
                'id_consultation': f'CONS_{date_obj.strftime("%Y%m%d")}_{i+1:04d}',
                'date_consultation': date_obj,
                'numero_siren': self.fake.siret()[:9],
                'type_consultation': type_credit,
                'montant_demande': montant,
                'duree_mois': self._get_duree_credit(type_credit, montant),
                'resultat': resultat,
                'score_ficp': score_ficp,
                'etablissement_demandeur': random.choice(self.etablissements),
                'motif_consultation': self._get_motif_consultation(type_credit),
                'revenus_declares': random.randint(1500, 8000) if random.random() > 0.1 else None
            }
            consultations.append(consultation)
        
        return pd.DataFrame(consultations)
    
    def _generate_professional_courriers(self, count, date_obj):
        """Génère les courriers FICP professionnels"""
        courriers = []
        
        for i in range(count):
            type_courrier = random.choices([
                'Notification inscription', 'Mise en demeure', 'Information radiation',
                'Courrier explicatif', 'Procedure recours', 'Regularisation',
                'Contestation', 'Relance paiement'
            ], weights=[30, 25, 15, 10, 8, 7, 3, 2])[0]
            
            courrier = {
                'id_courrier': f'COURR_{date_obj.strftime("%Y%m%d")}_{i+1:04d}',
                'date_envoi': date_obj,
                'numero_siren': self.fake.siret()[:9],
                'type_courrier': type_courrier,
                'objet_courrier': self._get_objet_courrier(type_courrier),
                'etablissement_expediteur': random.choice(self.etablissements),
                'canal_envoi': random.choices([
                    'Courrier AR', 'Email certifie', 'Courrier simple', 'SMS'
                ], weights=[50, 30, 15, 5])[0],
                'statut_envoi': random.choices([
                    'Envoye', 'Accuse reception', 'En preparation', 'Echec envoi'
                ], weights=[60, 25, 10, 5])[0],
                'numero_dossier': f'DOSS_{self.fake.siret()[:6]}_{random.randint(1000, 9999)}',
                'priorite': random.choices(['Normale', 'Urgente', 'Critique'], weights=[80, 15, 5])[0]
            }
            courriers.append(courrier)
        
        return pd.DataFrame(courriers)
    
    def _generate_professional_radiations(self, count, date_obj):
        """Génère les radiations FICP professionnelles"""
        radiations = []
        
        for i in range(count):
            # Durée d'inscription réaliste (jusqu'à 5 ans max légal)
            duree_inscription = random.randint(30, 1825)  # 30 jours à 5 ans
            
            # Montant résiduel plus réaliste
            montant_initial = random.randint(5000, 50000)
            taux_recouvre = random.uniform(0.6, 1.0)  # 60% à 100% recouvré
            montant_solde = round(montant_initial * (1 - taux_recouvre), 2)
            
            radiation = {
                'id_radiation': f'RAD_{date_obj.strftime("%Y%m%d")}_{i+1:04d}',
                'date_radiation': date_obj,
                'numero_siren': self.fake.siret()[:9],
                'motif_radiation': random.choices([
                    'Regularisation complete', 'Remboursement integral', 
                    'Prescription legale', 'Decision judiciaire',
                    'Accord amiable', 'Erreur inscription', 'Deces'
                ], weights=[40, 25, 15, 8, 7, 3, 2])[0],
                'montant_solde': montant_solde,
                'montant_initial': montant_initial,
                'taux_recouvrement': round(taux_recouvre * 100, 2),
                'duree_inscription_jours': duree_inscription,
                'etablissement_creancier': random.choice(self.etablissements),
                'statut_radiation': random.choices([
                    'Validee', 'En cours validation', 'Rejetee', 'En attente pieces'
                ], weights=[70, 20, 7, 3])[0],
                'numero_dossier_initial': f'DOSS_{self.fake.siret()[:6]}_{random.randint(1000, 9999)}',
                'date_inscription_initiale': date_obj - timedelta(days=duree_inscription)
            }
            radiations.append(radiation)
        
        return pd.DataFrame(radiations)
    
    def _get_duree_credit(self, type_credit, montant):
        """Durée réaliste selon le type de crédit"""
        if type_credit == 'Credit immobilier':
            return random.randint(180, 300)  # 15-25 ans
        elif type_credit == 'Credit auto':
            return random.randint(36, 84)   # 3-7 ans
        elif type_credit == 'Credit travaux':
            return random.randint(24, 120)  # 2-10 ans
        elif type_credit == 'Pret etudiant':
            return random.randint(12, 60)   # 1-5 ans
        else:
            return random.randint(12, 84)   # 1-7 ans
    
    def _get_motif_consultation(self, type_credit):
        """Motif réaliste selon le type de crédit"""
        motifs = {
            'Credit immobilier': ['Acquisition residence principale', 'Acquisition residence secondaire', 'Investissement locatif'],
            'Credit auto': ['Acquisition vehicule neuf', 'Acquisition vehicule occasion', 'Vehicule professionnel'],
            'Credit travaux': ['Renovation habitat', 'Extension logement', 'Amenagement'],
            'Pret etudiant': ['Financement etudes', 'Frais de scolarite', 'Frais de subsistance']
        }
        return random.choice(motifs.get(type_credit, ['Financement projet', 'Besoin tresorerie']))
    
    def _get_objet_courrier(self, type_courrier):
        """Objet réaliste selon le type de courrier"""
        objets = {
            'Notification inscription': 'Notification inscription fichier FICP',
            'Mise en demeure': 'Mise en demeure de regularisation',
            'Information radiation': 'Information radiation fichier FICP',
            'Procedure recours': 'Information procedures de recours FICP'
        }
        return objets.get(type_courrier, f'Courrier relatif au dossier FICP')

def main():
    """Fonction principale"""
    print("=== GENERATEUR DONNEES FICP PROFESSIONNELLES ===")
    print("Periode: 1er janvier 2025 au 29 octobre 2025")
    print("Suppression du suffixe 'test' pour données professionnelles")
    print("")
    
    confirmation = input("Generer 10 mois de donnees FICP ? (o/n): ").strip().lower()
    
    if confirmation == 'o':
        generator = FICPProfessionalGenerator()
        result = generator.generate_full_year_data()
        
        print("\n" + "="*60)
        print("GENERATION TERMINEE - DONNEES PROFESSIONNELLES")
        print("="*60)
        print(f"Fichiers generes: {result['total_files']:,}")
        print(f"Enregistrements: {result['total_records']:,}")
        print(f"Periode: {result['start_date']} au {result['end_date']}")
        print(f"Duree: {(result['end_date'] - result['start_date']).days + 1} jours")
        print("")
        print("FICHIERS PRETS POUR:")
        print("- Architecture Medallion Bronze/Silver/Gold")
        print("- Pipeline ETL automatise") 
        print("- Upload vers Azure Data Lake")
        print("- Analyses et dashboards Power BI")
        print("")
        print("DONNEES PROFESSIONNELLES SANS 'TEST' GENEREES !")
    else:
        print("Generation annulee")

if __name__ == "__main__":
    main()