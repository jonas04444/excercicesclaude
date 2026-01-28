"""**Partie 1 — Structure :**
1. Crée la classe `Voyage` avec tous les attributs nécessaires
2. Crée la liste d'objets `Voyage`

**Partie 2 — Contraintes de base :**
3. Chaque voyage affecté à **exactement 1 service**
4. Pas de chevauchement temporel (avec 10 min de pause)

**Partie 3 — Continuité géographique :**
5. Si deux voyages se suivent **directement** sur un service, l'arrivée du premier doit être égale au départ du suivant

**Partie 4 — Optimisation :**
6. Minimiser le nombre de services utilisés

---

## Résultat attendu (exemple)
```
Nombre de services utilisés : 3

=== Service 1 ===
  L1-1: DEPOT → CENTRE (06:00 - 06:30)
  L1-2: CENTRE → GARE (06:45 - 07:15)
  L1-3: GARE → DEPOT (07:30 - 08:00)

=== Service 2 ===
  L2-1: DEPOT → NORD (06:15 - 06:45)
  L2-2: NORD → CENTRE (07:00 - 07:30)
  L2-3: CENTRE → DEPOT (07:45 - 08:15)

=== Service 3 ===
  L3-1: DEPOT → SUD (06:30 - 07:00)
  L3-2: SUD → GARE (07:15 - 07:45)
  L3-3: GARE → DEPOT (08:00 - 08:30)"""



from ortools.sat.python import cp_model

model = cp_model.CpModel()

voyages = [
    # (ligne, numero, depart, arrivee, heure_debut, heure_fin)
    ("L1", 1, "DEPOT", "CENTRE", "06:00", "06:30"),
    ("L1", 2, "CENTRE", "GARE", "06:45", "07:15"),
    ("L1", 3, "GARE", "DEPOT", "07:30", "08:00"),

    ("L2", 1, "DEPOT", "NORD", "06:15", "06:45"),
    ("L2", 2, "NORD", "CENTRE", "07:00", "07:30"),
    ("L2", 3, "CENTRE", "DEPOT", "07:45", "08:15"),

    ("L3", 1, "DEPOT", "SUD", "06:30", "07:00"),
    ("L3", 2, "SUD", "GARE", "07:15", "07:45"),
    ("L3", 3, "GARE", "DEPOT", "08:00", "08:30"),
]

nb_services = 3
pause_min = 10

class Voyage:
    def __init__(self,ligne, numero, depart, arrivee, heure_debut, heure_fin):
        self.ligne = ligne
        self.numero = numero
        self.depart = depart
        self.arrivee = arrivee
        self.heure_debut = self.time_to_minutes(heure_debut)
        self.heure_fin = self.time_to_minutes(heure_fin)

    def time_to_minutes(self, heure_str):
        h, m = heure_str.split(':')
        return int(h) * 60 + int(m)

    def minutes_to_time(self, minutes):
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

objet_voyages = []

for voyage in voyages:
    objet_voyages.append(Voyage(*voyage))