import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker

faker = Faker('fr_FR')  # version française
today = datetime.today().date()
date_str = today.strftime("%Y-%m-%d")

# Options
agences = ["SOF", "CA", "LCL"]
fic_types = ["FIC1", "FIC2", "FIC3", "FIC4"]
canaux = ["Agence", "Web", "Téléphone"]

# Générer 10 clients fictifs
clients = []
for _ in range(1000):
    date_naissance = faker.date_of_birth(minimum_age=18, maximum_age=60)
    nom = faker.last_name().upper()
    id_client = date_naissance.strftime("%d%m%y") + nom[:5]
    clients.append((id_client, date_naissance.strftime("%d%m%Y"), nom))

# ---------- CONSULTATIONS ----------
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

print(f"✅ Fichiers générés :\n- ficp_consultation_{date_str}.csv\n- ficp_courrier_{date_str}.csv")
