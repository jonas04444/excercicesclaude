
"""```
**Ta mission :**

1. Chaque livraison doit être affectée à **exactement 1 livreur**

2. Pas de conflit temporel (chevauchement + pause de 10 min)

3. **Nouvelle contrainte - Continuité géographique :** Si deux livraisons se suivent sur le même livreur, l'arrivée de la première doit correspondre au départ de la suivante

4. **Objectif :** Minimiser le nombre de livreurs utilisés

**Résultat attendu (exemple) :**
```
=== Livreur 0 ===
  Livraison 0: Entrepôt → Client_A (8h00 - 9h00)
  Livraison 1: Client_A → Client_B (9h10 - 10h20)
  Livraison 3: Client_B → Entrepôt (10h30 - 11h40)

=== Livreur 1 ===
  Livraison 2: Entrepôt → Client_C (8h20 - 9h40)
  Livraison 4: Client_C → Client_D (10h00 - 11h00)
  Livraison 5: Client_D → Entrepôt (11h10 - 12h00)
  """

from ortools.sat.python import cp_model

model = cp_model.CpModel()
nb_livreurs = 2
PAUSE_MIN = 10
livraisons = [
    {"id": 0, "depart": "Entrepôt", "arrivee": "Client_A", "debut": 480, "fin": 540},    # 8h-9h
    {"id": 1, "depart": "Client_A", "arrivee": "Client_B", "debut": 550, "fin": 620},    # 9h10-10h20
    {"id": 2, "depart": "Entrepôt", "arrivee": "Client_C", "debut": 500, "fin": 580},    # 8h20-9h40
    {"id": 3, "depart": "Client_B", "arrivee": "Entrepôt", "debut": 630, "fin": 700},    # 10h30-11h40
    {"id": 4, "depart": "Client_C", "arrivee": "Client_D", "debut": 600, "fin": 660},    # 10h-11h
    {"id": 5, "depart": "Client_D", "arrivee": "Entrepôt", "debut": 670, "fin": 720},    # 11h10-12h
]

def conflit (v1,v2):
    return livraisons[v1]["fin"] + PAUSE_MIN > livraisons[v2]["debut"] and \
           livraisons[v2]["fin"] + PAUSE_MIN > livraisons[v1]["debut"]

def contraintegeographique (v1,v2):
    return livraisons[v1]["arrivee"] == livraisons[v2]["depart"]

x = {}

for v in range(len(livraisons)):
    for s in range(nb_livreurs):
        x[v, s] = model.NewBoolVar(f"livraison_{v}_livreur_{s}")

for v in range(len(livraisons)):
    model.Add(sum(x[v, s] for s in range(nb_livreurs)) == 1)

for v1 in range(len(livraisons)):
    for v2 in range(v1+1, len(livraisons)):
        if conflit(v1, v2):
            for s in range(nb_livreurs):
                model.Add(x[v1,s] + x[v2,s] <=1)


solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    for s in range(nb_livreurs):
        print(f"\n livraison_{s}")
        for v in range(len(livraisons)):
            if solver.Value(x[v,s]) == 1:
                livraison = livraisons[v]
                print (f" voyage {v} : {livraison['depart']} : {livraison['arrivee']} ")