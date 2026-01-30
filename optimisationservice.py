"""**Partie 1 — Classes :**
1. Crée une classe `Voyage` (comme avant)
2. Crée une classe `Service` avec : `id`, `heure_debut`, `heure_fin`, `voyages_assignes`

**Partie 2 — Contraintes :**
3. Les voyages pré-assignés restent sur leur service (contrainte fixe)
4. Les autres voyages doivent être affectés à **exactement 1 service**
5. Pas de chevauchement temporel sur un même service
6. Un voyage doit être dans la **plage horaire** de son service

**Partie 3 — Bonus :**
7. Continuité géographique (optionnel)
8. Équilibrer la charge entre services (optionnel)"""

"""=== Service S1 (05:30 - 10:00) ===
  [FIXE] L1-1: DEPOT → CENTRE (06:00 - 06:30)
  [FIXE] L1-2: CENTRE → GARE (06:45 - 07:15)
  [AJOUTÉ] L1-3: GARE → DEPOT (07:30 - 08:00)

=== Service S2 (06:00 - 10:30) ===
  [FIXE] L2-1: DEPOT → NORD (06:15 - 06:45)
  [AJOUTÉ] L2-2: NORD → CENTRE (07:00 - 07:30)
  [AJOUTÉ] L2-3: CENTRE → DEPOT (07:45 - 08:15)

=== Service S3 (06:00 - 11:00) ===
  [AJOUTÉ] L3-1: DEPOT → SUD (06:30 - 07:00)
  [AJOUTÉ] L3-2: SUD → GARE (07:15 - 07:45)
  [AJOUTÉ] L3-3: GARE → DEPOT (08:00 - 08:30)"""

services = [
    {"id": "S1", "debut": "05:30", "fin": "10:00", "voyages_assignes": [0, 1]},
    {"id": "S2", "debut": "06:00", "fin": "10:30", "voyages_assignes": [2]},
    {"id": "S3", "debut": "06:00", "fin": "11:00", "voyages_assignes": []},
]

# Tous les voyages (certains déjà assignés, d'autres à placer)
voyages = [
    # Voyages pré-assignés à S1
    ("L1", 1, "DEPOT", "CENTRE", "06:00", "06:30"),  # v0 → S1
    ("L1", 2, "CENTRE", "GARE", "06:45", "07:15"),  # v1 → S1

    # Voyage pré-assigné à S2
    ("L2", 1, "DEPOT", "NORD", "06:15", "06:45"),  # v3 → S2

    # Voyages à affecter (trouver le bon service)
    ("L1", 3, "GARE", "DEPOT", "07:30", "08:00"),  # v2 → ?
    ("L2", 2, "NORD", "CENTRE", "07:00", "07:30"),  # v4 → ?
    ("L2", 3, "CENTRE", "DEPOT", "07:45", "08:15"),  # v5 → ?
    ("L3", 1, "DEPOT", "SUD", "06:30", "07:00"),  # v6 → ?
    ("L3", 2, "SUD", "GARE", "07:15", "07:45"),  # v7 → ?
    ("L3", 3, "GARE", "DEPOT", "08:00", "08:30"),  # v8 → ?
]

from ortools.sat.python import cp_model

model = cp_model.CpModel()

pause_min = 5

class Service:
    def __init__(self, id, debut, fin):
        self.id = id
        self.debut = self.time_to_minutes(debut)
        self.fin = self.time_to_minutes(fin)
        self.voyages_assignes = []

    def time_to_minutes(self, heure_str):
        h, m = heure_str.split(':')
        return int(h) * 60 + int(m)

    def minutes_to_time(self, minutes):
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

class Voyage:
    def __init__(self, ligne, num, debut, fin, h_debut, h_fin):
        self.ligne = ligne
        self.num = num
        self.debut = debut
        self.fin = fin
        self.h_debut = self.time_to_minutes(h_debut)
        self.h_fin = self.time_to_minutes(h_fin)

    def time_to_minutes(self, heure_str):
        h, m = heure_str.split(':')
        return int(h) * 60 + int(m)

    def minutes_to_time(self, minutes):
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

def chevauchement(v1, v2):
    return voyages_objets[v1].h_fin + pause_min > voyages_objets[v2].h_debut and \
           voyages_objets[v2].h_fin + pause_min > voyages_objets[v1].h_debut

voyages_objets = []

for voyage in voyages:
    voyages_objets.append(Voyage(*voyage))

services_objets = []
for s in services:
    serv = Service(s["id"], s["debut"], s["fin"])
    serv.voyages_assignes = s["voyages_assignes"]
    services_objets.append(serv)

x = {}
for v in range(len(voyages_objets)):
    for s in range(len(services_objets)):
        x[v, s] = model.NewBoolVar(f"voyage_{v}_service_{s}")

for v in range(len(voyages_objets)):
    model.Add(sum(x[v, s] for s in range(len(services_objets))) == 1)

for s in range(len(services_objets)):
    for v in services_objets[s].voyages_assignes:
        model.Add(x[v, s] == 1)

for v1 in range(len(voyages_objets)):
    for v2 in range(v1 + 1, len(voyages_objets)):
        if chevauchement(v1, v2):
            for s in range(len(services_objets)):
                model.Add(x[v1, s] + x[v2, s] <= 1)

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    for s in range(len(services_objets)):
        serv = services_objets[s]
        print(f"\n=== Service {serv.id} ({serv.minutes_to_time(serv.debut)} - {serv.minutes_to_time(serv.fin)}) ===")
        for v in range(len(voyages_objets)):
            if solver.Value(x[v, s]) == 1:
                voy = voyages_objets[v]
                debut = voy.minutes_to_time(voy.h_debut)
                fin = voy.minutes_to_time(voy.h_fin)

                # Marquer si pré-assigné ou ajouté
                if v in serv.voyages_assignes:
                    tag = "[FIXE]"
                else:
                    tag = "[AJOUTÉ]"

                print(f"  {tag} {voy.ligne}-{voy.num}: {voy.debut} → {voy.fin} ({debut} - {fin})")

elif status == cp_model.INFEASIBLE:
    print("❌ Pas de solution possible")
else:
    print(f"Status: {status}")