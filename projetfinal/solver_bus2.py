from objet import voyage
import random


def optimiser_services(voyages_list, services_list, max_solutions=5, pause_min=5, verbose = True):  # ✅ Ajouter pause_min
    """
    Algorithme glouton générant plusieurs solutions
    SANS OR-Tools (stable et rapide)
    """
    if verbose:
        print(f"🔧 Début optimisation glouton (pause_min = {pause_min} min)")
        print(f"   Voyages: {len(voyages_list)}")
        print(f"   Services: {len(services_list)}")

    if not voyages_list or not services_list:
        if verbose:
            print("❌ Pas de voyages ou services")
        return []

    solutions = []

    # Générer plusieurs solutions avec différentes stratégies
    strategies = [
        ("Par heure de début", lambda v: v['voyage'].hdebut),
        ("Par durée", lambda v: v['voyage'].hfin - v['voyage'].hdebut),
        ("Par heure de fin", lambda v: v['voyage'].hfin),
        ("Par ligne puis heure", lambda v: (v['voyage'].num_ligne, v['voyage'].hdebut)),
        ("Ordre inversé", lambda v: -v['voyage'].hdebut),
    ]

    for strat_idx, (strat_nom, strat_tri) in enumerate(strategies[:max_solutions]):
        if verbose:
            print(f"\n🎯 Génération solution {strat_idx + 1} ({strat_nom})...")

        solution = generer_solution_gloutonne(
            voyages_list,
            services_list,
            strat_tri,
            strat_nom,
            pause_min  # ✅ Passer pause_min
        )

        if solution:
            solutions.append(solution)
    if verbose:
        print(f"\n✅ {len(solutions)} solution(s) générée(s)")
    return solutions


def generer_solution_gloutonne(voyages_list, services_list, tri_func, nom_strategie, pause_min=5):
    """
    Génère UNE solution avec une stratégie de tri donnée
    """

    # Extraire les services
    services_info = []
    for idx, (service, indices_assignes) in enumerate(services_list):
        services_info.append({
            'id': idx,
            'debut': service.heure_debut,
            'fin': service.heure_fin,
            'voyages_assignes': list(indices_assignes),
            'voyages': []
        })

    # Créer liste des voyages
    voyages_avec_index = []
    for idx, voy in enumerate(voyages_list):
        voyages_avec_index.append({
            'index': idx,
            'voyage': voy,
            'assigne': False
        })

    # Pré-assigner les voyages fixés
    for serv_info in services_info:
        for v_idx in serv_info['voyages_assignes']:
            if v_idx < len(voyages_avec_index):
                voy_info = voyages_avec_index[v_idx]
                serv_info['voyages'].append({
                    'index': v_idx,
                    'voyage_obj': voy_info['voyage'],
                    'fixe': True
                })
                voy_info['assigne'] = True

    # Trier les voyages non assignés selon la stratégie
    voyages_non_assignes = [v for v in voyages_avec_index if not v['assigne']]
    try:
        voyages_non_assignes.sort(key=tri_func)
    except:
        voyages_non_assignes.sort(key=lambda v: v['voyage'].hdebut)

    # Algorithme glouton
    nb_non_assignes = 0
    for voy_info in voyages_non_assignes:
        voy = voy_info['voyage']
        v_idx = voy_info['index']

        # Chercher le meilleur service
        meilleur_service = None
        meilleur_score = -1

        for serv_info in services_info:
            # Vérifier limites horaires
            if voy.hdebut < serv_info['debut'] or voy.hfin > serv_info['fin']:
                continue
            service_original = services_list[serv_info['id']][0]
            if hasattr(service_original, 'pauses') and service_original.est_dans_pause(voy.hdebut, voy.hfin):
                continue

            # Vérifier chevauchements
            compatible = True
            for v_existant in serv_info['voyages']:
                v_exist = v_existant['voyage_obj']

                # ✅ Utiliser pause_min au lieu de PAUSE_MIN
                if not (voy.hfin + pause_min <= v_exist.hdebut or
                        voy.hdebut >= v_exist.hfin + pause_min):
                    compatible = False
                    break

            if not compatible:
                continue

            # Calculer score (préférer services avec continuité géo)
            score = 0

            # Voyages avant - ✅ Utiliser pause_min
            voyages_avant = [v for v in serv_info['voyages']
                             if v['voyage_obj'].hfin + pause_min <= voy.hdebut]

            if voyages_avant:
                dernier = max(voyages_avant, key=lambda v: v['voyage_obj'].hfin)
                try:
                    if dernier['voyage_obj'].arret_fin_id() == voy.arret_debut_id():
                        score += 100  # Bonus continuité
                except:
                    pass

                # Bonus proximité temporelle
                temps_attente = voy.hdebut - dernier['voyage_obj'].hfin
                score += max(0, 50 - temps_attente)
            else:
                score += 10  # Premier voyage du service

            # Voyages après - ✅ Utiliser pause_min
            voyages_apres = [v for v in serv_info['voyages']
                             if voy.hfin + pause_min <= v['voyage_obj'].hdebut]

            if voyages_apres:
                prochain = min(voyages_apres, key=lambda v: v['voyage_obj'].hdebut)
                try:
                    if voy.arret_fin_id() == prochain['voyage_obj'].arret_debut_id():
                        score += 100  # Bonus continuité
                except:
                    pass

            # Pénalité si le service a déjà beaucoup de voyages
            score -= len(serv_info['voyages']) * 5

            if score > meilleur_score:
                meilleur_score = score
                meilleur_service = serv_info

        # Assigner au meilleur service
        if meilleur_service:
            meilleur_service['voyages'].append({
                'index': v_idx,
                'voyage_obj': voy,
                'fixe': False
            })
            voy_info['assigne'] = True
        else:
            nb_non_assignes += 1

    # Trier les voyages de chaque service
    for serv_info in services_info:
        serv_info['voyages'].sort(key=lambda v: v['voyage_obj'].hdebut)

    # Créer la solution
    solution = {
        "services": {},
        "strategie": nom_strategie,
        "nb_non_assignes": nb_non_assignes
    }

    for serv_info in services_info:
        solution["services"][serv_info['id']] = serv_info['voyages']

    total_assignes = sum(len(s['voyages']) for s in services_info)
    print(f"   Assignés: {total_assignes}/{len(voyages_list)} ({nb_non_assignes} non assignés)")

    return solution