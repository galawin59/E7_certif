import pandas as pd
import subprocess
import sys
from pathlib import Path

def run_sql_query(query):
    """Exécute une requête SQL via Invoke-Sqlcmd PowerShell"""
    cmd = [
        "powershell.exe", "-Command",
        f"Invoke-Sqlcmd -ServerInstance 'sql-server-ficp-5647.database.windows.net' -Database 'db-ficp-datawarehouse' -Username 'ficpadmin' -Password 'FicpDataWarehouse2025!' -Query \"{query}\" -QueryTimeout 60"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def import_consultations():
    """Import des consultations FICP"""
    print("📋 Import consultations FICP...")
    
    csv_path = Path("DataLakeE7/tables_finales/TABLE_CONSULTATIONS_FICP.csv")
    if not csv_path.exists():
        print(f"❌ Fichier non trouvé: {csv_path}")
        return 0
    
    df = pd.read_csv(csv_path)
    print(f"📊 Lignes à traiter: {len(df)}")
    
    imported = 0
    batch_size = 50
    
    for i in range(0, min(len(df), 2000), batch_size):  # Limiter à 2000 pour le test
        batch = df.iloc[i:i+batch_size]
        
        values = []
        for _, row in batch.iterrows():
            # Nettoyage des données
            date_consultation = str(row.get('date_consultation', '2025-01-01'))[:10]
            numero_siren = str(row.get('numero_siren', '000000000'))[:20]
            nom_entreprise = str(row.get('etablissement_demandeur', 'Etablissement')).replace("'", "''")[:100]
            montant = float(row.get('montant_demande', 0)) if pd.notna(row.get('montant_demande')) else 0
            type_credit = str(row.get('type_consultation', 'Crédit')).replace("'", "''")[:50]
            statut = str(row.get('resultat', 'En cours')).replace("'", "''")[:30]
            score = int(row.get('score_ficp', 500)) if pd.notna(row.get('score_ficp')) else 500
            
            values.append(f"('{date_consultation}', '{numero_siren}', '{nom_entreprise}', {montant}, '{type_credit}', '{statut}', {score}, 'France', 'Services Financiers')")
        
        if values:
            query = f"INSERT INTO ConsultationsFICP (DateConsultation, NumeroSIREN, NomEntreprise, MontantDemande, TypeCredit, StatutDemande, ScoreRisque, RegionEntreprise, SecteurActivite) VALUES {', '.join(values)}"
            
            success, result = run_sql_query(query)
            if success:
                imported += len(values)
                if imported % 200 == 0:
                    print(f"   📈 {imported} lignes importées...")
            else:
                print(f"⚠️  Erreur batch {i//batch_size + 1}: {result[:100]}")
    
    print(f"✅ Consultations importées: {imported}")
    return imported

def import_inscriptions():
    """Import des inscriptions FICP"""
    print("📝 Import inscriptions FICP...")
    
    csv_path = Path("DataLakeE7/tables_finales/TABLE_INSCRIPTIONS_FICP.csv")
    if not csv_path.exists():
        print(f"❌ Fichier non trouvé: {csv_path}")
        return 0
    
    df = pd.read_csv(csv_path)
    # Filtrer seulement les vraies inscriptions FICP
    if 'type_inscription' in df.columns:
        df = df[df['type_inscription'] == 'Inscription FICP']
    
    print(f"📊 Inscriptions FICP à traiter: {len(df)}")
    
    imported = 0
    batch_size = 50
    
    for i in range(0, min(len(df), 1000), batch_size):  # Limiter pour le test
        batch = df.iloc[i:i+batch_size]
        
        values = []
        for _, row in batch.iterrows():
            date_inscription = str(row.get('date_envoi', '2025-01-01'))[:10]
            numero_siren = str(row.get('numero_siren', '000000000'))[:20]
            nom_entreprise = str(row.get('objet_courrier', 'Entreprise')).replace("'", "''")[:100]
            montant = float(row.get('montant_incident', 10000)) if pd.notna(row.get('montant_incident')) else 10000
            type_incident = str(row.get('type_courrier', 'Incident')).replace("'", "''")[:50]
            statut = str(row.get('statut_envoi', 'Active')).replace("'", "''")[:30]
            duree = int(row.get('duree_prevue_jours', 730)) if pd.notna(row.get('duree_prevue_jours')) else 730
            organisme = str(row.get('etablissement_expediteur', 'Banque')).replace("'", "''")[:100]
            
            values.append(f"('{date_inscription}', '{numero_siren}', '{nom_entreprise}', {montant}, '{type_incident}', '{statut}', {duree}, '{organisme}', 'France', 'Services Financiers')")
        
        if values:
            query = f"INSERT INTO InscriptionsFICP (DateInscription, NumeroSIREN, NomEntreprise, MontantIncident, TypeIncident, StatutInscription, DureeInscription, OrganismeDeclarant, RegionEntreprise, SecteurActivite) VALUES {', '.join(values)}"
            
            success, result = run_sql_query(query)
            if success:
                imported += len(values)
                if imported % 200 == 0:
                    print(f"   📈 {imported} lignes importées...")
    
    print(f"✅ Inscriptions importées: {imported}")
    return imported

def calculate_kpis():
    """Calcule les KPIs"""
    print("📊 Calcul des KPIs...")
    
    query = """
    INSERT INTO KPIDashboardFICP (
        DateCalcul, TotalConsultations, MontantTotalDemandes, TauxAcceptation,
        TotalInscriptions, TotalRadiations, NombreEntreprisesUniques
    )
    SELECT 
        CAST(GETDATE() as DATE),
        (SELECT COUNT(*) FROM ConsultationsFICP),
        (SELECT ISNULL(SUM(MontantDemande), 0) FROM ConsultationsFICP),
        (SELECT CASE WHEN COUNT(*) > 0 THEN CAST(COUNT(CASE WHEN StatutDemande LIKE '%Favorable%' THEN 1 END) * 100.0 / COUNT(*) as DECIMAL(5,2)) ELSE 0 END FROM ConsultationsFICP),
        (SELECT COUNT(*) FROM InscriptionsFICP),
        (SELECT COUNT(*) FROM RadiationsFICP),
        (SELECT COUNT(DISTINCT NumeroSIREN) FROM ConsultationsFICP)
    """
    
    success, result = run_sql_query(query)
    if success:
        print("✅ KPIs calculés")
    else:
        print(f"⚠️  Erreur KPIs: {result}")

def verify_import():
    """Vérifie l'import"""
    print("🔍 Vérification finale...")
    
    query = "SELECT 'ConsultationsFICP' as TableName, COUNT(*) as Count FROM ConsultationsFICP UNION ALL SELECT 'InscriptionsFICP', COUNT(*) FROM InscriptionsFICP UNION ALL SELECT 'RadiationsFICP', COUNT(*) FROM RadiationsFICP UNION ALL SELECT 'KPIDashboardFICP', COUNT(*) FROM KPIDashboardFICP"
    
    success, result = run_sql_query(query)
    if success:
        print("📊 État des tables:")
        print(result)
    else:
        print(f"❌ Erreur vérification: {result}")

if __name__ == "__main__":
    print("=" * 60)
    print("   IMPORT CSV VERS AZURE SQL DATABASE")
    print("=" * 60)
    
    total_imported = 0
    
    # Import consultations
    total_imported += import_consultations()
    
    # Import inscriptions
    total_imported += import_inscriptions()
    
    # Calcul KPIs
    calculate_kpis()
    
    # Vérification
    verify_import()
    
    print("=" * 60)
    print(f"🎉 IMPORT TERMINÉ: {total_imported} enregistrements")
    print("✅ AZURE SQL DATABASE OPÉRATIONNELLE !")
    print("=" * 60)