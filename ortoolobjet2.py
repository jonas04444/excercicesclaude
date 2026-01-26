"""**Ta mission :**

1. Crée une classe `Reunion` avec : `departement`, `numero`, `heure_debut`, `heure_fin`

2. Chaque réunion doit être affectée à **exactement 1 salle**

3. Pas de chevauchement temporel dans une même salle (avec 10 min de pause)

4. **Nouvelle contrainte simple :** Les réunions d'un même département doivent être dans la **même salle**

**Résultat attendu (exemple) :**
```
=== Salle 0 ===
  Marketing-1: 09:00 - 10:00
  Marketing-2: 10:15 - 11:30

=== Salle 1 ===
  Tech-1: 09:30 - 10:30
  Tech-2: 11:00 - 12:00

=== Salle 2 ===
  RH-1: 09:00 - 09:45
  RH-2: 10:00 - 11:00
  Finance-1: 10:30 - 11:30
  Finance-2: 13:00 - 14:00"""

from ortools.sat.python import cp_model

model = cp_model.CpModel()

reunions = [
    ("Marketing", 1, "09:00", "10:00"),
    ("Marketing", 2, "10:15", "11:30"),
    ("Tech", 1, "09:30", "10:30"),
    ("Tech", 2, "11:00", "12:00"),
    ("RH", 1, "09:00", "09:45"),
    ("RH", 2, "10:00", "11:00"),
    ("Finance", 1, "10:30", "11:30"),
    ("Finance", 2, "13:00", "14:00"),
]

nb_salles = 3
pause_min = 10

class Reunion:
    def __init__(self, departement, numero, heure_debut, heure_fin):
        self.departement = departement
        self.numero = numero
        self.heure_debut = self.time_to_minutes(heure_debut)
        self.heure_fin = self.time_to_minutes(heure_fin)

    def time_to_minutes(self, heure_str):
        h, m = heure_str.split(':')
        return int(h) * 60 + int(m)

    def minutes_to_time(self, minutes):
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

def chevauchement(r1,r2):
    return reunions_obj[r1].heure_fin +pause_min > reunions_obj[r2].heure_debut and \
           reunions_obj[r2].heure_fin +pause_min > reunions_obj[r1].heure_debut

reunions_obj = []

for r in reunions:
    reunions_obj.append(Reunion(*r))

salle_reunions= {}
for v in range(len(reunions_obj)):
    for s in range(nb_salles):
        salle_reunions[v,s] = model.NewBoolVar(f"salle_reunions_{v}_{s}")

solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    for s in range(nb_salles):
        print(f"Salut {s}")
        for v in range(len(reunions_obj)):
            if solver.Value(salle_reunions[v,s]) == 1:
                meeting = reunions_obj[v]
                print(f"{meeting.departement} - {meeting.numero}")