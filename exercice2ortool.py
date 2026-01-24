"""```

2. **Contrainte 1** : Chaque voyage doit être affecté à **exactement 1 service**

3. **Contrainte 2** : Pas de chevauchement dans un même service (si deux voyages sont sur le même service, ils ne doivent pas se chevaucher)

**Indice pour le chevauchement :**
Deux voyages se chevauchent si :

debut_A < fin_B  ET  debut_B < fin_A

PAUSE_MIN = 5

def conflit(v1, v2):
    # Retourne True si v1 et v2 ne peuvent pas être sur le même service
    # (chevauchement OU pas assez de pause entre les deux)

```"""
from ortools.sat.python import cp_model

model = cp_model.CpModel()

voyages = [
    {"id": 0, "depart": "Lyon", "arrivee": "Paris", "heure_debut": 480, "heure_fin": 600},      # 8h-10h
    {"id": 1, "depart": "Paris", "arrivee": "Lille", "heure_debut": 540, "heure_fin": 620},     # 9h-10h20
    {"id": 2, "depart": "Paris", "arrivee": "Lyon", "heure_debut": 660, "heure_fin": 780},      # 11h-13h
    {"id": 3, "depart": "Lille", "arrivee": "Paris", "heure_debut": 700, "heure_fin": 780},     # 11h40-13h
    {"id": 4, "depart": "Lyon", "arrivee": "Marseille", "heure_debut": 800, "heure_fin": 900},  # 13h20-15h
]

def se_chevauchent(v1, v2):
    return voyages[v1]["heure_debut"] < voyages[v2]["heure_fin"] and \
           voyages[v2]["heure_debut"] < voyages[v1]["heure_fin"]

PAUSE_MIN = 5

def conflit(v1, v2):
    return voyages[v1]["heure_fin"] + PAUSE_MIN > voyages[v2]["heure_debut"] and \
           voyages[v2]["heure_fin"] + PAUSE_MIN > voyages[v1]["heure_debut"]
nb_services = 2

# x[v, s] = 1 si le voyage v est affecté au service s
x = {}
for v in range(len(voyages)):
    for s in range(nb_services):
        x[v, s] = model.NewBoolVar(f"voyage_{v}_service_{s}")

for v in range(len(voyages)):
    model.Add(sum(x[v, s] for s in range(nb_services)) == 1)

for v1 in range(len(voyages)):
    for v2 in range(v1 + 1, len(voyages)):  # Toutes les paires
        if conflit(v1, v2):
            # Ils ne peuvent pas être ensemble sur le même service
            for s in range(nb_services):
                model.Add(x[v1, s] + x[v2, s] <= 1)

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    for s in range(nb_services):
        print(f"\n=== Service {s} ===")
        for v in range(len(voyages)):
            if solver.Value(x[v, s]) == 1:
                voyage = voyages[v]
                print(f"  Voyage {v}: {voyage['depart']} → {voyage['arrivee']} ({voyage['heure_debut']}min - {voyage['heure_fin']}min)")