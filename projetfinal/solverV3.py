from newversion.solverv2 import generer_solution_gloutonne
from objet import *
import logging
logging.basicConfig(level=logging.DEBUG)

def optimiser_services(voyages_list, services_list, max_solutions=6, pause_min=5, verbose=True):

    if verbose:
        print(f"🔧 Début optimisation glouton (pause_min = {pause_min} min)")
        print(f"   Voyages: {len(voyages_list)}")
        print(f"   Services: {len(services_list)}")

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
        if verbose:
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
    if verbose:
        print(f"\n{len(solutions)} solutions trouvée")
    return solutions

def generer_solutio_gloutonne(voyages_list, services_list, tri_func, nom_strategie, pause_min=5, verbose=True):

    services_info = []
    for idx, (service, indices_assignes) in enumerate(services_list):
        services_info.append({
            'idx': idx,
            'debut': service.heure_debut,
            'fin': service.heure_fin,
            'voyages_assignes': list(indices_assignes),
            'voyages':[]
        })

    voyages_avec_index = []
    for idx, voy in enumerate(voyages_list):
        voyages_avec_index.append({
            'index': idx,
            'voyage': voy,
            'assignes': False
        })

    for serv_info in services_info:
        for v_idx in serv_info['voyages_assignes']:
            if v_idx < len(voyages_avec_index):
                voy_info = voyages_avec_index[v_idx]
                serv_info['voyages'].append({
                    'index': v_idx,
                    'voyage_obj': voy_info['voyage'],
                    'fixe': True
                })
                voy_info['assignes'] = True

    voyages_non_assignes = [v for v in voyages_avec_index if not v['assignes']]
    try:
        voyages_non_assignes.sort(key=tri_func)
    except:
        voyages_non_assignes.sort(key=lambda v: v['voyage'].hdebut)

    nb_non_assignes = 0
    for voy_info in voyages_non_assignes:
        voy = voy_info['voyage']
        v_idx = voy_info['index']

        meilleure_service = None
        meilleur_score = -1

        for serv_info in services_info:
            if voy.hdebut < serv_info['debut'] or voy.hfin > serv_info['fin']:
                continue
            service_original = services_list[serv_info['idx']][0]
            if hasattr(service_original, 'pauses') and service_original.est_dans_pause(voy.hdebut, voy.hfin):
                continue

            compatible = True
            for v_existant in serv_info['voyages']:
                v_exist = v_existant['voyage_obj']

                if not (voy.hfin + pause_min <= v_exist.hdebut or
                        voy.hdebut >= v_exist.hfin + pause_min):
                    compatible = False
                    break

                #calcul du score
                score = 0

                voyages_avant = [v for v in serv_info['voyages']
                                 if v ['voyage_obj'].hfin + pause_min <= voy.hdebut]

                if voyages_avant:
                    dernier = max(voyages_avant, key=lambda v: v['voyage_obj'].hfin)
                    try:
                        if dernier['voyage_obj'].arret_fin_id() == voy.arret_debut_id():
                            score += 100
                    except:
                        pass

                    temps_attente = voy.hdebut - dernier['voyage_obj'].hfin
                    score += max (0, 50 - temps_attente)
                else:
                    score += 10

