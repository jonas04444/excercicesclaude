from newversion.solverv2 import generer_solution_gloutonne
from objet import *
import logging
logging.basicConfig(level=logging.DEBUG)

def optimiser_services(voyages_list, services_list, max_solutions=6, pause_min=5):

    if not voyages_list or not services_list:
        return logging.error("voyages_list or services_list not valid")

    solutions = []

    strategies = [
        ("Par heure de début", lambda v:v['voyage'].hdebut),
        ("Par durée", lambda v:v['voyage'].hfin - v['voyage'].hdebut),
        ("Par heure de fin", lambda v:v['voyage'].hfin),
        ("Par ligne puis heure",lambda v: (v['voyage'].num_ligne,v['voyage'].hdebut)),
        ("Ordre inversé", lambda v:-v['voyage'].hdebut),
        ("Nombre de voyages", lambda v: len(v['voyages']))
    ]

    for strat_idx, (strat_nom, strat_tri) in enumerate(strategies[:max_solutions]):

        print(f"\n Génération solution {strat_idx + 1} ({strat_nom})")

        solution =generer_solution_gloutonne (
            voyages_list,
            services_list,
            strat_tri,
            strat_nom,
            pause_min
        )

        if solution:
            solutions.append(solution)

    print(f"\n{len(solutions)} solutions trouvée")
    return solutions