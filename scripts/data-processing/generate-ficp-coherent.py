#!/usr/bin/env python3
"""
E7 CERTIFICATION - GÉNÉRATEUR FICP COHÉRENT
===========================================
Description: Génère TOUTES les données FICP avec cohérence des clés BDF
Version: 1.0.0 
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole
Date: 2025-10-30
License: MIT

WORKFLOW COHÉRENT:
1. Génère consultations FICP (base de référence)
2. Génère courriers FICP (utilise clients INSCRITS des consultations)
3. Génère radiations FICP (utilise clients INSCRITS des courriers)
"""

import pandas as pd
import random
from datetime import datetime, timedelta, date
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class GenerateurFICPCoherent:
    """Générateur FICP avec cohérence totale des clés BDF"""
    
    def __init__(self):
        self.consultations = []
        self.courriers = []
        self.radiations = []
        
        # Organismes UNIQUEMENT CA/SOF/LCL
        self.organismes = ['CA', 'SOF', 'LCL']
        
        # Noms/prénoms pour génération
        self.noms = ['MARTIN', 'BERNARD', 'THOMAS', 'PETIT', 'ROBERT', 'RICHARD', 'DURAND', 'DUBOIS', 'MOREAU', 'LAURENT']
        self.prenoms = ['JEAN', 'MARIE', 'PIERRE', 'MICHEL', 'ALAIN', 'PHILIPPE', 'DANIEL', 'BERNARD', 'CHRISTOPHE', 'PATRICK']
        
        # Types de courriers
        self.types_courriers = ['SURVEILLANCE', 'INSCRIPTION', 'RADIATION']
        
        # Types de radiations
        self.types_radiations = {
            'REGULARISATION_VOLONTAIRE': 0.70,
            'FIN_DELAI_LEGAL': 0.25,
            'ERREUR_CONTESTATION': 0.05
        }
    
    def generer_cle_bdf(self, nom, prenom, date_naissance):
        """Génère une clé BDF réaliste (13 caractères)"""
        # Normaliser texte (supprimer accents, garder A-Z)
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
                if '-' in date_naissance:
                    year, month, day = date_naissance.split('-')
                else:
                    year, month, day = date_naissance[:4], date_naissance[4:6], date_naissance[6:8]
            else:
                year, month, day = str(date_naissance.year), f"{date_naissance.month:02d}", f"{date_naissance.day:02d}"
            date_part = year[2:] + month + day
        except:
            date_part = "251030"  # Fallback
        
        # Clé de 13 caractères exactement
        cle_base = nom_clean + prenom_clean + date_part
        if len(cle_base) > 13:
            cle_base = cle_base[:13]
        elif len(cle_base) < 13:
            cle_base = cle_base.ljust(13, 'X')
        
        return cle_base
    
    def etape_1_generer_consultations(self, nb_consultations=3000):
        """ÉTAPE 1: Génère les consultations FICP (base de référence)"""
        logger.info(f"🎯 ÉTAPE 1: Génération de {nb_consultations} consultations FICP")
        
        # Période: octobre 2025
        date_debut = date(2025, 10, 1)
        date_fin = date(2025, 10, 30)
        
        for i in range(nb_consultations):
            # Date aléatoire en octobre
            jours_ecart = random.randint(0, (date_fin - date_debut).days)
            date_consultation = date_debut + timedelta(days=jours_ecart)
            
            # Client fictif
            nom = random.choice(self.noms)
            prenom = random.choice(self.prenoms)
            
            # Date naissance (18-80 ans)
            age_jours = random.randint(18*365, 80*365)
            date_naissance = date_consultation - timedelta(days=age_jours)
            
            # Clé BDF
            cle_bdf = self.generer_cle_bdf(nom, prenom, date_naissance)
            
            # Réponse FICP (15% inscrits)
            reponse = 'INSCRIT' if random.random() < 0.15 else 'NON_INSCRIT'
            
            # Organisme demandeur
            organisme = random.choice(self.organismes)
            
            # Heure consultation
            heure = f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}"
            
            self.consultations.append({
                'id_consultation': f"FICP_{date_consultation.strftime('%Y%m%d')}_{i+1:04d}",
                'date_consultation': date_consultation.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'reponse_registre': reponse,
                'etablissement_demandeur': organisme,
                'heure_consultation': heure
            })
        
        logger.info(f"✅ {len(self.consultations)} consultations générées")
        
        # Statistiques
        inscrits = sum(1 for c in self.consultations if c['reponse_registre'] == 'INSCRIT')
        logger.info(f"   📊 Clients inscrits: {inscrits} ({inscrits/len(self.consultations)*100:.1f}%)")
        
        return inscrits
    
    def etape_2_generer_courriers(self):
        """ÉTAPE 2: Génère courriers basés sur clients INSCRITS des consultations"""
        logger.info("📮 ÉTAPE 2: Génération courriers FICP basés sur consultations")
        
        # Récupérer les clients inscrits
        clients_inscrits = [c for c in self.consultations if c['reponse_registre'] == 'INSCRIT']
        logger.info(f"   🎯 {len(clients_inscrits)} clients inscrits à traiter")
        
        if not clients_inscrits:
            logger.warning("⚠️ Aucun client inscrit trouvé!")
            return 0
        
        for client in clients_inscrits:
            cle_bdf = client['cle_bdf']
            date_consultation = datetime.strptime(client['date_consultation'], '%Y-%m-%d').date()
            
            # 1. SURVEILLANCE (envoyé immédiatement)
            date_surveillance = date_consultation + timedelta(days=random.randint(1, 5))
            self.courriers.append({
                'date_envoi': date_surveillance.strftime('%Y-%m-%d'),
                'cle_bdf': cle_bdf,
                'type_courrier': 'SURVEILLANCE'
            })
            
            # 2. INSCRIPTION (70% des cas, après surveillance)
            # NORME REGLEMENTAIRE: EXACTEMENT entre 31 et 37 jours après surveillance
            if random.random() < 0.70:
                # S'assurer que l'écart est strictement dans la fourchette 31-37
                ecart_jours = random.randint(31, 37)
                date_inscription = date_surveillance + timedelta(days=ecart_jours)
                
                # Vérification supplémentaire pour s'assurer de la conformité
                ecart_reel = (date_inscription - date_surveillance).days
                if 31 <= ecart_reel <= 37:
                    self.courriers.append({
                        'date_envoi': date_inscription.strftime('%Y-%m-%d'),
                        'cle_bdf': cle_bdf,
                        'type_courrier': 'INSCRIPTION'
                    })
                else:
                    # Forcer la conformité
                    date_inscription = date_surveillance + timedelta(days=33)  # Milieu de la fourchette
                    self.courriers.append({
                        'date_envoi': date_inscription.strftime('%Y-%m-%d'),
                        'cle_bdf': cle_bdf,
                        'type_courrier': 'INSCRIPTION'
                    })
                
                # 3. RADIATION (30% des inscrits)
                if random.random() < 0.30:
                    date_radiation = date_inscription + timedelta(days=random.randint(90, 365))
                    self.courriers.append({
                        'date_envoi': date_radiation.strftime('%Y-%m-%d'),
                        'cle_bdf': cle_bdf,
                        'type_courrier': 'RADIATION'
                    })
        
        logger.info(f"✅ {len(self.courriers)} courriers générés")
        
        # Statistiques
        stats = {}
        for courrier in self.courriers:
            type_c = courrier['type_courrier']
            stats[type_c] = stats.get(type_c, 0) + 1
        
        for type_c, count in stats.items():
            pct = count / len(self.courriers) * 100
            logger.info(f"   📊 {type_c}: {count} ({pct:.1f}%)")
        
        return len(self.courriers)
    
    def etape_3_generer_radiations(self):
        """ÉTAPE 3: Génère radiations détaillées basées sur courriers INSCRIPTION"""
        logger.info("☢️ ÉTAPE 3: Génération radiations détaillées")
        
        # Récupérer les clients avec courrier INSCRIPTION
        clients_inscrits = [c for c in self.courriers if c['type_courrier'] == 'INSCRIPTION']
        logger.info(f"   🎯 {len(clients_inscrits)} clients inscrits à traiter")
        
        if not clients_inscrits:
            logger.warning("⚠️ Aucune inscription trouvée!")
            return 0
        
        for client in clients_inscrits:
            cle_bdf = client['cle_bdf']
            date_inscription = datetime.strptime(client['date_envoi'], '%Y-%m-%d').date()
            
            # Probabilité de radiation (50% des inscrits)
            if random.random() < 0.50:
                # Type de radiation selon probabilités
                rand = random.random()
                cumul = 0
                type_radiation = 'REGULARISATION_VOLONTAIRE'
                
                for type_rad, prob in self.types_radiations.items():
                    cumul += prob
                    if rand <= cumul:
                        type_radiation = type_rad
                        break
                
                # Date et durée selon le type
                if type_radiation == 'FIN_DELAI_LEGAL':
                    duree_jours = 1825  # Exactement 5 ans
                    date_radiation = date_inscription + timedelta(days=duree_jours)
                elif type_radiation == 'ERREUR_CONTESTATION':
                    duree_jours = random.randint(15, 90)  # 2 semaines à 3 mois
                    date_radiation = date_inscription + timedelta(days=duree_jours)
                else:  # REGULARISATION_VOLONTAIRE
                    duree_jours = random.randint(30, 365)  # 1 mois à 1 an
                    date_radiation = date_inscription + timedelta(days=duree_jours)
                
                # Montant radié 
                if type_radiation == 'ERREUR_CONTESTATION':
                    montant = 0  # Pas de dette réelle
                else:
                    montant = random.randint(500, 15000)
                
                # Organisme (même répartition CA/SOF/LCL)
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
                
                self.radiations.append({
                    'date_radiation': date_radiation.strftime('%Y-%m-%d'),
                    'cle_bdf': cle_bdf,
                    'type_radiation': type_radiation,
                    'date_inscription_origine': date_inscription.strftime('%Y-%m-%d'),
                    'duree_inscription_jours': duree_jours,
                    'montant_radie': montant,
                    'organisme_demandeur': organisme,
                    'motif_detaille': motif
                })
        
        logger.info(f"✅ {len(self.radiations)} radiations générées")
        
        # Statistiques
        stats = {}
        for radiation in self.radiations:
            type_r = radiation['type_radiation']
            stats[type_r] = stats.get(type_r, 0) + 1
        
        for type_r, count in stats.items():
            pct = count / len(self.radiations) * 100
            logger.info(f"   📊 {type_r}: {count} ({pct:.1f}%)")
        
        return len(self.radiations)
    
    def sauvegarder_fichiers(self):
        """Sauvegarde tous les fichiers CSV"""
        logger.info("💾 Sauvegarde des fichiers CSV")
        
        # Créer le dossier
        output_dir = Path("DataLakeE7/tables_finales")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder consultations
        if self.consultations:
            df_consultations = pd.DataFrame(self.consultations)
            path_consultations = output_dir / "TABLE_CONSULTATIONS_FICP_REALISTIC.csv"
            df_consultations.to_csv(path_consultations, index=False, encoding='utf-8')
            logger.info(f"✅ Consultations: {path_consultations}")
        
        # Sauvegarder courriers
        if self.courriers:
            df_courriers = pd.DataFrame(self.courriers)
            # Trier par date
            df_courriers['date_envoi'] = pd.to_datetime(df_courriers['date_envoi'])
            df_courriers = df_courriers.sort_values('date_envoi')
            df_courriers['date_envoi'] = df_courriers['date_envoi'].dt.strftime('%Y-%m-%d')
            
            path_courriers = output_dir / "TABLE_COURRIERS_FICP_REALISTIC.csv"
            df_courriers.to_csv(path_courriers, index=False, encoding='utf-8')
            logger.info(f"✅ Courriers: {path_courriers}")
        
        # Sauvegarder radiations
        if self.radiations:
            df_radiations = pd.DataFrame(self.radiations)
            # Trier par date
            df_radiations['date_radiation'] = pd.to_datetime(df_radiations['date_radiation'])
            df_radiations = df_radiations.sort_values('date_radiation')
            df_radiations['date_radiation'] = df_radiations['date_radiation'].dt.strftime('%Y-%m-%d')
            
            path_radiations = output_dir / "TABLE_RADIATIONS_FICP_REALISTIC.csv"
            df_radiations.to_csv(path_radiations, index=False, encoding='utf-8')
            logger.info(f"✅ Radiations: {path_radiations}")
    
    def generer_statistiques_finales(self):
        """Génère les statistiques finales de cohérence"""
        logger.info("="*80)
        logger.info("📊 STATISTIQUES FINALES - DONNÉES COHÉRENTES")
        logger.info("="*80)
        
        total_consultations = len(self.consultations)
        total_courriers = len(self.courriers)
        total_radiations = len(self.radiations)
        
        logger.info(f"🔍 Consultations FICP: {total_consultations:,}")
        logger.info(f"📮 Courriers FICP: {total_courriers:,}")
        logger.info(f"☢️ Radiations FICP: {total_radiations:,}")
        logger.info(f"📊 Total général: {total_consultations + total_courriers + total_radiations:,}")
        
        # Vérifier cohérence clés BDF
        if self.consultations and self.courriers:
            cles_consultations = {c['cle_bdf'] for c in self.consultations if c['reponse_registre'] == 'INSCRIT'}
            cles_courriers = {c['cle_bdf'] for c in self.courriers}
            coherence_courriers = len(cles_courriers & cles_consultations) / len(cles_courriers) if cles_courriers else 0
            logger.info(f"🔗 Cohérence consultations→courriers: {coherence_courriers*100:.1f}%")
        
        if self.courriers and self.radiations:
            cles_inscriptions = {c['cle_bdf'] for c in self.courriers if c['type_courrier'] == 'INSCRIPTION'}
            cles_radiations = {r['cle_bdf'] for r in self.radiations}
            coherence_radiations = len(cles_radiations & cles_inscriptions) / len(cles_radiations) if cles_radiations else 0
            logger.info(f"🔗 Cohérence inscriptions→radiations: {coherence_radiations*100:.1f}%")
        
        logger.info("="*80)

def main():
    """Fonction principale - Génération FICP cohérente complète"""
    print("🎯 GÉNÉRATEUR FICP COHÉRENT - E7 CERTIFICATION")
    print("="*60)
    print("Génération avec cohérence totale des clés BDF")
    print("Organismes: CA / SOF / LCL uniquement")
    print("Données sans accents")
    print("="*60)
    
    generateur = GenerateurFICPCoherent()
    
    try:
        # ÉTAPE 1: Consultations (base)
        nb_inscrits = generateur.etape_1_generer_consultations(3000)
        
        if nb_inscrits > 0:
            # ÉTAPE 2: Courriers (basés sur inscrits)
            nb_courriers = generateur.etape_2_generer_courriers()
            
            # ÉTAPE 3: Radiations (basées sur inscriptions)
            nb_radiations = generateur.etape_3_generer_radiations()
            
            # Sauvegarde
            generateur.sauvegarder_fichiers()
            
            # Statistiques finales
            generateur.generer_statistiques_finales()
            
            print("\n🎉 GÉNÉRATION COHÉRENTE TERMINÉE AVEC SUCCÈS!")
        else:
            print("❌ Aucun client inscrit généré - Arrêt du processus")
            
    except Exception as e:
        logger.error(f"❌ Erreur génération: {e}")
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()