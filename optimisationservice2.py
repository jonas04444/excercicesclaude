voyages = [
    # Voyages pré-assignés à S1
    ("63", 1, "JUMA1", "FOMET", "06:00", "06:30"),
    ("63", 2, "FOMET", "JUMA2", "06:45", "07:15"),

    # Voyage pré-assigné à S2
    ("63", 3, "JUMA1", "FOMET", "06:15", "06:45"),

    # Voyages à affecter (trouver le bon service)
    ("63", 4, "FOMET", "JUMA2", "07:00", "07:30"),
    ("63", 5, "JUMA1", "FOMET", "06:30", "07:00"),
    ("63", 6, "FOMET", "JUMA2", "07:15", "07:45"),
    ("63", 7, "JUMA1", "FOMET", "06:45", "07:15"),
    ("63", 8, "FOMET", "JUMA2", "07:30", "08:00"),
    ("63", 9, "JUMA1", "FOMET", "07:00", "07:30"),
    ("63", 10, "FOMET", "JUMA2", "07:45", "08:15"),
    ("63", 11, "JUMA1", "FOMET", "07:15", "07:45"),
    ("63", 12, "FOMET", "JUMA2", "08:00", "08:30"),
    ("63", 13, "JUMA1", "FOMET", "09:30", "10:00"),
]

services = [
    {"id": "S1", "debut": "05:30", "fin": "12:00", "voyages_assignes": [0,1]},
    {"id": "S2", "debut": "06:00", "fin": "12:30", "voyages_assignes": [2,3]},
    {"id": "S3", "debut": "06:00", "fin": "12:00", "voyages_assignes": []},
    {"id": "S4", "debut": "06:00", "fin": "12:00", "voyages_assignes": []},
    {"id": "S5", "debut": "06:00", "fin": "12:00", "voyages_assignes": []},
    {"id": "S6", "debut": "06:00", "fin": "12:00", "voyages_assignes": []},
    #{"id": "S7", "debut": "06:00", "fin": "12:00", "voyages_assignes": []}
]
from ortools.sat.python import cp_model

model = cp_model.CpModel()

pause_min = 5


class SolutionCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, x, voyages_objets, services_objets, max_solutions=5):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.x = x
        self.voyages_objets = voyages_objets
        self.services_objets = services_objets
        self.solutions = []
        self.max_solutions = max_solutions

    def on_solution_callback(self):
        if len(self.solutions) >= self.max_solutions:
            self.StopSearch()
            return

        # Structure plus complète pour Tkinter
        solution = {
            "services": {}
        }

        for s in range(len(self.services_objets)):
            serv = self.services_objets[s]
            voyages_du_service = []

            for v in range(len(self.voyages_objets)):
                if self.Value(self.x[v, s]) == 1:
                    voy = self.voyages_objets[v]
                    voyages_du_service.append({
                        "index": v,
                        "ligne": voy.ligne,
                        "num": voy.num,
                        "depart": voy.debut,
                        "arrivee": voy.fin,
                        "heure_debut": voy.h_debut,
                        "heure_fin": voy.h_fin,
                        "heure_debut_str": voy.minutes_to_time(voy.h_debut),
                        "heure_fin_str": voy.minutes_to_time(voy.h_fin),
                        "fixe": v in serv.voyages_assignes
                    })

            # Trier par heure de début
            voyages_du_service.sort(key=lambda x: x["heure_debut"])

            solution["services"][serv.id] = {
                "id": serv.id,
                "debut": serv.minutes_to_time(serv.debut),
                "fin": serv.minutes_to_time(serv.fin),
                "voyages": voyages_du_service
            }

        self.solutions.append(solution)

    def get_solutions(self):
        """Retourne les solutions pour Tkinter"""
        return self.solutions

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

y = {}
for v1 in range(len(voyages_objets)):
    for v2 in range(len(voyages_objets)):
        if v1 != v2:
            if voyages_objets[v1].h_fin + pause_min <= voyages_objets[v2].h_debut:
                for s in range(len(services_objets)):
                    y[v1, v2, s] = model.NewBoolVar(f"succ_{v1}_{v2}_{s}")

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

for (v1, v2, s) in y:
    model.Add(x[v1, s] == 1).OnlyEnforceIf(y[v1, v2, s])
    model.Add(x[v2, s] == 1).OnlyEnforceIf(y[v1, v2, s])

for v1 in range(len(voyages_objets)):
    for s in range(len(services_objets)):
        successeurs = [y[v1, v2, s] for v2 in range(len(voyages_objets)) if (v1, v2, s) in y]
        if successeurs:
            model.Add(sum(successeurs) <= 1).OnlyEnforceIf(x[v1, s])

# 6. Chaque voyage a AU PLUS UN prédécesseur direct sur un service
for v2 in range(len(voyages_objets)):
    for s in range(len(services_objets)):
        predecesseurs = [y[v1, v2, s] for v1 in range(len(voyages_objets)) if (v1, v2, s) in y]
        if predecesseurs:
            model.Add(sum(predecesseurs) <= 1).OnlyEnforceIf(x[v2, s])

# 7. Continuité géographique : interdit les successions sans continuité
for (v1, v2, s) in y:
    geo_ok = voyages_objets[v1].fin[:3] == voyages_objets[v2].debut[:3]
    if not geo_ok:
        model.Add(y[v1, v2, s] == 0)

# 8. Si deux voyages sont sur le même service et peuvent se suivre,
#    l'un doit être le successeur de l'autre (ou il y a un voyage entre)
for v1 in range(len(voyages_objets)):
    for v2 in range(len(voyages_objets)):
        if v1 != v2 and (v1, v2, 0) in y:  # Si v1 peut précéder v2
            for s in range(len(services_objets)):
                # Si v1 et v2 sont sur le même service...
                both_on_s = model.NewBoolVar(f"both_{v1}_{v2}_{s}")
                model.Add(x[v1, s] + x[v2, s] == 2).OnlyEnforceIf(both_on_s)
                model.Add(x[v1, s] + x[v2, s] < 2).OnlyEnforceIf(both_on_s.Not())

                # ...alors soit v1→v2 directement, soit il y a un intermédiaire
                intermediaires = [y[v1, vi, s] for vi in range(len(voyages_objets))
                                  if (v1, vi, s) in y and vi != v2 and
                                  voyages_objets[vi].h_fin + pause_min <= voyages_objets[v2].h_debut]

                if (v1, v2, s) in y:
                    # v1 est suivi de v2 OU v1 est suivi d'un intermédiaire
                    model.Add(y[v1, v2, s] + sum(intermediaires) >= 1).OnlyEnforceIf(both_on_s)

# Ajoute avant le solver
"""print("=== Voyages qui se chevauchent ===")
for v1 in range(len(voyages_objets)):
    for v2 in range(v1 + 1, len(voyages_objets)):
        if chevauchement(v1, v2):
            voy1 = voyages_objets[v1]
            voy2 = voyages_objets[v2]
            print(f"  v{v1} ({voy1.h_debut}-{voy1.h_fin}) ↔ v{v2} ({voy2.h_debut}-{voy2.h_fin})")"""

collector = SolutionCollector(x, voyages_objets, services_objets, max_solutions=10)

solver = cp_model.CpSolver()
solver.parameters.enumerate_all_solutions = True
status = solver.Solve(model, collector)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print(f"\n🎉 {len(collector.solutions)} solution(s) trouvée(s) !")
elif status == cp_model.INFEASIBLE:
    print("❌ Pas de solution possible")
else:
    print(f"Status: {status}")

import tkinter as tk
from tkinter import ttk


def afficher_solutions(solutions):
    root = tk.Tk()
    root.title("Solutions d'attribution")
    root.geometry("800x600")

    # Combobox pour choisir la solution
    frame_top = tk.Frame(root)
    frame_top.pack(pady=10)

    tk.Label(frame_top, text="Choisir une solution :").pack(side=tk.LEFT)

    solution_var = tk.StringVar()
    combo = ttk.Combobox(frame_top, textvariable=solution_var,
                         values=[f"Solution {i + 1}" for i in range(len(solutions))])
    combo.pack(side=tk.LEFT, padx=10)
    combo.current(0)

    # Zone d'affichage
    text_area = tk.Text(root, width=90, height=30)
    text_area.pack(pady=10, padx=10)

    def afficher_solution(event=None):
        text_area.delete(1.0, tk.END)
        idx = combo.current()
        solution = solutions[idx]

        for service_id, service_data in solution["services"].items():
            if service_data["voyages"]:
                text_area.insert(tk.END,
                                 f"\n=== Service {service_id} ({service_data['debut']} - {service_data['fin']}) ===\n")

                for voyage in service_data["voyages"]:
                    tag = "[FIXE]" if voyage["fixe"] else "[AJOUTÉ]"
                    text_area.insert(tk.END,
                                     f"  {tag} {voyage['ligne']}-{voyage['num']}: {voyage['depart']} → {voyage['arrivee']} ({voyage['heure_debut_str']} - {voyage['heure_fin_str']})\n")

    combo.bind("<<ComboboxSelected>>", afficher_solution)
    afficher_solution()  # Afficher la première solution

    root.mainloop()


# Appel après la résolution
solutions = collector.get_solutions()
afficher_solutions(solutions)