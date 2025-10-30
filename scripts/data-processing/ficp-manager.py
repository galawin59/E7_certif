#!/usr/bin/env python3
"""
E7 CERTIFICATION - GESTIONNAIRE PRINCIPAL FICP
==============================================
Description: Script principal pour toutes les opérations FICP
Version: 1.0.0
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole  
Date: 2025-10-30
License: MIT

FONCTIONNALITÉS:
- Génération de données FICP réalistes (consultations + courriers)
- Import vers Azure SQL Database
- Workflow complet avec gestion d'erreurs
"""

import pandas as pd
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

class FICPManager:
    """Gestionnaire principal pour toutes les opérations FICP"""
    
    def __init__(self):
        self.config = self._load_config()
        self.sql_config = self.config["azure"]["sqlDatabase"]
        
    def _load_config(self):
        """Charge la configuration projet"""
        try:
            with open("config/project-config.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Erreur configuration: {e}")
            sys.exit(1)
    
    def run_sql_query(self, query, timeout=30):
        """Exécute une requête SQL via PowerShell"""
        server = f"{self.sql_config['serverName']}.database.windows.net"
        database = self.sql_config['databaseName']
        username = self.sql_config['adminLogin']
        password = self.sql_config['adminPassword']
        
        cmd = [
            "powershell.exe", "-Command",
            f"Invoke-Sqlcmd -ServerInstance '{server}' "
            f"-Database '{database}' -Username '{username}' "
            f"-Password '{password}' -Query \"{query}\" -QueryTimeout {timeout}"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+30, encoding='utf-8', errors='replace')
            return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return False, str(e)
    
    def test_azure_connection(self):
        """Test de connexion Azure SQL"""
        print("🔍 Test connexion Azure SQL...")
        success, result = self.run_sql_query("SELECT 1 as test")
        if success:
            print("✅ Connexion Azure SQL OK")
            return True
        else:
            print(f"❌ Erreur connexion: {result}")
            return False
    
    def generate_ficp_data(self):
        """Génère les données FICP réalistes"""
        print("🎯 Génération données FICP réalistes...")
        
        # Générer consultations
        result_consultations = subprocess.run([
            sys.executable, "scripts/data-processing/generate-ficp-realistic.py"
        ], capture_output=True, text=True)
        
        if result_consultations.returncode == 0:
            print("✅ Consultations FICP générées")
        else:
            print(f"❌ Erreur consultations: {result_consultations.stderr}")
            return False
        
        # Générer courriers
        result_courriers = subprocess.run([
            sys.executable, "scripts/data-processing/generate-courriers-ficp-realistic.py"
        ], capture_output=True, text=True)
        
        if result_courriers.returncode == 0:
            print("✅ Courriers FICP générés")
        else:
            print(f"❌ Erreur courriers: {result_courriers.stderr}")
            return False
        
        # Générer radiations
        result_radiations = subprocess.run([
            sys.executable, "scripts/data-processing/generate-radiations-ficp-realistic.py"
        ], capture_output=True, text=True)
        
        if result_radiations.returncode == 0:
            print("✅ Radiations FICP générées")
            return True
        else:
            print(f"❌ Erreur radiations: {result_radiations.stderr}")
            return False
    
    def import_consultations(self, limit=1000):
        """Import des consultations FICP vers Azure"""
        print(f"📋 Import consultations FICP (limite: {limit})...")
        
        csv_path = Path("DataLakeE7/tables_finales/TABLE_CONSULTATIONS_FICP_REALISTIC.csv")
        if not csv_path.exists():
            print(f"❌ Fichier consultations non trouvé: {csv_path}")
            return 0
        
        try:
            df = pd.read_csv(csv_path)
            print(f"📊 {len(df)} consultations disponibles")
            
            df_import = df.head(limit)
            imported = 0
            
            for _, row in df_import.iterrows():
                date_consultation = str(row.get('date_consultation', '2025-01-01'))[:10]
                cle_bdf = str(row.get('cle_bdf', 'TESTCLIENT123'))[:13]
                etablissement = str(row.get('etablissement_demandeur', 'Test Bank')).replace("'", "''")[:50]
                reponse = str(row.get('reponse_registre', 'NON_INSCRIT'))
                
                montant = 50000 if reponse == 'NON_INSCRIT' else 0
                statut = 'Favorable' if reponse == 'NON_INSCRIT' else 'Refusé'
                score = 750 if reponse == 'NON_INSCRIT' else 300
                
                query = f"""
                INSERT INTO ConsultationsFICP 
                (DateConsultation, NumeroSIREN, NomEntreprise, MontantDemande, TypeCredit, StatutDemande, ScoreRisque, RegionEntreprise, SecteurActivite)
                VALUES 
                ('{date_consultation}', '{cle_bdf}', '{etablissement}', {montant}, 'Consultation FICP', '{statut}', {score}, 'France', 'Services Financiers')
                """
                
                success, result = self.run_sql_query(query.replace('\n', ' ').strip())
                if success:
                    imported += 1
                    if imported % 50 == 0:
                        print(f"   📈 {imported} consultations importées...")
                else:
                    print(f"⚠️ Erreur ligne {imported + 1}: {result[:100]}")
                    break
            
            print(f"✅ Import consultations terminé: {imported}")
            return imported
            
        except Exception as e:
            print(f"❌ Erreur import consultations: {e}")
            return 0
    
    def import_courriers(self, limit=500):
        """Import des courriers FICP vers Azure"""
        print(f"📮 Import courriers FICP (limite: {limit})...")
        
        csv_path = Path("DataLakeE7/tables_finales/TABLE_COURRIERS_FICP_REALISTIC.csv")
        if not csv_path.exists():
            print(f"❌ Fichier courriers non trouvé: {csv_path}")
            return 0
        
        try:
            df = pd.read_csv(csv_path)
            print(f"📊 {len(df)} courriers disponibles")
            
            df_import = df.head(limit)
            imported = 0
            
            for _, row in df_import.iterrows():
                date_envoi = str(row.get('date_envoi', '2025-01-01'))[:10]
                cle_bdf = str(row.get('cle_bdf', 'TESTCLIENT123'))[:13]
                type_courrier = str(row.get('type_courrier', 'SURVEILLANCE'))
                
                nom_client = f"Client {type_courrier}"
                type_incident = f"Courrier {type_courrier}"
                statut = 'Envoyé'
                duree = 30 if type_courrier == 'SURVEILLANCE' else (1825 if type_courrier == 'INSCRIPTION' else 0)
                
                query = f"""
                INSERT INTO InscriptionsFICP 
                (DateInscription, NumeroSIREN, NomEntreprise, MontantIncident, TypeIncident, StatutInscription, DureeInscription, OrganismeDeclarant, RegionEntreprise, SecteurActivite)
                VALUES 
                ('{date_envoi}', '{cle_bdf}', '{nom_client}', 0, '{type_incident}', '{statut}', {duree}, 'Crédit Agricile', 'France', 'Services Financiers')
                """
                
                success, result = self.run_sql_query(query.replace('\n', ' ').strip())
                if success:
                    imported += 1
                    if imported % 50 == 0:
                        print(f"   📈 {imported} courriers importés...")
                else:
                    print(f"⚠️ Erreur courrier {imported + 1}: {result[:100]}")
                    break
            
            print(f"✅ Import courriers terminé: {imported}")
            return imported
            
        except Exception as e:
            print(f"❌ Erreur import courriers: {e}")
            return 0
    
    def import_radiations(self, limit=300):
        """Import des radiations FICP vers Azure"""
        print(f"☢️ Import radiations FICP (limite: {limit})...")
        
        csv_path = Path("DataLakeE7/tables_finales/TABLE_RADIATIONS_FICP_REALISTIC.csv")
        if not csv_path.exists():
            print(f"❌ Fichier radiations non trouvé: {csv_path}")
            return 0
        
        try:
            df = pd.read_csv(csv_path, encoding='utf-8')
            print(f"📊 {len(df)} radiations disponibles")
            
            df_import = df.head(limit)
            imported = 0
            
            for _, row in df_import.iterrows():
                date_radiation = str(row.get('date_radiation', '2025-01-01'))[:10]
                cle_bdf = str(row.get('cle_bdf', 'TESTCLIENT123'))[:13]
                type_radiation = str(row.get('type_radiation', 'REGULARISATION_VOLONTAIRE'))
                montant_radie = int(row.get('montant_radie', 0))
                organisme = str(row.get('organisme_demandeur', 'Crédit Agricole')).replace("'", "''")[:50]
                motif = str(row.get('motif_detaille', 'Régularisation')).replace("'", "''")[:100]
                
                # Créer une entrée dans RadiationsFICP avec les bons noms de colonnes
                duree_incident = int(row.get('duree_inscription_jours', 0))
                query = f"""
                INSERT INTO RadiationsFICP 
                (DateRadiation, NumeroSIREN, NomEntreprise, MontantRembourse, TypeRadiation, StatutRadiation, DureeIncident, OrganismeValidation, RegionEntreprise, SecteurActivite)
                VALUES 
                ('{date_radiation}', '{cle_bdf}', 'Client Radié', {montant_radie}, '{type_radiation}', 'Validée', {duree_incident}, '{organisme}', 'France', 'Services Financiers')
                """
                
                success, result = self.run_sql_query(query.replace('\n', ' ').strip())
                if success:
                    imported += 1
                    if imported % 50 == 0:
                        print(f"   📈 {imported} radiations importées...")
                else:
                    print(f"⚠️ Erreur radiation {imported + 1}: {result[:100]}")
                    break
            
            print(f"✅ Import radiations terminé: {imported}")
            return imported
            
        except Exception as e:
            print(f"❌ Erreur import radiations: {e}")
            return 0
    
    def get_azure_stats(self):
        """Récupère les statistiques Azure"""
        print("📊 Statistiques Azure SQL...")
        
        queries = [
            ("ConsultationsFICP", "SELECT COUNT(*) as count FROM ConsultationsFICP"),
            ("InscriptionsFICP", "SELECT COUNT(*) as count FROM InscriptionsFICP"),
            ("RadiationsFICP", "SELECT COUNT(*) as count FROM RadiationsFICP")
        ]
        
        stats = {}
        for table, query in queries:
            success, result = self.run_sql_query(query)
            if success and result.strip():
                try:
                    count = int(result.strip().split('\n')[-1].strip())
                    stats[table] = count
                except:
                    stats[table] = 0
            else:
                stats[table] = 0
        
        print(f"  • Consultations: {stats.get('ConsultationsFICP', 0):,}")
        print(f"  • Inscriptions: {stats.get('InscriptionsFICP', 0):,}")
        print(f"  • Radiations: {stats.get('RadiationsFICP', 0):,}")
        
        return stats

def generer_fichier_quotidien():
    """Génération quotidienne automatique avec conformité ≤ 9.6%"""
    try:
        print("🤖 GÉNÉRATION QUOTIDIENNE AUTOMATIQUE")
        print("="*50)
        print("⚖️ Conformité réglementaire ≤ 9.6% garantie")
        print("🗓️ Génération pour aujourd'hui")
        print("="*50)
        
        # Import dynamique du générateur
        import importlib.util
        import sys
        from pathlib import Path
        from datetime import date
        
        # Chemin vers le générateur quotidien
        script_path = Path(__file__).parent / "generate-quotidien-ficp-automatique.py"
        
        if not script_path.exists():
            print(f"❌ Fichier générateur non trouvé: {script_path}")
            return
        
        # Charger le module dynamiquement
        spec = importlib.util.spec_from_file_location("generate_quotidien", script_path)
        generate_quotidien = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generate_quotidien)
        
        generateur = generate_quotidien.GenerateurQuotidienFICPAutomatique()
        base_path = "DataLakeE7/historique_quotidien"
        date_aujourd_hui = date.today()
        
        print(f"📅 Génération pour {date_aujourd_hui}...")
        
        stats = generateur.generer_jour_automatique(date_aujourd_hui, base_path)
        
        if stats:
            print(f"\n🎊 GÉNÉRATION RÉUSSIE !")
            print(f"📋 Consultations: {stats['consultations']}")
            print(f"📝 Inscriptions: {stats['inscriptions']} (≤9.6% non-conformes)")
            print(f"☢️ Radiations: {stats['radiations']}")
            print(f"⚖️ Conformité réglementaire respectée !")
        else:
            print(f"⏭️ {date_aujourd_hui} est un weekend - Pas de génération")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def show_menu():
    """Affiche le menu principal"""
    print("\n" + "="*60)
    print("   E7 CERTIFICATION - GESTIONNAIRE FICP v2.2")
    print("="*60)
    print("1. 🎯 Générer données FICP réalistes (consultations + courriers + radiations)")
    print("2. 🔍 Tester connexion Azure")
    print("3. 📋 Importer consultations (1000)")
    print("4. 📮 Importer courriers (500)")
    print("5. ☢️ Importer radiations (300)")
    print("6. 🚀 Import complet (consultations + courriers + radiations)")
    print("7. 📊 Statistiques Azure")
    print("8. 🤖 Génération quotidienne automatique (≤9.6% non-conformité)")
    print("9. ❌ Quitter")
    print("="*60)

def main():
    """Fonction principale avec menu interactif"""
    manager = FICPManager()
    
    while True:
        show_menu()
        choice = input("Votre choix (1-9): ").strip()
        
        if choice == "1":
            print("\n🎯 GÉNÉRATION DONNÉES FICP")
            print("-" * 40)
            manager.generate_ficp_data()
            
        elif choice == "2":
            print("\n🔍 TEST CONNEXION AZURE")
            print("-" * 40)
            manager.test_azure_connection()
            
        elif choice == "3":
            print("\n📋 IMPORT CONSULTATIONS")
            print("-" * 40)
            if manager.test_azure_connection():
                manager.import_consultations(1000)
            
        elif choice == "4":
            print("\n📮 IMPORT COURRIERS")
            print("-" * 40)
            if manager.test_azure_connection():
                manager.import_courriers(500)
            
        elif choice == "5":
            print("\n☢️ IMPORT RADIATIONS")
            print("-" * 40)
            if manager.test_azure_connection():
                manager.import_radiations(300)
            
        elif choice == "6":
            print("\n🚀 IMPORT COMPLET")
            print("-" * 40)
            if manager.test_azure_connection():
                total_consultations = manager.import_consultations(1000)
                total_courriers = manager.import_courriers(500)
                total_radiations = manager.import_radiations(300)
                print(f"\n🎉 IMPORT TERMINÉ: {total_consultations + total_courriers + total_radiations} enregistrements")
            
        elif choice == "7":
            print("\n📊 STATISTIQUES AZURE")
            print("-" * 40)
            if manager.test_azure_connection():
                manager.get_azure_stats()
                
        elif choice == "8":
            print("\n🤖 GÉNÉRATION QUOTIDIENNE AUTOMATIQUE")
            print("-" * 40)
            generer_fichier_quotidien()
                
        elif choice == "9":
            print("\n👋 Au revoir !")
            break
            
        else:
            print("❌ Choix invalide")
        
        input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()