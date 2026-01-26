"""---
## Ta mission

**Partie 1 — Créer la classe Voyage :**

1. Crée une classe `Voyage` avec les attributs : `ligne`, `numero`, `depart`, `arrivee`, `heure_debut`, `heure_fin`

2. Ajoute une méthode `convertir_en_minutes(heure_str)` qui transforme `"04:30"` en `270`

3. Ajoute une méthode `__repr__` pour afficher proprement un voyage

**Partie 2 — Créer les objets :**

4. Transforme la liste de tuples en liste d'objets `Voyage`

**Partie 3 — Adapter le solver :**

5. Adapte les fonctions `conflit()` et `continuite_geo()` pour utiliser les objets

6. Adapte l'affichage pour montrer les infos complètes

---

## Résultat attendu (exemple)
```
=== Service 0 ===
  C00A1-2: CEN18 → GOGAR (04:30 - 04:48)
  C00A1-3: GOGAR → CEN05 (05:30 - 05:51)

=== Service 1 ===
  C00A1-4: CEN18 → GOGAR (05:00 - 05:18)
  C00A1-5: GOGAR → CEN05 (06:00 - 06:21)
  ...

=== Service 2 ===
  C0068-5: JUMA2 → CEN05 (16:30 - 17:02)
"""

from ortools.sat.python import cp_model

model = cp_model.CpModel()

class Voyage:
    def __init__(self,ligne, num_voyage, depart, arrivee, heure_debut, heure_fin):
        self.ligne = ligne
        self.num_voyage = num_voyage
        self.depart = depart
        self.arrivee = arrivee
        self.heure_debut = self.convertir_en_minute(heure_debut)
        self.heure_fin = self.convertir_en_minute(heure_fin)

    def convertir_en_minute(self, heure_str):
        h, m = heure_str.split(':')
        return int(h) * 60 + int(m)

    def __repr__(self):
        return f"Voyage({self.ligne}, {self.num_voyage}: {self.depart} -> {self.arrivee}, {self.heure_debut}, {self.heure_fin})"

voyages = [
    Voyage("C00A1", 2, "CEN18", "GOGAR", "04:30", "04:48"),
    Voyage("C00A1", 3, "GOGAR", "CEN05", "05:30", "05:51"),
    Voyage("C00A1", 4, "CEN18", "GOGAR", "05:00", "05:18"),
    Voyage("C00A1", 5, "GOGAR", "CEN05", "06:00", "06:21"),
    Voyage("C00A1", 6, "CEN18", "GOGAR", "05:30", "05:48"),
    Voyage("C00A1", 7, "GOGAR", "CEN05", "06:30", "06:51"),
    Voyage("C00A1", 8, "CEN18", "GOGAR", "06:00", "06:18"),
    Voyage("C00A1", 9, "GOGAR", "CEN05", "07:00", "07:21"),
]

nb_services = 2
pause_min = 5

def se_chevauchent(v1,v2):
    return voyages[v1].heure_fin + pause_min > voyages[v2].heure_debut and \
           voyages[v2].heure_fin + pause_min > voyages[v1].heure_debut

def continuite_geo(v1,v2):
    return voyages[v2].depart[:3] == voyages[v1].arrivee[:3]

y = {}
for v1 in range(len(voyages)):
    for v2 in range(len(voyages)):
        if v1 != v2:
            # v1 peut précéder v2 dans le temps ?
            if voyages[v1].heure_fin + pause_min <= voyages[v2].heure_debut:
                for s in range(nb_services):
                    y[v1, v2, s] = model.NewBoolVar(f"succ_{v1}_{v2}_{s}")

x = {}
for v in range(len(voyages)):
    for s in range(nb_services):
        x[v, s] = model.NewBoolVar(f"voyage_{v}_service_{s}")

for v in range(len(voyages)):
    model.Add(sum(x[v, s] for s in range(nb_services)) == 1)

for v1 in range(len(voyages)):
    for v2 in range(v1 + 1, len(voyages)):
        if se_chevauchent(v1, v2):
            for s in range(nb_services):
                model.Add(x[v1, s] + x[v2, s] <= 1)

for v1 in range(len(voyages)):
    for v2 in range(len(voyages)):
        if v1 != v2:
            # v1 peut DIRECTEMENT précéder v2 ?
            if voyages[v1].heure_fin + pause_min <= voyages[v2].heure_debut:
                # Mais PAS de continuité géo → interdit
                if not continuite_geo(v1, v2):
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
                print(f"  Voyage {v}: {voyage.depart} → {voyage.arrivee} ({voyage.heure_debut}min - {voyage.heure_fin}min)")
# Après la boucle de contrainte géographique, ajoute :
print("Contraintes géo ajoutées :")
for v1 in range(len(voyages)):
    for v2 in range(len(voyages)):
        if v1 != v2:
            if voyages[v1].heure_fin + pause_min <= voyages[v2].heure_debut:
                if not continuite_geo(v1, v2):
                    print(f"  v{v1} ({voyages[v1].arrivee}) et v{v2} ({voyages[v2].depart}) incompatibles")