import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker
import os
import glob

faker = Faker('fr_FR')
agences = ["SOF", "CA", "LCL"]
fic_types = ["FIC1", "FIC2", "FIC3", "FIC4"]
canaux = ["Agence", "Web", "Téléphone"]
motifs_radiation = {
    "remboursement": 0.70,    # 70% - remboursement total
    "echeance": 0.25,         # 25% - échéance 5 ans
    "deces": 0.03,            # 3% - décès
    "erreur": 0.02            # 2% - erreur administrative
}

# 📁 Créer dossier de sortie local
output_folder = "ficp_data"
os.makedirs(output_folder, exist_ok=True)

def lire_inscriptions_anterieures_a(date_limite):
    """Lit toutes les inscriptions antérieures à une date donnée"""
    inscriptions = []
    
    # Lire tous les fichiers courrier existants
    pattern = os.path.join(output_folder, "ficp_courrier_*.csv")
    fichiers_courrier = glob.glob(pattern)
    
    for fichier in fichiers_courrier:
        try:
            # Extraire la date du nom du fichier
            date_fichier_str = fichier.split('_')[-1].replace('.csv', '')
            date_fichier = datetime.strptime(date_fichier_str, "%Y-%m-%d").date()
            
            # Ne lire que les fichiers antérieurs à la date limite
            if date_fichier >= date_limite:
                continue
                
            df = pd.read_csv(fichier)
            # Filtrer uniquement les inscriptions
            inscriptions_jour = df[df['type_courrier'] == 'inscription'].copy()
            
            if not inscriptions_jour.empty:
                inscriptions_jour['date_inscription_fichier'] = date_fichier_str
                inscriptions.append(inscriptions_jour)
                
        except Exception as e:
            print(f"⚠️ Erreur lecture {fichier}: {e}")
    
    if inscriptions:
        return pd.concat(inscriptions, ignore_index=True)
    else:
        return pd.DataFrame()

def generer_radiations_pour_date(date_courante):
    """Génère des radiations pour une date donnée"""
    inscriptions_historiques = lire_inscriptions_anterieures_a(date_courante)
    
    if inscriptions_historiques.empty:
        return pd.DataFrame()
    
    radiations = []
    
    for _, inscription in inscriptions_historiques.iterrows():
        date_inscription_str = inscription.get('date_envoi_inscription') or inscription.get('date_inscription_fichier')
        
        if pd.isna(date_inscription_str) or date_inscription_str == '':
            continue
            
        try:
            date_inscription = datetime.strptime(str(date_inscription_str), "%Y-%m-%d").date()
        except:
            continue
        
        jours_depuis_inscription = (date_courante - date_inscription).days
        
        # Radiations possibles après 30 jours minimum
        if jours_depuis_inscription < 30:
            continue
            
        # Probabilité de radiation selon l'ancienneté
        if jours_depuis_inscription < 90:
            prob_radiation = 0.02  # 2% par jour (plus faible pour éviter trop de radiations)
        elif jours_depuis_inscription < 180:
            prob_radiation = 0.05  # 5% par jour
        else:
            prob_radiation = 0.08  # 8% par jour
            
        if random.random() > prob_radiation:
            continue
            
        # Choisir le motif
        rand = random.random()
        cumul = 0
        motif_choisi = "remboursement"
        
        for motif, prob in motifs_radiation.items():
            cumul += prob
            if rand <= cumul:
                motif_choisi = motif
                break
        
        # Date de radiation = date courante (pour ce jour précis)
        radiations.append({
            "id_client": inscription['id_client'],
            "date_radiation": date_courante.strftime("%Y-%m-%d"),
            "motif_radiation": motif_choisi,
            "date_inscription_originale": date_inscription.strftime("%Y-%m-%d"),
            "fic_type": inscription['fic_type'],
            "origine_agence": inscription['origine_agence']
        })
    
    return pd.DataFrame(radiations)

# 🔁 Générer données pour les 30 derniers jours
nb_jours = 30
for i in range(nb_jours):
    jour = datetime.today().date() - timedelta(days=i)
    date_str = jour.strftime("%Y-%m-%d")

    # Générer 1000 clients par jour
    clients = []
    for _ in range(1000):
        date_naissance = faker.date_of_birth(minimum_age=18, maximum_age=60)
        nom = faker.last_name().upper()
        id_client = date_naissance.strftime("%d%m%y") + nom[:5]
        clients.append((id_client, date_naissance.strftime("%d%m%Y"), nom))

    # -------- CONSULTATIONS --------
    consultations = []
    for id_client, _, _ in clients:
        consultations.append({
            "id_client": id_client,
            "date_consultation": date_str,
            "origine_agence": random.choice(agences),
            "canal": random.choice(canaux)
        })
    df_consult = pd.DataFrame(consultations)
    df_consult.to_csv(os.path.join(output_folder, f"ficp_consultation_{date_str}.csv"), index=False)

    # -------- COURRIERS --------
    courriers = []
    for id_client, _, _ in clients:
        # Surveillance (obligatoire)
        date_surv = jour - timedelta(days=random.randint(30, 45))
        courriers.append({
            "id_client": id_client,
            "date_envoi_surveillance": date_surv.strftime("%Y-%m-%d"),
            "date_envoi_inscription": "",
            "type_courrier": "surveillance",
            "fic_type": random.choice(fic_types),
            "origine_agence": random.choice(agences)
        })

        # Inscription (50% des cas)
        if random.random() < 0.5:
            date_insc = date_surv + timedelta(days=random.randint(31, 37))
            courriers.append({
                "id_client": id_client,
                "date_envoi_surveillance": "",
                "date_envoi_inscription": date_insc.strftime("%Y-%m-%d"),
                "type_courrier": "inscription",
                "fic_type": random.choice(fic_types),
                "origine_agence": random.choice(agences)
            })

    df_courriers = pd.DataFrame(courriers)
    df_courriers.to_csv(os.path.join(output_folder, f"ficp_courrier_{date_str}.csv"), index=False)

    # -------- RADIATIONS --------
    df_radiations = generer_radiations_pour_date(jour)
    
    if not df_radiations.empty:
        df_radiations.to_csv(os.path.join(output_folder, f"ficp_radiation_{date_str}.csv"), index=False)
        print(f"📅 {date_str}: {len(df_consult)} consultations, {len(df_courriers)} courriers, {len(df_radiations)} radiations")
    else:
        print(f"📅 {date_str}: {len(df_consult)} consultations, {len(df_courriers)} courriers, 0 radiations")

print(f"✅ Génération terminée : {nb_jours} jours de fichiers créés dans '{output_folder}/')")