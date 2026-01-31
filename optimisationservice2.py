voyages = [
    # Voyages pré-assignés à S1
    ("63", 1, "JUMA1", "FOMET", "06:00", "06:30"),
    ("63", 2, "FOMET", "JUMA2", "06:45", "07:15"),

    # Voyage pré-assigné à S2
    ("63", 3, "JUMA1", "FOMET", "06:15", "06:45"),

    # Voyages à affecter (trouver le bon service)
    ("63", 4, "FOMET", "JUMA2", "07:30", "08:00"),
    ("63", 5, "JUMA1", "FOMET", "07:00", "07:30"),
    ("63", 6, "FOMET", "JUMA2", "07:45", "08:15"),
    ("63", 7, "JUMA1", "FOMET", "06:30", "07:00"),
    ("63", 8, "FOMET", "JUMA2", "07:15", "07:45"),
    ("63", 9, "JUMA1", "FOMET", "08:00", "08:30"),
    ("63", 10, "FOMET", "JUMA2", "06:45", "07:15"),
    ("63", 11, "JUMA1", "FOMET", "07:00", "07:30"),
]

services = [
    {"id": "S1", "debut": "05:30", "fin": "12:00", "voyages_assignes": [0, 1]},
    {"id": "S2", "debut": "06:00", "fin": "12:30", "voyages_assignes": [2]},
    {"id": "S3", "debut": "06:00", "fin": "12:00", "voyages_assignes": [6]},
    {"id": "S4", "debut": "06:00", "fin": "12:00", "voyages_assignes": [9]},
    {"id": "S5", "debut": "06:00", "fin": "12:00", "voyages_assignes": []}
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

"""for v1 in range(len(voyages_objets)):
    for v2 in range(len(voyages_objets)):
        if v1 != v2:
            temps_ok = voyages_objets[v1].h_fin + pause_min <= voyages_objets[v2].h_debut
            geo_ok = voyages_objets[v1].fin[:3] == voyages_objets[v2].debut[:3]  # arrivée_v1 == départ_v2
            if temps_ok and not geo_ok:
                for s in range(len(services_objets)):
                    model.Add(x[v1, s] + x[v2, s] <= 1)"""

# Ajoute avant le solver
print("=== Voyages qui se chevauchent ===")
for v1 in range(len(voyages_objets)):
    for v2 in range(v1 + 1, len(voyages_objets)):
        if chevauchement(v1, v2):
            voy1 = voyages_objets[v1]
            voy2 = voyages_objets[v2]
            print(f"  v{v1} ({voy1.h_debut}-{voy1.h_fin}) ↔ v{v2} ({voy2.h_debut}-{voy2.h_fin})")

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