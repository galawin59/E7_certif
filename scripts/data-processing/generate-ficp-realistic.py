#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GÉNÉRATEUR CONSULTATION FICP RÉALISTE - CRÉDIT AGRICOLE/LCL/SOFINCO
================================================================
Contexte métier : Avant octroi de crédit, interrogation du fichier FICP BDF
Structure : date_consultation, cle_bdf (13 car), reponse_registre (inscrit/non inscrit)
"""

import pandas as pd
import random
import unicodedata
from datetime import datetime, timedelta, date
from faker import Faker
import logging

class FICPRealisticGenerator:
    """Générateur consultation FICP réaliste selon processus Crédit Agricole"""
    
    def __init__(self):
        self.fake = Faker('fr_FR')
        self.today = date.today()
        
        # Etablissements du groupe CAPFM - SANS ACCENTS
        self.etablissements_capfm = [
            'CA',
            'LCL', 
            'SOF'
        ]
        
        # Configuration logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def normaliser_texte(self, texte):
        """Normalise nom/prénom selon règles BDF"""
        if not texte:
            return ""
            
        # Convertir en majuscules
        texte = texte.upper()
        
        # Supprimer accents
        texte = unicodedata.normalize('NFD', texte)
        texte = ''.join(c for c in texte if unicodedata.category(c) != 'Mn')
        
        # Garder seulement A-Z
        texte = ''.join(c for c in texte if c.isalpha() and 'A' <= c <= 'Z')
        
        return texte
    
    def generer_cle_bdf(self, nom, prenom, date_naissance):
        """
        Génère clé BDF de 13 caractères selon règles Banque de France
        
        Args:
            nom: Nom de naissance
            prenom: Prénom usuel
            date_naissance: Format AAAAMMJJ (str)
            
        Returns:
            str: Clé BDF de 13 caractères exactement
        """
        # Normalisation
        nom_norm = self.normaliser_texte(nom)
        prenom_norm = self.normaliser_texte(prenom)
        
        # Concaténation base
        base = nom_norm + prenom_norm + str(date_naissance)
        
        # Ajustement à 13 caractères
        if len(base) < 13:
            # Compléter avec X jusqu'à 13
            base = base + 'X' * (13 - len(base))
        elif len(base) > 13:
            # Tronquer à 13
            base = base[:13]
            
        return base
    
    def generer_consultations_jour(self, date_consultation, nb_consultations):
        """Génère les consultations FICP pour une journée"""
        consultations = []
        
        for i in range(nb_consultations):
            # Génération client fictif
            nom = self.fake.last_name()
            prenom = self.fake.first_name()
            
            # Date naissance réaliste (18-80 ans)
            age_jours = random.randint(18*365, 80*365)
            date_naissance = self.today - timedelta(days=age_jours)
            date_naissance_str = date_naissance.strftime('%Y%m%d')
            
            # Génération clé BDF
            cle_bdf = self.generer_cle_bdf(nom, prenom, date_naissance_str)
            
            # Réponse du registre BDF (répartition réaliste)
            # 85% non inscrit, 15% inscrit (taux réel approximatif)
            reponse_registre = random.choices(
                ['NON_INSCRIT', 'INSCRIT'], 
                weights=[85, 15]
            )[0]
            
            # Établissement demandeur
            etablissement = random.choice(self.etablissements_capfm)
            
            # Informations complémentaires pour traçabilité
            consultation = {
                'id_consultation': f'FICP_{date_consultation.strftime("%Y%m%d")}_{i+1:04d}',
                'date_consultation': date_consultation,
                'cle_bdf': cle_bdf,
                'reponse_registre': reponse_registre,
                'etablissement_demandeur': etablissement,
                'nom_client': nom,  # Pour vérification uniquement
                'prenom_client': prenom,  # Pour vérification uniquement
                'date_naissance': date_naissance_str,  # Pour vérification uniquement
                'heure_consultation': f"{random.randint(8,18):02d}:{random.randint(0,59):02d}",
            }
            
            consultations.append(consultation)
            
        return pd.DataFrame(consultations)
    
    def generer_periode_complete(self, date_debut, date_fin):
        """Génère consultations FICP pour toute la période"""
        self.logger.info(f"Génération consultations FICP : {date_debut} à {date_fin}")
        
        all_consultations = []
        current_date = date_debut
        total_consultations = 0
        
        while current_date <= date_fin:
            # Volume variable selon jour semaine
            if current_date.weekday() < 5:  # Lundi-Vendredi
                nb_consultations = random.randint(50, 200)
            else:  # Weekend
                nb_consultations = random.randint(5, 30)
                
            # Génération consultations du jour
            consultations_jour = self.generer_consultations_jour(
                current_date, nb_consultations
            )
            
            all_consultations.append(consultations_jour)
            total_consultations += nb_consultations
            
            if current_date.day == 1:  # Log début de mois
                self.logger.info(f"Traitement mois {current_date.strftime('%Y-%m')}")
                
            current_date += timedelta(days=1)
        
        # Consolidation finale
        df_final = pd.concat(all_consultations, ignore_index=True)
        
        self.logger.info(f"✅ Génération terminée : {total_consultations:,} consultations")
        
        return df_final
    
    def sauvegarder_table_finale(self, df, nom_fichier="TABLE_CONSULTATIONS_FICP_REALISTIC.csv"):
        """Sauvegarde la table finale consolidée"""
        output_path = f"DataLakeE7/tables_finales/{nom_fichier}"
        
        # Créer le dossier si nécessaire
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Sauvegarder (sans les colonnes de vérification en production)
        df_production = df[[
            'id_consultation', 'date_consultation', 'cle_bdf', 
            'reponse_registre', 'etablissement_demandeur', 'heure_consultation'
        ]]
        
        df_production.to_csv(output_path, index=False, encoding='utf-8')
        self.logger.info(f"✅ Table sauvegardée : {output_path}")
        
        return output_path

def main():
    """Génération des consultations FICP réalistes"""
    print("=" * 70)
    print("   GÉNÉRATEUR CONSULTATION FICP RÉALISTE")
    print("   Crédit Agricole / LCL / Sofinco")
    print("=" * 70)
    print()
    
    generator = FICPRealisticGenerator()
    
    # Test avec une période courte
    date_debut = date(2025, 10, 1)
    date_fin = date(2025, 10, 30)  # Octobre 2025
    
    print(f"Période de génération : {date_debut} à {date_fin}")
    print("Structure : date_consultation, cle_bdf (13 car), reponse_registre")
    print()
    
    confirmation = input("Générer les consultations FICP réalistes ? (o/n): ").strip().lower()
    
    if confirmation == 'o':
        # Génération
        df_consultations = generator.generer_periode_complete(date_debut, date_fin)
        
        # Sauvegarde
        fichier_output = generator.sauvegarder_table_finale(df_consultations)
        
        # Statistiques
        print("\n" + "=" * 50)
        print("   GÉNÉRATION TERMINÉE")
        print("=" * 50)
        print(f"Total consultations : {len(df_consultations):,}")
        print(f"Inscrit FICP : {len(df_consultations[df_consultations['reponse_registre'] == 'INSCRIT']):,}")
        print(f"Non inscrit : {len(df_consultations[df_consultations['reponse_registre'] == 'NON_INSCRIT']):,}")
        print(f"Taux inscription : {len(df_consultations[df_consultations['reponse_registre'] == 'INSCRIT']) / len(df_consultations) * 100:.1f}%")
        print(f"Fichier : {fichier_output}")
        
        # Exemple de clés BDF générées
        print("\n📋 EXEMPLES CLÉS BDF GÉNÉRÉES :")
        sample = df_consultations.head(5)
        for _, row in sample.iterrows():
            print(f"  {row['nom_client']} {row['prenom_client']} ({row['date_naissance']}) → {row['cle_bdf']}")
            
        print("\n✅ CONSULTATION FICP RÉALISTE PRÊTE POUR IMPORT AZURE SQL !")
        
    else:
        print("Génération annulée")

if __name__ == "__main__":
    main()