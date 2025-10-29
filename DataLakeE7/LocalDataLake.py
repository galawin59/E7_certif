import os
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import shutil

class LocalDataLake:
    """Simulation complète d'un Data Lake Azure en local"""
    
    def __init__(self, base_path="LocalDataLake"):
        self.base_path = Path(base_path)
        self.setup_structure()
    
    def setup_structure(self):
        """Crée la structure Bronze/Silver/Gold du Data Lake"""
        
        # Zones du Data Lake
        zones = {
            'bronze': 'raw/ficp',
            'silver': 'processed/ficp', 
            'gold': 'analytics/ficp'
        }
        
        for zone, subpath in zones.items():
            zone_path = self.base_path / zone / subpath
            zone_path.mkdir(parents=True, exist_ok=True)
            
        print(f"✅ Structure Data Lake créée dans {self.base_path}")
    
    def ingest_to_bronze(self, csv_files):
        """Ingestion des CSV bruts vers la zone Bronze"""
        bronze_path = self.base_path / 'bronze' / 'raw' / 'ficp'
        
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                # Organisation par date et type
                date_str = datetime.now().strftime('%Y/%m/%d')
                file_type = csv_file.split('_')[1]  # consultation, courrier, radiation
                
                target_dir = bronze_path / file_type / date_str
                target_dir.mkdir(parents=True, exist_ok=True)
                
                target_path = target_dir / os.path.basename(csv_file)
                shutil.copy2(csv_file, target_path)
                
                print(f"📥 {csv_file} → Bronze/{file_type}")
    
    def process_to_silver(self):
        """Transformation CSV → Parquet optimisé (Zone Silver)"""
        bronze_path = self.base_path / 'bronze' / 'raw' / 'ficp'
        silver_path = self.base_path / 'silver' / 'processed' / 'ficp'
        
        for data_type in ['consultation', 'courrier', 'radiation']:
            type_path = bronze_path / data_type
            
            if type_path.exists():
                # Traiter tous les CSV du type
                csv_files = list(type_path.rglob('*.csv'))
                
                if csv_files:
                    # Combiner et optimiser
                    all_data = []
                    for csv_file in csv_files:
                        df = pd.read_csv(csv_file)
                        all_data.append(df)
                    
                    if all_data:
                        combined_df = pd.concat(all_data, ignore_index=True)
                        
                        # Optimisations Silver
                        combined_df = self.optimize_dataframe(combined_df, data_type)
                        
                        # Sauvegarde Parquet avec compression
                        date_str = datetime.now().strftime('%Y/%m')
                        silver_dir = silver_path / data_type / date_str
                        silver_dir.mkdir(parents=True, exist_ok=True)
                        
                        parquet_file = silver_dir / f"{data_type}_{datetime.now().strftime('%Y-%m-%d')}.parquet"
                        combined_df.to_parquet(parquet_file, compression='snappy', index=False)
                        
                        print(f"🔄 {len(csv_files)} fichiers CSV → {parquet_file}")
                        print(f"   📊 {len(combined_df)} records, {combined_df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    def optimize_dataframe(self, df, data_type):
        """Optimisations spécifiques par type de données"""
        
        # Optimisations communes
        if 'date_inscription' in df.columns:
            df['date_inscription'] = pd.to_datetime(df['date_inscription'])
            df['annee'] = df['date_inscription'].dt.year
            df['mois'] = df['date_inscription'].dt.month
        
        if 'montant' in df.columns:
            df['montant'] = pd.to_numeric(df['montant'], errors='coerce')
        
        # Optimisations par type
        if data_type == 'consultation':
            # Catégorisation des motifs
            if 'motif_consultation' in df.columns:
                df['motif_consultation'] = df['motif_consultation'].astype('category')
        
        elif data_type == 'courrier':
            # Catégorisation des types de courrier
            if 'type_courrier' in df.columns:
                df['type_courrier'] = df['type_courrier'].astype('category')
        
        elif data_type == 'radiation':
            # Calcul de durées d'inscription
            if 'date_radiation' in df.columns:
                df['date_radiation'] = pd.to_datetime(df['date_radiation'])
                if 'date_inscription' in df.columns:
                    df['duree_inscription_jours'] = (df['date_radiation'] - df['date_inscription']).dt.days
        
        return df
    
    def create_gold_analytics(self):
        """Création d'agrégations métier (Zone Gold)"""
        silver_path = self.base_path / 'silver' / 'processed' / 'ficp'
        gold_path = self.base_path / 'gold' / 'analytics' / 'ficp'
        
        analytics = {}
        
        # Lire les données Silver
        for data_type in ['consultation', 'courrier', 'radiation']:
            type_path = silver_path / data_type
            if type_path.exists():
                parquet_files = list(type_path.rglob('*.parquet'))
                if parquet_files:
                    dfs = [pd.read_parquet(f) for f in parquet_files]
                    analytics[data_type] = pd.concat(dfs, ignore_index=True)
        
        # KPIs quotidiens
        daily_kpis = self.calculate_daily_kpis(analytics)
        
        # KPIs mensuels
        monthly_kpis = self.calculate_monthly_kpis(analytics)
        
        # Sauvegarde des analytics
        gold_dir = gold_path / 'kpis'
        gold_dir.mkdir(parents=True, exist_ok=True)
        
        if not daily_kpis.empty:
            daily_kpis.to_parquet(gold_dir / 'kpis_quotidiens.parquet', index=False)
            daily_kpis.to_csv(gold_dir / 'kpis_quotidiens.csv', index=False)
            print(f"📈 KPIs quotidiens créés ({len(daily_kpis)} jours)")
        
        if not monthly_kpis.empty:
            monthly_kpis.to_parquet(gold_dir / 'kpis_mensuels.parquet', index=False)
            monthly_kpis.to_csv(gold_dir / 'kpis_mensuels.csv', index=False)
            print(f"📊 KPIs mensuels créés ({len(monthly_kpis)} mois)")
        
        # Rapport de synthèse
        self.create_summary_report(analytics, gold_dir)
    
    def calculate_daily_kpis(self, analytics):
        """Calcul des KPIs quotidiens"""
        daily_stats = []
        
        for data_type, df in analytics.items():
            if not df.empty and 'date_inscription' in df.columns:
                daily = df.groupby(df['date_inscription'].dt.date).agg({
                    'client_id': 'count'
                }).rename(columns={'client_id': f'{data_type}_count'})
                
                daily['date'] = daily.index
                daily['type'] = data_type
                daily_stats.append(daily.reset_index(drop=True))
        
        if daily_stats:
            return pd.concat(daily_stats, ignore_index=True)
        return pd.DataFrame()
    
    def calculate_monthly_kpis(self, analytics):
        """Calcul des KPIs mensuels"""
        monthly_stats = []
        
        for data_type, df in analytics.items():
            if not df.empty and 'date_inscription' in df.columns:
                df['year_month'] = df['date_inscription'].dt.to_period('M')
                monthly = df.groupby('year_month').agg({
                    'client_id': ['count', 'nunique'],
                    'montant': ['sum', 'mean'] if 'montant' in df.columns else 'client_id'
                })
                
                monthly.columns = [f'{data_type}_{col[1]}' for col in monthly.columns]
                monthly['period'] = monthly.index.astype(str)
                monthly['type'] = data_type
                monthly_stats.append(monthly.reset_index(drop=True))
        
        if monthly_stats:
            return pd.concat(monthly_stats, ignore_index=True)
        return pd.DataFrame()
    
    def create_summary_report(self, analytics, gold_dir):
        """Rapport de synthèse du Data Lake"""
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'data_lake_stats': {},
            'data_quality': {},
            'business_insights': {}
        }
        
        # Stats générales
        for data_type, df in analytics.items():
            if not df.empty:
                report['data_lake_stats'][data_type] = {
                    'total_records': len(df),
                    'unique_clients': df['client_id'].nunique() if 'client_id' in df.columns else 0,
                    'date_range': {
                        'start': df['date_inscription'].min().isoformat() if 'date_inscription' in df.columns else None,
                        'end': df['date_inscription'].max().isoformat() if 'date_inscription' in df.columns else None
                    },
                    'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024**2
                }
        
        # Qualité des données
        if 'consultation' in analytics:
            df = analytics['consultation']
            report['data_quality']['consultation'] = {
                'completeness': (1 - df.isnull().sum() / len(df)).to_dict(),
                'duplicates': df.duplicated().sum()
            }
        
        # Insights métier
        if analytics:
            total_clients = set()
            for df in analytics.values():
                if 'client_id' in df.columns:
                    total_clients.update(df['client_id'].unique())
            
            report['business_insights'] = {
                'total_unique_clients': len(total_clients),
                'ficp_activity_period': 30,  # derniers 30 jours
                'data_lake_size_mb': sum([stats['memory_usage_mb'] for stats in report['data_lake_stats'].values()])
            }
        
        # Sauvegarde du rapport
        with open(gold_dir / 'data_lake_summary.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Rapport de synthèse créé")
        return report
    
    def get_structure_info(self):
        """Informations sur la structure du Data Lake"""
        
        def get_directory_size(path):
            total = 0
            if path.exists():
                for item in path.rglob('*'):
                    if item.is_file():
                        total += item.stat().st_size
            return total / 1024**2  # MB
        
        zones_info = {}
        for zone in ['bronze', 'silver', 'gold']:
            zone_path = self.base_path / zone
            
            if zone_path.exists():
                files = list(zone_path.rglob('*'))
                file_count = len([f for f in files if f.is_file()])
                dir_count = len([f for f in files if f.is_dir()])
                size_mb = get_directory_size(zone_path)
                
                zones_info[zone] = {
                    'files': file_count,
                    'directories': dir_count,
                    'size_mb': round(size_mb, 2)
                }
        
        return zones_info

def main():
    """Démonstration complète du Data Lake local"""
    
    print("🏗️ CRÉATION DU DATA LAKE LOCAL FICP")
    print("=" * 50)
    
    # Initialisation du Data Lake
    dl = LocalDataLake("LocalDataLake_FICP")
    
    # Étape 1: Génération des données (si pas déjà fait)
    print("\n📊 Étape 1: Vérification des données sources")
    csv_files = [
        f"ficp_consultation_{datetime.now().strftime('%Y-%m-%d')}.csv",
        f"ficp_courrier_{datetime.now().strftime('%Y-%m-%d')}.csv", 
        f"ficp_radiation_{datetime.now().strftime('%Y-%m-%d')}.csv"
    ]
    
    # Vérifier si les fichiers existent
    existing_files = [f for f in csv_files if os.path.exists(f)]
    
    if len(existing_files) < 3:
        print("⚠️ Génération des données manquantes...")
        # Ici on pourrait appeler GenerateWithRadiation.py
        print("💡 Exécutez d'abord: python GenerateWithRadiation.py")
        return
    
    print(f"✅ {len(existing_files)} fichiers de données trouvés")
    
    # Étape 2: Ingestion Bronze
    print("\n📥 Étape 2: Ingestion vers Bronze")
    dl.ingest_to_bronze(existing_files)
    
    # Étape 3: Traitement Silver
    print("\n🔄 Étape 3: Traitement vers Silver")
    dl.process_to_silver()
    
    # Étape 4: Analytics Gold  
    print("\n📈 Étape 4: Création des analytics Gold")
    dl.create_gold_analytics()
    
    # Étape 5: Rapport final
    print("\n📋 Étape 5: Rapport du Data Lake")
    structure = dl.get_structure_info()
    
    print("\n" + "="*50)
    print("🏆 DATA LAKE FICP CRÉÉ AVEC SUCCÈS !")
    print("="*50)
    
    for zone, info in structure.items():
        print(f"{zone.upper():>8}: {info['files']:>3} fichiers, {info['size_mb']:>6.1f} MB")
    
    print(f"\n📁 Localisation: {dl.base_path.absolute()}")
    print("\n💡 Vous avez maintenant un Data Lake complet avec:")
    print("   • Zone Bronze : Données brutes CSV")  
    print("   • Zone Silver : Données optimisées Parquet")
    print("   • Zone Gold   : Analytics et KPIs")
    
    return dl

if __name__ == "__main__":
    main()