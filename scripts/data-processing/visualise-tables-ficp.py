#!/usr/bin/env python3
"""
E7 CERTIFICATION - VISUALISATEUR TABLES FICP
============================================
Description: Script pour visualiser les données des tables Azure SQL
Version: 1.0.0
Author: E7 Data Engineering Team - Expert FICP Crédit Agricole
Date: 2025-10-30
License: MIT
"""

import pandas as pd
import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime

class FICPTableVisualizer:
    """Visualisateur des tables FICP Azure SQL"""
    
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
        """Exécute une requête SQL et retourne un DataFrame"""
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
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)
    
    def get_table_overview(self, table_name, limit=10):
        """Récupère un aperçu d'une table"""
        print(f"\n{'='*60}")
        print(f"📋 TABLE: {table_name}")
        print(f"{'='*60}")
        
        # Compter les enregistrements
        success, result = self.run_sql_query(f"SELECT COUNT(*) as total FROM {table_name}")
        if success and result.strip():
            try:
                total = int(result.strip().split('\n')[-1].strip())
                print(f"📊 Total enregistrements: {total:,}")
            except:
                total = 0
        else:
            total = 0
        
        if total == 0:
            print("⚠️ Table vide")
            return
        
        # Récupérer les données
        success, result = self.run_sql_query(f"SELECT TOP {limit} * FROM {table_name}")
        if success and result.strip():
            lines = result.strip().split('\n')
            if len(lines) >= 3:  # Headers + separator + data
                print(f"🔍 Aperçu (TOP {limit}):")
                print("-" * 60)
                for line in lines:
                    if line.strip():
                        print(line)
            else:
                print("⚠️ Données non formatées correctement")
        else:
            print(f"❌ Erreur récupération données: {result}")
    
    def get_ficp_statistics(self):
        """Génère les statistiques FICP complètes"""
        print(f"\n{'='*80}")
        print(f"📈 STATISTIQUES FICP DÉTAILLÉES - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*80}")
        
        # Statistiques par table
        tables = ["ConsultationsFICP", "InscriptionsFICP", "RadiationsFICP"]
        totals = {}
        
        for table in tables:
            success, result = self.run_sql_query(f"SELECT COUNT(*) as count FROM {table}")
            if success and result.strip():
                try:
                    count = int(result.strip().split('\n')[-1].strip())
                    totals[table] = count
                except:
                    totals[table] = 0
            else:
                totals[table] = 0
        
        print(f"🔍 Consultations FICP: {totals['ConsultationsFICP']:,}")
        print(f"📝 Inscriptions FICP: {totals['InscriptionsFICP']:,}")
        print(f"☢️ Radiations FICP: {totals['RadiationsFICP']:,}")
        print(f"📊 Total général: {sum(totals.values()):,}")
        
        # Statistiques détaillées par type de radiation
        if totals['RadiationsFICP'] > 0:
            print(f"\n🔬 ANALYSE RADIATIONS FICP:")
            print("-" * 40)
            success, result = self.run_sql_query("""
                SELECT TypeRadiation, COUNT(*) as count 
                FROM RadiationsFICP 
                GROUP BY TypeRadiation 
                ORDER BY count DESC
            """)
            if success and result.strip():
                lines = result.strip().split('\n')[2:]  # Skip headers
                for line in lines:
                    if line.strip() and '---' not in line:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            type_rad = parts[0]
                            count = parts[-1]
                            try:
                                pct = (int(count) / totals['RadiationsFICP'] * 100)
                                print(f"  • {type_rad}: {count} ({pct:.1f}%)")
                            except:
                                print(f"  • {type_rad}: {count}")
        
        # Statistiques par organisme
        print(f"\n🏛️ TOP 5 ORGANISMES (Radiations):")
        print("-" * 40)
        success, result = self.run_sql_query("""
            SELECT TOP 5 OrganismeValidation, COUNT(*) as count 
            FROM RadiationsFICP 
            GROUP BY OrganismeValidation 
            ORDER BY count DESC
        """)
        if success and result.strip():
            lines = result.strip().split('\n')[2:]  # Skip headers
            for line in lines:
                if line.strip() and '---' not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        organisme = ' '.join(parts[:-1])
                        count = parts[-1]
                        print(f"  • {organisme}: {count}")
    
    def export_to_csv(self, table_name, limit=1000):
        """Exporte une table vers CSV"""
        print(f"\n📤 EXPORT {table_name} vers CSV...")
        
        success, result = self.run_sql_query(f"SELECT TOP {limit} * FROM {table_name}")
        if success and result.strip():
            # Créer le dossier d'export
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            # Nom du fichier avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = export_dir / f"{table_name}_{timestamp}.csv"
            
            try:
                # Écrire le résultat brut
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result)
                
                print(f"✅ Export réussi: {filename}")
                return str(filename)
            except Exception as e:
                print(f"❌ Erreur export: {e}")
                return None
        else:
            print(f"❌ Erreur récupération données: {result}")
            return None

def show_menu():
    """Affiche le menu de visualisation"""
    print("\n" + "="*60)
    print("   E7 CERTIFICATION - VISUALISATEUR TABLES FICP")
    print("="*60)
    print("1. 📋 Aperçu ConsultationsFICP (TOP 10)")
    print("2. 📝 Aperçu InscriptionsFICP (TOP 10)")
    print("3. ☢️ Aperçu RadiationsFICP (TOP 10)")
    print("4. 📊 Statistiques FICP complètes")
    print("5. 📤 Exporter ConsultationsFICP vers CSV")
    print("6. 📤 Exporter InscriptionsFICP vers CSV")
    print("7. 📤 Exporter RadiationsFICP vers CSV")
    print("8. 🔍 Vue d'ensemble (toutes les tables)")
    print("9. ❌ Quitter")
    print("="*60)

def main():
    """Fonction principale avec menu interactif"""
    visualizer = FICPTableVisualizer()
    
    while True:
        show_menu()
        choice = input("Votre choix (1-9): ").strip()
        
        if choice == "1":
            visualizer.get_table_overview("ConsultationsFICP", 10)
            
        elif choice == "2":
            visualizer.get_table_overview("InscriptionsFICP", 10)
            
        elif choice == "3":
            visualizer.get_table_overview("RadiationsFICP", 10)
            
        elif choice == "4":
            visualizer.get_ficp_statistics()
            
        elif choice == "5":
            visualizer.export_to_csv("ConsultationsFICP", 2000)
            
        elif choice == "6":
            visualizer.export_to_csv("InscriptionsFICP", 1000)
            
        elif choice == "7":
            visualizer.export_to_csv("RadiationsFICP", 500)
            
        elif choice == "8":
            print("\n🔍 VUE D'ENSEMBLE - TOUTES LES TABLES")
            visualizer.get_table_overview("ConsultationsFICP", 5)
            visualizer.get_table_overview("InscriptionsFICP", 5)
            visualizer.get_table_overview("RadiationsFICP", 5)
            visualizer.get_ficp_statistics()
            
        elif choice == "9":
            print("\n👋 Au revoir !")
            break
            
        else:
            print("❌ Choix invalide")
        
        input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()