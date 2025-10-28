#!/usr/bin/env python3
# ===============================
# SCRIPT PRINCIPAL - GÉNÉRATION ET UPLOAD FICP
# Exécuté dans Azure Container Instances
# ===============================

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import random
from faker import Faker
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/ficp-generator.log')
    ]
)
logger = logging.getLogger(__name__)

class FICPGenerator:
    """Générateur de données FICP pour Azure Data Lake"""
    
    def __init__(self, config):
        self.config = config
        self.faker = Faker('fr_FR')
        self.today = datetime.now().date()
        
        # Configuration métier
        self.agences = ["SOF", "CA", "LCL"]
        self.fic_types = ["FIC1", "FIC2", "FIC3", "FIC4"]
        self.canaux = ["Agence", "Web", "Téléphone"]
        self.motifs_radiation = {
            "remboursement": 0.70,
            "echeance": 0.25,
            "deces": 0.03,
            "erreur": 0.02
        }
        
        logger.info("FICPGenerator initialisé")
    
    def generate_clients(self, count=300):
        """Génère des clients fictifs"""
        logger.info(f"Génération de {count} clients fictifs")
        clients = []
        
        for _ in range(count):
            date_naissance = self.faker.date_of_birth(minimum_age=18, maximum_age=60)
            nom = self.faker.last_name().upper()
            id_client = date_naissance.strftime("%d%m%y") + nom[:5]
            clients.append((id_client, date_naissance.strftime("%d%m%Y"), nom))
        
        return clients
    
    def generate_consultations(self, clients):
        """Génère les consultations FICP"""
        logger.info("Génération des consultations")
        consultations = []
        
        for id_client, _, _ in clients:
            consultations.append({
                "id_client": id_client,
                "date_consultation": self.today.strftime("%Y-%m-%d"),
                "origine_agence": random.choice(self.agences),
                "canal": random.choice(self.canaux)
            })
        
        return pd.DataFrame(consultations)
    
    def generate_courriers(self, clients):
        """Génère les courriers (surveillance + inscriptions)"""
        logger.info("Génération des courriers")
        courriers = []
        
        for id_client, _, _ in clients:
            # Surveillance (obligatoire)
            date_surv = self.today - timedelta(days=random.randint(30, 45))
            courriers.append({
                "id_client": id_client,
                "date_envoi_surveillance": date_surv.strftime("%Y-%m-%d"),
                "date_envoi_inscription": "",
                "type_courrier": "surveillance",
                "fic_type": random.choice(self.fic_types),
                "origine_agence": random.choice(self.agences)
            })
            
            # Inscription (50% des cas)
            if random.random() < 0.5:
                date_insc = date_surv + timedelta(days=random.randint(31, 37))
                courriers.append({
                    "id_client": id_client,
                    "date_envoi_surveillance": "",
                    "date_envoi_inscription": date_insc.strftime("%Y-%m-%d"),
                    "type_courrier": "inscription",
                    "fic_type": random.choice(self.fic_types),
                    "origine_agence": random.choice(self.agences)
                })
        
        return pd.DataFrame(courriers)
    
    def generate_radiations(self, nombre_simule=50):
        """Génère des radiations simulées"""
        logger.info(f"Génération de {nombre_simule} radiations simulées")
        radiations = []
        
        # Simulation basique pour les radiations
        for _ in range(nombre_simule):
            # ID client simulé
            date_naissance = self.faker.date_of_birth(minimum_age=18, maximum_age=60)
            nom = self.faker.last_name().upper()
            id_client = date_naissance.strftime("%d%m%y") + nom[:5]
            
            # Date d'inscription passée
            date_inscription = self.today - timedelta(days=random.randint(90, 365))
            
            # Motif de radiation
            rand = random.random()
            cumul = 0
            motif_choisi = "remboursement"
            
            for motif, prob in self.motifs_radiation.items():
                cumul += prob
                if rand <= cumul:
                    motif_choisi = motif
                    break
            
            radiations.append({
                "id_client": id_client,
                "date_radiation": self.today.strftime("%Y-%m-%d"),
                "motif_radiation": motif_choisi,
                "date_inscription_originale": date_inscription.strftime("%Y-%m-%d"),
                "fic_type": random.choice(self.fic_types),
                "origine_agence": random.choice(self.agences)
            })
        
        return pd.DataFrame(radiations)
    
    def save_to_csv(self, df, filename, output_dir):
        """Sauvegarde un DataFrame en CSV"""
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Fichier sauvé: {output_path} ({len(df)} lignes)")
        return output_path

class AzureUploader:
    """Upload des fichiers vers Azure Data Lake Storage"""
    
    def __init__(self, config):
        self.config = config
        self.storage_account = config.get("azure_storage_account")
        self.container_name = config.get("azure_container", "bronze")
        
        # Authentification via Managed Identity ou Service Principal
        credential = DefaultAzureCredential()
        account_url = f"https://{self.storage_account}.blob.core.windows.net"
        self.blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=credential
        )
        logger.info(f"Connexion Azure Storage: {account_url}")
    
    def upload_file(self, local_path, blob_path):
        """Upload un fichier vers Azure Blob Storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            logger.info(f"Upload réussi: {local_path} → {blob_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur upload {local_path}: {str(e)}")
            return False
    
    def upload_batch(self, files_mapping):
        """Upload multiple files"""
        results = []
        for local_path, blob_path in files_mapping.items():
            result = self.upload_file(local_path, blob_path)
            results.append(result)
        
        success_count = sum(results)
        logger.info(f"Batch upload: {success_count}/{len(results)} fichiers uploadés")
        return success_count == len(results)

def main():
    parser = argparse.ArgumentParser(description="Générateur FICP pour Azure Data Lake")
    parser.add_argument("--volume", type=int, default=300, help="Nombre de clients à générer")
    parser.add_argument("--output-dir", default="/tmp/ficp-output", help="Dossier de sortie local")
    parser.add_argument("--skip-upload", action="store_true", help="Générer sans upload")
    parser.add_argument("--config", default="config.json", help="Fichier de configuration")
    
    args = parser.parse_args()
    
    # Chargement de la configuration
    try:
        if os.path.exists(args.config):
            with open(args.config, 'r') as f:
                config = json.load(f)
        else:
            # Configuration par variables d'environnement
            config = {
                "azure_storage_account": os.getenv("AZURE_STORAGE_ACCOUNT"),
                "azure_container": os.getenv("AZURE_STORAGE_CONTAINER", "bronze"),
                "data_volume": int(os.getenv("DATA_VOLUME", "300"))
            }
    except Exception as e:
        logger.error(f"Erreur configuration: {e}")
        sys.exit(1)
    
    # Vérifications
    if not args.skip_upload and not config.get("azure_storage_account"):
        logger.error("AZURE_STORAGE_ACCOUNT requis pour l'upload")
        sys.exit(1)
    
    try:
        # Génération des données
        logger.info("=== DÉBUT GÉNÉRATION FICP ===")
        generator = FICPGenerator(config)
        
        # Générer les données
        clients = generator.generate_clients(args.volume)
        df_consultations = generator.generate_consultations(clients)
        df_courriers = generator.generate_courriers(clients)
        df_radiations = generator.generate_radiations(args.volume // 6)  # ~50 radiations pour 300 clients
        
        # Sauvegarder localement
        date_str = generator.today.strftime("%Y-%m-%d")
        files_created = {}
        
        files_created["consultations"] = generator.save_to_csv(
            df_consultations, 
            f"ficp_consultation_{date_str}.csv", 
            args.output_dir
        )
        
        files_created["courriers"] = generator.save_to_csv(
            df_courriers, 
            f"ficp_courrier_{date_str}.csv", 
            args.output_dir
        )
        
        files_created["radiations"] = generator.save_to_csv(
            df_radiations, 
            f"ficp_radiation_{date_str}.csv", 
            args.output_dir
        )
        
        # Upload vers Azure (si activé)
        if not args.skip_upload:
            logger.info("=== UPLOAD VERS AZURE ===")
            uploader = AzureUploader(config)
            
            # Mapping local → blob paths
            upload_mapping = {}
            for data_type, local_path in files_created.items():
                blob_path = f"raw/ficp/{data_type}/{date_str}/{local_path.name}"
                upload_mapping[str(local_path)] = blob_path
            
            # Upload batch
            success = uploader.upload_batch(upload_mapping)
            
            if success:
                logger.info("✅ Upload complet réussi")
            else:
                logger.error("❌ Échec partiel de l'upload")
                sys.exit(1)
        
        # Statistiques finales
        logger.info("=== STATISTIQUES ===")
        logger.info(f"Clients générés: {len(clients)}")
        logger.info(f"Consultations: {len(df_consultations)}")
        logger.info(f"Courriers: {len(df_courriers)}")
        logger.info(f"Radiations: {len(df_radiations)}")
        logger.info("=== GÉNÉRATION TERMINÉE ===")
        
    except Exception as e:
        logger.error(f"Erreur fatale: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()