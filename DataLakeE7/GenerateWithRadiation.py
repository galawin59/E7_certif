import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker
import os
import glob

faker = Faker('fr_FR')
today = datetime.today().date()
date_str = today.strftime("%Y-%m-%d")

# Options
agences = ["SOF", "CA", "LCL"]
fic_types = ["FIC1", "FIC2", "FIC3", "FIC4"]
canaux = ["Agence", "Web", "Téléphone"]
motifs_radiation = {
    "remboursement": 0.70,    # 70% - remboursement total
    "echeance": 0.25,         # 25% - échéance 5 ans
    "deces": 0.03,            # 3% - décès
    "erreur": 0.02            # 2% - erreur administrative
}

def lire_inscriptions_historiques():
    """Lit toutes les inscriptions des fichiers CSV historiques"""
    inscriptions = []
    
    # Lire tous les fichiers courrier existants
    pattern = os.path.join("ficp_data", "ficp_courrier_*.csv")
    fichiers_courrier = glob.glob(pattern)
    
    for fichier in fichiers_courrier:
        try:
            df = pd.read_csv(fichier)
            # Filtrer uniquement les inscriptions
            inscriptions_jour = df[df['type_courrier'] == 'inscription'].copy()
            
            if not inscriptions_jour.empty:
                # Ajouter la date d'inscription à partir du nom du fichier
                date_fichier = fichier.split('_')[-1].replace('.csv', '')
                inscriptions_jour['date_inscription_fichier'] = date_fichier
                inscriptions.append(inscriptions_jour)
                
        except Exception as e:
            print(f"⚠️ Erreur lecture {fichier}: {e}")
    
    if inscriptions:
        return pd.concat(inscriptions, ignore_index=True)
    else:
        return pd.DataFrame()

def generer_radiations_coherentes():
    """Génère des radiations basées sur les inscriptions historiques"""
    print("📖 Lecture des inscriptions historiques...")
    inscriptions_historiques = lire_inscriptions_historiques()
    
    if inscriptions_historiques.empty:
        print("⚠️ Aucune inscription historique trouvée")
        return pd.DataFrame()
    
    print(f"📊 {len(inscriptions_historiques)} inscriptions trouvées")
    
    radiations = []
    
    for _, inscription in inscriptions_historiques.iterrows():
        # Date d'inscription (soit du fichier, soit de la colonne)
        date_inscription_str = inscription.get('date_envoi_inscription') or inscription.get('date_inscription_fichier')
        
        if pd.isna(date_inscription_str) or date_inscription_str == '':
            continue
            
        try:
            date_inscription = datetime.strptime(str(date_inscription_str), "%Y-%m-%d").date()
        except:
            continue
        
        # Calculer si cette inscription est éligible à radiation
        jours_depuis_inscription = (today - date_inscription).days
        
        # Radiations possibles après 30 jours minimum (pour simulation)
        if jours_depuis_inscription < 30:
            continue
            
        # Probabilité de radiation selon l'ancienneté (ajustée pour simulation)
        if jours_depuis_inscription < 90:   # < 3 mois
            prob_radiation = 0.10  # 10% de chance
        elif jours_depuis_inscription < 180:  # 3-6 mois
            prob_radiation = 0.25  # 25% de chance
        else:  # > 6 mois
            prob_radiation = 0.40  # 40% de chance
            
        # Décider si on génère une radiation
        if random.random() > prob_radiation:
            continue
            
        # Choisir le motif de radiation selon les probabilités
        rand = random.random()
        cumul = 0
        motif_choisi = "remboursement"  # par défaut
        
        for motif, prob in motifs_radiation.items():
            cumul += prob
            if rand <= cumul:
                motif_choisi = motif
                break
        
        # Calculer la date de radiation selon le motif (ajusté pour simulation)
        if motif_choisi == "remboursement":
            # Remboursement : entre 30 jours et l'ancienneté actuelle
            jours_max_radiation = min(jours_depuis_inscription - 15, 365)  # max 1 an pour simulation
            jours_radiation = random.randint(30, max(30, jours_max_radiation))
            
        elif motif_choisi == "echeance":
            # Échéance : pour simulation, on simule 1 an au lieu de 5 ans
            jours_radiation = min(365, jours_depuis_inscription - 15)
            
        elif motif_choisi == "deces":
            # Décès : aléatoire dans la période
            jours_radiation = random.randint(30, jours_depuis_inscription)
            
        else:  # erreur
            # Erreur administrative : rapidement après inscription
            jours_radiation = random.randint(15, 60)
        
        date_radiation = date_inscription + timedelta(days=jours_radiation)
        
        # Ne pas générer de radiations futures
        if date_radiation > today:
            continue
            
        radiations.append({
            "id_client": inscription['id_client'],
            "date_radiation": date_radiation.strftime("%Y-%m-%d"),
            "motif_radiation": motif_choisi,
            "date_inscription_originale": date_inscription.strftime("%Y-%m-%d"),
            "fic_type": inscription['fic_type'],
            "origine_agence": inscription['origine_agence']
        })
    
    return pd.DataFrame(radiations)

# Générer 1000 nouveaux clients (logique existante)
print("👥 Génération de nouveaux clients...")
clients = []
for _ in range(1000):
    date_naissance = faker.date_of_birth(minimum_age=18, maximum_age=60)
    nom = faker.last_name().upper()
    id_client = date_naissance.strftime("%d%m%y") + nom[:5]
    clients.append((id_client, date_naissance.strftime("%d%m%Y"), nom))

# ---------- CONSULTATIONS ----------
print("🔍 Génération des consultations...")
consultations = []
for id_client, _, _ in clients:
    consultations.append({
        "id_client": id_client,
        "date_consultation": date_str,
        "origine_agence": random.choice(agences),
        "canal": random.choice(canaux)
    })

df_consult = pd.DataFrame(consultations)
df_consult.to_csv(f"ficp_consultation_{date_str}.csv", index=False)

# ---------- COURRIERS ----------
print("📮 Génération des courriers...")
courriers = []
for id_client, _, _ in clients:
    # Surveillance (obligatoire)
    date_surv = today - timedelta(days=random.randint(30, 45))
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
df_courriers.to_csv(f"ficp_courrier_{date_str}.csv", index=False)

# ---------- RADIATIONS ----------
print("🗂️ Génération des radiations...")
df_radiations = generer_radiations_coherentes()

if not df_radiations.empty:
    df_radiations.to_csv(f"ficp_radiation_{date_str}.csv", index=False)
    print(f"✅ {len(df_radiations)} radiations générées")
else:
    print("⚠️ Aucune radiation générée")

print(f"✅ Fichiers générés :")
print(f"- ficp_consultation_{date_str}.csv ({len(df_consult)} consultations)")
print(f"- ficp_courrier_{date_str}.csv ({len(df_courriers)} courriers)")
if not df_radiations.empty:
    print(f"- ficp_radiation_{date_str}.csv ({len(df_radiations)} radiations)")