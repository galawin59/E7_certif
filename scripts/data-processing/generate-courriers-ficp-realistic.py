#!/usr/bin/env python3
"""
E7 CERTIFICATION - GÉNÉRATEUR COURRIERS FICP RÉALISTES
=====================================================
Description: Génère des courriers FICP avec workflow métier réaliste
Version: 1.0.0
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole
Date: 2025-10-30
License: MIT

PROCESSUS MÉTIER FICP:
1. SURVEILLANCE → Courrier de mise en demeure (30 jours pour régulariser)
2. INSCRIPTION → Si pas de régularisation sous 30 jours
3. RADIATION → Si régularisation OU après 5 ans légaux
"""

import pandas as pd
import random
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class CourriersRealistes:
    """Générateur de courriers FICP avec workflow métier réaliste"""
    
    def __init__(self):
        self.clients_surveilles = {}  # {cle_bdf: date_surveillance}
        self.clients_inscrits = {}    # {cle_bdf: date_inscription}
        self.courriers = []
        
        # Probabilités réalistes basées sur l'expérience Crédit Agricole
        self.proba_regularisation_surveillance = 0.70  # 70% régularisent après surveillance
        self.proba_regularisation_inscription = 0.30   # 30% régularisent après inscription
        
    def generer_cle_bdf(self, nom: str, prenom: str, date_naissance: str) -> str:
        """
        Génère une clé BDF réaliste (13 caractères)
        Algorithme basé sur l'expérience Crédit Agricole
        """
        # Normalisation des caractères
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
    
    def charger_clients_existants(self):
        """Charge les clients existants depuis le fichier de consultations réalistes"""
        consultation_path = Path("DataLakeE7/tables_finales/TABLE_CONSULTATIONS_FICP_REALISTIC.csv")
        
        if consultation_path.exists():
            df_consultations = pd.read_csv(consultation_path)
            logger.info(f"📋 Chargement de {len(df_consultations)} consultations existantes")
            
            # Extraire les clients inscrits (réponse INSCRIT)
            clients_inscrits = df_consultations[df_consultations['reponse_registre'] == 'INSCRIT']
            
            for _, row in clients_inscrits.iterrows():
                cle_bdf = row['cle_bdf']
                # Simuler une date d'inscription antérieure à la consultation
                date_consultation = pd.to_datetime(row['date_consultation'])
                date_inscription = date_consultation - timedelta(days=random.randint(30, 1825))  # 1 mois à 5 ans
                self.clients_inscrits[cle_bdf] = date_inscription
                
            logger.info(f"✅ {len(self.clients_inscrits)} clients inscrits identifiés")
        else:
            logger.warning("⚠️ Aucun fichier de consultations trouvé, génération autonome")
    
    def generer_nouveaux_incidents(self, nb_incidents: int = 200):
        """Génère de nouveaux incidents avec le workflow réaliste"""
        logger.info(f"🎯 Génération de {nb_incidents} nouveaux incidents")
        
        noms = ['MARTIN', 'BERNARD', 'DUBOIS', 'THOMAS', 'ROBERT', 'PETIT', 'DURAND', 'LEROY', 'MOREAU', 'SIMON']
        prenoms = ['PIERRE', 'MARIE', 'JEAN', 'CLAUDE', 'ANNE', 'MICHEL', 'FRANCOISE', 'PATRICK', 'CHRISTINE', 'DANIEL']
        
        for i in range(nb_incidents):
            # Génération identité client
            nom = random.choice(noms)
            prenom = random.choice(prenoms)
            date_naissance = datetime(
                random.randint(1960, 2000),
                random.randint(1, 12), 
                random.randint(1, 28)
            ).strftime('%Y-%m-%d')
            
            cle_bdf = self.generer_cle_bdf(nom, prenom, date_naissance)
            
            # Date de surveillance (incident initial)
            date_surveillance = datetime.now() - timedelta(days=random.randint(1, 90))
            self.clients_surveilles[cle_bdf] = date_surveillance
            
            # Courrier de surveillance
            self.courriers.append({
                'date_envoi': date_surveillance.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'type_courrier': 'SURVEILLANCE'
            })
    
    def traiter_workflow_surveillance(self):
        """Traite le workflow des clients en surveillance"""
        logger.info("🔄 Traitement du workflow surveillance → inscription/radiation")
        
        clients_a_traiter = list(self.clients_surveilles.items())
        
        for cle_bdf, date_surveillance in clients_a_traiter:
            date_limite = date_surveillance + timedelta(days=30)
            
            if random.random() < self.proba_regularisation_surveillance:
                # ✅ RÉGULARISATION → Radiation directe
                date_radiation = date_surveillance + timedelta(days=random.randint(5, 25))
                self.courriers.append({
                    'date_envoi': date_radiation.strftime('%Y-%m-%d'),
                    'cle_bdf': cle_bdf,
                    'type_courrier': 'RADIATION'
                })
                # Retirer de la surveillance
                del self.clients_surveilles[cle_bdf]
                
            else:
                # ❌ PAS DE RÉGULARISATION → Inscription
                date_inscription = date_limite + timedelta(days=random.randint(1, 7))
                self.courriers.append({
                    'date_envoi': date_inscription.strftime('%Y-%m-%d'),
                    'cle_bdf': cle_bdf,
                    'type_courrier': 'INSCRIPTION'
                })
                
                # Déplacer vers les inscrits
                self.clients_inscrits[cle_bdf] = date_inscription
                del self.clients_surveilles[cle_bdf]
    
    def traiter_workflow_inscription(self):
        """Traite le workflow des clients inscrits"""
        logger.info("🔄 Traitement du workflow inscription → radiation")
        
        clients_a_traiter = list(self.clients_inscrits.items())
        
        for cle_bdf, date_inscription in clients_a_traiter:
            duree_inscription = (datetime.now() - date_inscription).days
            
            # Cas 1: Régularisation volontaire (probabilité décroissante dans le temps)
            if duree_inscription < 1825 and random.random() < self.proba_regularisation_inscription:
                # Radiation entre 30 jours et 3 ans après inscription
                jours_radiation = random.randint(30, min(1095, max(60, duree_inscription)))
                date_radiation = date_inscription + timedelta(days=jours_radiation)
                self.courriers.append({
                    'date_envoi': date_radiation.strftime('%Y-%m-%d'),
                    'cle_bdf': cle_bdf,
                    'type_courrier': 'RADIATION'
                })
                del self.clients_inscrits[cle_bdf]
                
            # Cas 2: Délai légal de 5 ans dépassé
            elif duree_inscription >= 1825:  # 5 ans
                date_radiation = date_inscription + timedelta(days=1825)
                self.courriers.append({
                    'date_envoi': date_radiation.strftime('%Y-%m-%d'),
                    'cle_bdf': cle_bdf,
                    'type_courrier': 'RADIATION'
                })
                del self.clients_inscrits[cle_bdf]
    
    def generer_courriers_complets(self):
        """Génère l'ensemble des courriers avec workflow réaliste"""
        logger.info("🚀 Génération complète des courriers FICP")
        
        # 1. Charger les clients existants
        self.charger_clients_existants()
        
        # 2. Générer de nouveaux incidents
        self.generer_nouveaux_incidents()
        
        # 3. Traiter les workflows
        self.traiter_workflow_surveillance()
        self.traiter_workflow_inscription()
        
        # 4. Créer le DataFrame final
        df_courriers = pd.DataFrame(self.courriers)
        
        # Tri par date d'envoi
        df_courriers['date_envoi'] = pd.to_datetime(df_courriers['date_envoi'])
        df_courriers = df_courriers.sort_values('date_envoi')
        df_courriers['date_envoi'] = df_courriers['date_envoi'].dt.strftime('%Y-%m-%d')
        
        return df_courriers
    
    def generer_statistiques(self, df_courriers):
        """Génère les statistiques du workflow"""
        stats = df_courriers['type_courrier'].value_counts()
        total = len(df_courriers)
        
        logger.info("=" * 50)
        logger.info("📊 STATISTIQUES COURRIERS FICP")
        logger.info("=" * 50)
        logger.info(f"Total courriers générés: {total:,}")
        logger.info(f"  • Surveillance: {stats.get('SURVEILLANCE', 0):,} ({stats.get('SURVEILLANCE', 0)/total*100:.1f}%)")
        logger.info(f"  • Inscription: {stats.get('INSCRIPTION', 0):,} ({stats.get('INSCRIPTION', 0)/total*100:.1f}%)")
        logger.info(f"  • Radiation: {stats.get('RADIATION', 0):,} ({stats.get('RADIATION', 0)/total*100:.1f}%)")
        logger.info("=" * 50)

def main():
    """Fonction principale"""
    print("GENERATION COURRIERS FICP REALISTES")
    print("=" * 50)
    
    # Créer les dossiers nécessaires
    output_dir = Path("DataLakeE7/tables_finales")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Générer les courriers
    generateur = CourriersRealistes()
    df_courriers = generateur.generer_courriers_complets()
    
    # Statistiques
    generateur.generer_statistiques(df_courriers)
    
    # Sauvegarde
    output_path = output_dir / "TABLE_COURRIERS_FICP_REALISTIC.csv"
    df_courriers.to_csv(output_path, index=False, encoding='utf-8')
    
    print(f"Fichier genere: {output_path}")
    print(f"Total: {len(df_courriers):,} courriers")
    print("GENERATION TERMINEE !")

if __name__ == "__main__":
    main()