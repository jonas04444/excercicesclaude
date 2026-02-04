from ortools.sat.python import cp_model

# ==================== DONNÉES ====================

voyages_data = [
    # (ligne, num_voyage, arret_debut, arret_fin, heure_debut, heure_fin)
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

services_data = [
    {"id": "S1", "debut": "05:30", "fin": "12:00", "voyages_assignes": [0, 1]},
    {"id": "S2", "debut": "06:00", "fin": "12:30", "voyages_assignes": [2, 3]},
    {"id": "S3", "debut": "06:00", "fin": "12:00", "voyages_assignes": []},
    {"id": "S4", "debut": "06:00", "fin": "12:00", "voyages_assignes": []},
    {"id": "S5", "debut": "06:00", "fin": "12:00", "voyages_assignes": []},
    {"id": "S6", "debut": "06:00", "fin": "12:00", "voyages_assignes": []},
]

pause_min = 5  # Minutes de pause minimum entre deux voyages


# ==================== CLASSE SERVICE POUR LE SOLVER ====================

class ServiceSolver:
    """Wrapper pour service_agent adapté au solver"""

    def __init__(self, id, debut, fin):
        self.id = id
        self.debut = self.time_to_minutes(debut)
        self.fin = self.time_to_minutes(fin)
        self.voyages_assignes = []  # Indices des voyages pré-assignés

    def time_to_minutes(self, heure_str):
        h, m = heure_str.split(':')
        return int(h) * 60 + int(m)

    def minutes_to_time(self, minutes):
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"


# ==================== COLLECTEUR DE SOLUTIONS ====================

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

        solution = {"services": {}}

        for s in range(len(self.services_objets)):
            serv = self.services_objets[s]
            voyages_du_service = []

            for v in range(len(self.voyages_objets)):
                if self.Value(self.x[v, s]) == 1:
                    voy = self.voyages_objets[v]
                    voyages_du_service.append({
                        "index": v,
                        "ligne": voy.num_ligne,  # Adapté pour objet.py
                        "num": voy.num_voyage,  # Adapté pour objet.py
                        "depart": voy.arret_debut,  # Adapté pour objet.py
                        "arrivee": voy.arret_fin,  # Adapté pour objet.py
                        "heure_debut": voy.hdebut,  # Adapté pour objet.py
                        "heure_fin": voy.hfin,  # Adapté pour objet.py
                        "heure_debut_str": voyage.minutes_to_time(voy.hdebut),
                        "heure_fin_str": voyage.minutes_to_time(voy.hfin),
                        "js_srv": voy.js_srv,
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
        return self.solutions


# ==================== FONCTIONS UTILITAIRES ====================

def chevauchement(v1, v2, voyages_objets):
    """Vérifie si deux voyages se chevauchent"""
    return (voyages_objets[v1].hfin + pause_min > voyages_objets[v2].hdebut and
            voyages_objets[v2].hfin + pause_min > voyages_objets[v1].hdebut)


# ==================== CRÉATION DES OBJETS ====================

# Créer les objets voyage depuis objet.py
voyages_objets = []
for v_data in voyages_data:
    ligne, num, arr_deb, arr_fin, h_deb, h_fin = v_data
    voy = voyage(
        num_ligne=ligne,
        num_voyage=num,
        arret_debut=arr_deb,
        arret_fin=arr_fin,
        heure_debut=h_deb,
        heure_fin=h_fin
    )
    voyages_objets.append(voy)

# Créer les objets service
services_objets = []
for s_data in services_data:
    serv = ServiceSolver(s_data["id"], s_data["debut"], s_data["fin"])
    serv.voyages_assignes = s_data["voyages_assignes"]
    services_objets.append(serv)

# ==================== MODÈLE CP-SAT ====================

model = cp_model.CpModel()

# Variables x[v,s] = 1 si voyage v est assigné au service s
x = {}
for v in range(len(voyages_objets)):
    for s in range(len(services_objets)):
        x[v, s] = model.NewBoolVar(f"voyage_{v}_service_{s}")

# Variables de succession y[v1,v2,s] = 1 si v1 précède directement v2 sur le service s
y = {}
for v1 in range(len(voyages_objets)):
    for v2 in range(len(voyages_objets)):
        if v1 != v2:
            # v1 peut précéder v2 si v1 termine avant que v2 commence (avec pause)
            if voyages_objets[v1].hfin + pause_min <= voyages_objets[v2].hdebut:
                for s in range(len(services_objets)):
                    y[v1, v2, s] = model.NewBoolVar(f"succ_{v1}_{v2}_{s}")

# Contrainte 1: Chaque voyage est assigné à exactement un service
for v in range(len(voyages_objets)):
    model.Add(sum(x[v, s] for s in range(len(services_objets))) == 1)

# Contrainte 2: Voyages pré-assignés restent sur leur service
for s in range(len(services_objets)):
    for v in services_objets[s].voyages_assignes:
        model.Add(x[v, s] == 1)

# Contrainte 3: Pas de chevauchement sur le même service
for v1 in range(len(voyages_objets)):
    for v2 in range(v1 + 1, len(voyages_objets)):
        if chevauchement(v1, v2, voyages_objets):
            for s in range(len(services_objets)):
                model.Add(x[v1, s] + x[v2, s] <= 1)

# Contrainte 4: Respect des limites horaires des services
for v in range(len(voyages_objets)):
    for s in range(len(services_objets)):
        voy = voyages_objets[v]
        serv = services_objets[s]
        if voy.hdebut < serv.debut or voy.hfin > serv.fin:
            model.Add(x[v, s] == 0)

# Contrainte 5: Lien entre succession et assignation
for (v1, v2, s) in y:
    model.Add(x[v1, s] == 1).OnlyEnforceIf(y[v1, v2, s])
    model.Add(x[v2, s] == 1).OnlyEnforceIf(y[v1, v2, s])

# Contrainte 6: Au plus un successeur direct par voyage
for v1 in range(len(voyages_objets)):
    for s in range(len(services_objets)):
        successeurs = [y[v1, v2, s] for v2 in range(len(voyages_objets)) if (v1, v2, s) in y]
        if successeurs:
            model.Add(sum(successeurs) <= 1).OnlyEnforceIf(x[v1, s])

# Contrainte 7: Au plus un prédécesseur direct par voyage
for v2 in range(len(voyages_objets)):
    for s in range(len(services_objets)):
        predecesseurs = [y[v1, v2, s] for v1 in range(len(voyages_objets)) if (v1, v2, s) in y]
        if predecesseurs:
            model.Add(sum(predecesseurs) <= 1).OnlyEnforceIf(x[v2, s])

# Contrainte 8: Continuité géographique (3 premiers caractères)
for (v1, v2, s) in y:
    # Utiliser arret_fin_id() et arret_debut_id() de objet.py
    geo_ok = voyages_objets[v1].arret_fin_id() == voyages_objets[v2].arret_debut_id()
    if not geo_ok:
        model.Add(y[v1, v2, s] == 0)

# Contrainte 9: Si deux voyages sont sur le même service et peuvent se suivre,
# l'un doit être le successeur de l'autre (ou il y a un voyage entre)
for v1 in range(len(voyages_objets)):
    for v2 in range(len(voyages_objets)):
        if v1 != v2 and (v1, v2, 0) in y:
            for s in range(len(services_objets)):
                both_on_s = model.NewBoolVar(f"both_{v1}_{v2}_{s}")
                model.Add(x[v1, s] + x[v2, s] == 2).OnlyEnforceIf(both_on_s)
                model.Add(x[v1, s] + x[v2, s] < 2).OnlyEnforceIf(both_on_s.Not())

                intermediaires = [y[v1, vi, s] for vi in range(len(voyages_objets))
                                  if (v1, vi, s) in y and vi != v2 and
                                  voyages_objets[vi].hfin + pause_min <= voyages_objets[v2].hdebut]

                if (v1, v2, s) in y:
                    model.Add(y[v1, v2, s] + sum(intermediaires) >= 1).OnlyEnforceIf(both_on_s)

# ==================== RÉSOLUTION ====================

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

# ==================== AFFICHAGE TKINTER ====================

import tkinter as tk
from tkinter import ttk


def afficher_solutions(solutions):
    root = tk.Tk()
    root.title("Solutions d'attribution")
    root.geometry("900x700")

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
    text_area = tk.Text(root, width=100, height=35, font=("Consolas", 10))
    text_area.pack(pady=10, padx=10)

    def afficher_solution(event=None):
        text_area.delete(1.0, tk.END)
        idx = combo.current()
        solution = solutions[idx]

        for service_id, service_data in solution["services"].items():
            voyages_list = service_data["voyages"]
            text_area.insert(tk.END,
                             f"\n{'=' * 60}\n")
            text_area.insert(tk.END,
                             f"=== Service {service_id} ({service_data['debut']} - {service_data['fin']}) ===\n")
            text_area.insert(tk.END,
                             f"    {len(voyages_list)} voyage(s)\n")
            text_area.insert(tk.END,
                             f"{'=' * 60}\n\n")

            if voyages_list:
                prev_voyage = None
                for voy in voyages_list:
                    tag = "🔒 FIXE  " if voy["fixe"] else "✨ AJOUTÉ"

                    # Vérifier continuité géo
                    geo_warning = ""
                    if prev_voyage:
                        if prev_voyage["arrivee"][:3] != voy["depart"][:3]:
                            geo_warning = " ⚠️ RUPTURE GÉO"

                    text_area.insert(tk.END,
                                     f"  {tag} | {voy['ligne']}-{voy['num']:>2} | "
                                     f"{voy['heure_debut_str']}-{voy['heure_fin_str']} | "
                                     f"{voy['depart']} → {voy['arrivee']}{geo_warning}\n")
                    prev_voyage = voy
            else:
                text_area.insert(tk.END, "  (aucun voyage)\n")

    combo.bind("<<ComboboxSelected>>", afficher_solution)
    afficher_solution()

    root.mainloop()


# Appel après la résolution
solutions = collector.get_solutions()
if solutions:
    afficher_solutions(solutions)