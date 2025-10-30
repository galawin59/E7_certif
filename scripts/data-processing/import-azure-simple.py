#!/usr/bin/env python3
"""
E7 CERTIFICATION - IMPORT AZURE SIMPLE
======================================
Description: Import simple et robuste vers Azure SQL
Version: 1.0.0
Author: E7 Data Engineering Team
Date: 2025-10-30
License: MIT
"""

import pandas as pd
import subprocess
import sys
from pathlib import Path

def run_sql_simple(query):
    """Exécute une requête SQL simple"""
    server = "sql-server-ficp-5647.database.windows.net"
    database = "db-ficp-datawarehouse"
    username = "ficpadmin"
    password = "FicpDataWarehouse2025!"
    
    cmd = [
        "powershell.exe", "-Command",
        f"Invoke-Sqlcmd -ServerInstance '{server}' "
        f"-Database '{database}' -Username '{username}' "
        f"-Password '{password}' -Query \"{query}\" -QueryTimeout 30"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return False, str(e)

def test_connection():
    """Test de connexion simple"""
    print("🔍 Test connexion Azure SQL...")
    success, result = run_sql_simple("SELECT 1 as test")
    if success:
        print("✅ Connexion Azure SQL OK")
        return True
    else:
        print(f"❌ Erreur connexion: {result}")
        return False

def import_consultations_simple():
    """Import consultations simple"""
    print("📋 Import consultations FICP...")
    
    csv_path = Path("DataLakeE7/tables_finales/TABLE_CONSULTATIONS_FICP_REALISTIC.csv")
    if not csv_path.exists():
        print(f"❌ Fichier non trouvé: {csv_path}")
        return 0
    
    try:
        df = pd.read_csv(csv_path)
        print(f"📊 {len(df)} consultations trouvées")
        
        # Limiter à 100 pour test
        df_test = df.head(100)
        imported = 0
        
        for _, row in df_test.iterrows():
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
            
            success, result = run_sql_simple(query)
            if success:
                imported += 1
                if imported % 10 == 0:
                    print(f"   📈 {imported} consultations importées...")
            else:
                print(f"⚠️ Erreur ligne {imported + 1}: {result[:100]}")
                break
        
        print(f"✅ Import terminé: {imported} consultations")
        return imported
        
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return 0

def main():
    """Fonction principale simple"""
    print("🚀 IMPORT AZURE SQL SIMPLE")
    print("=" * 40)
    
    # Test connexion
    if not test_connection():
        print("❌ Connexion impossible, arrêt")
        return
    
    # Import
    total = import_consultations_simple()
    
    print("=" * 40)
    print(f"🎉 TERMINÉ: {total} enregistrements importés")

if __name__ == "__main__":
    main()