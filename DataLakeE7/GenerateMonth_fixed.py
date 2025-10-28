import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker
import os

faker = Faker('fr_FR')
agences = ["SOF", "CA", "LCL"]
fic_types = ["FIC1", "FIC2", "FIC3", "FIC4"]
canaux = ["Agence", "Web", "Téléphone"]

# 📁 Créer dossier de sortie local
output_folder = "ficp_data"
os.makedirs(output_folder, exist_ok=True)

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

print(f"✅ Génération terminée : {nb_jours} jours de fichiers créés dans '{output_folder}/')")