"""
Module d'optimisation des services de transport.
Utilise un algorithme glouton pour assigner des voyages à des services.
"""

from objetv2 import voyage
from logger import get_logger

# Logger pour ce module
logger = get_logger(__name__)


# =============================================================================
# STRATÉGIES DE TRI
# =============================================================================

STRATEGIES_TRI = [
    ("Par heure de début", lambda v: v['voyage'].hdebut),
    ("Par durée", lambda v: v['voyage'].hfin - v['voyage'].hdebut),
    ("Par heure de fin", lambda v: v['voyage'].hfin),
    ("Par ligne puis heure", lambda v: (v['voyage'].num_ligne, v['voyage'].hdebut)),
    ("Ordre inversé", lambda v: -v['voyage'].hdebut),
]


# =============================================================================
# PRÉPARATION DES DONNÉES
# =============================================================================

def preparer_services(services_list):
    """Transforme la liste de services en structure exploitable."""
    logger.debug(f"Préparation de {len(services_list)} services")

    services_info = []

    for idx, (service, indices_assignes) in enumerate(services_list):
        services_info.append({
            'id': idx,
            'service_original': service,
            'debut': service.heure_debut,
            'fin': service.heure_fin,
            'voyages_assignes': list(indices_assignes),
            'voyages': []
        })

    return services_info


def preparer_voyages(voyages_list):
    """Transforme la liste de voyages en structure exploitable."""
    logger.debug(f"Préparation de {len(voyages_list)} voyages")

    return [
        {'index': idx, 'voyage': voy, 'assigne': False}
        for idx, voy in enumerate(voyages_list)
    ]


def preassigner_voyages_fixes(services_info, voyages_info):
    """Assigne les voyages déjà fixés à leurs services respectifs."""
    nb_preassignes = 0

    for serv in services_info:
        for v_idx in serv['voyages_assignes']:
            if v_idx < len(voyages_info):
                voy_info = voyages_info[v_idx]
                serv['voyages'].append({
                    'index': v_idx,
                    'voyage_obj': voy_info['voyage'],
                    'fixe': True
                })
                voy_info['assigne'] = True
                nb_preassignes += 1
            else:
                logger.warning(f"Index voyage invalide: {v_idx} (max: {len(voyages_info) - 1})")

    logger.debug(f"{nb_preassignes} voyages pré-assignés")


def trier_voyages_non_assignes(voyages_info, tri_func):
    """Filtre et trie les voyages non encore assignés."""
    voyages_non_assignes = [v for v in voyages_info if not v['assigne']]

    try:
        voyages_non_assignes.sort(key=tri_func)
    except Exception as e:
        logger.warning(f"Erreur tri personnalisé, fallback sur hdebut: {e}")
        voyages_non_assignes.sort(key=lambda v: v['voyage'].hdebut)

    logger.debug(f"{len(voyages_non_assignes)} voyages à assigner")
    return voyages_non_assignes


# =============================================================================
# VÉRIFICATIONS DE COMPATIBILITÉ
# =============================================================================

def est_dans_plage_horaire(voyage_obj, service_info):
    """Vérifie si un voyage est dans la plage horaire du service."""
    return (voyage_obj.hdebut >= service_info['debut'] and
            voyage_obj.hfin <= service_info['fin'])


def est_pendant_pause(voyage_obj, service_info):
    """Vérifie si un voyage tombe pendant une pause du service."""
    service_original = service_info['service_original']

    try:
        if hasattr(service_original, 'pauses'):
            return service_original.est_dans_pause(voyage_obj.hdebut, voyage_obj.hfin)
    except Exception as e:
        logger.error(f"Erreur vérification pause: {e}")

    return False


def a_chevauchement(voyage_obj, voyages_existants, pause_min):
    """Vérifie si un voyage chevauche des voyages existants."""
    for v_existant in voyages_existants:
        v_exist = v_existant['voyage_obj']

        fin_nouveau_avec_pause = voyage_obj.hfin + pause_min
        fin_existant_avec_pause = v_exist.hfin + pause_min

        pas_de_chevauchement = (fin_nouveau_avec_pause <= v_exist.hdebut or
                                voyage_obj.hdebut >= fin_existant_avec_pause)

        if not pas_de_chevauchement:
            return True

    return False


def est_service_compatible(voyage_obj, service_info, pause_min):
    """Vérifie toutes les conditions de compatibilité."""
    if not est_dans_plage_horaire(voyage_obj, service_info):
        return False

    if est_pendant_pause(voyage_obj, service_info):
        return False

    if a_chevauchement(voyage_obj, service_info['voyages'], pause_min):
        return False

    return True


# =============================================================================
# CALCUL DU SCORE D'ASSIGNATION
# =============================================================================

def calculer_bonus_continuite_avant(voyage_obj, voyages_service, pause_min):
    """Calcule le bonus de continuité avec le voyage précédent."""
    voyages_avant = [
        v for v in voyages_service
        if v['voyage_obj'].hfin + pause_min <= voyage_obj.hdebut
    ]

    if not voyages_avant:
        return 10

    score = 0
    dernier = max(voyages_avant, key=lambda v: v['voyage_obj'].hfin)

    try:
        arret_fin = str(dernier['voyage_obj'].arret_fin_id())[:3]
        arret_debut = str(voyage_obj.arret_debut_id())[:3]
        if arret_fin == arret_debut:
            score += 100
    except Exception as e:
        logger.debug(f"Impossible de vérifier continuité avant: {e}")

    temps_attente = voyage_obj.hdebut - dernier['voyage_obj'].hfin
    score += max(0, 50 - temps_attente)

    return score


def calculer_bonus_continuite_apres(voyage_obj, voyages_service, pause_min):
    """Calcule le bonus de continuité avec le voyage suivant."""
    voyages_apres = [
        v for v in voyages_service
        if voyage_obj.hfin + pause_min <= v['voyage_obj'].hdebut
    ]

    if not voyages_apres:
        return 0

    prochain = min(voyages_apres, key=lambda v: v['voyage_obj'].hdebut)

    try:
        if voyage_obj.arret_fin_id() == prochain['voyage_obj'].arret_debut_id():
            return 100
    except Exception as e:
        logger.debug(f"Impossible de vérifier continuité après: {e}")

    return 0


def calculer_score_assignation(voyage_obj, service_info, pause_min):
    """Calcule le score total pour assigner un voyage à un service."""
    voyages_service = service_info['voyages']

    score = 0
    score += calculer_bonus_continuite_avant(voyage_obj, voyages_service, pause_min)
    score += calculer_bonus_continuite_apres(voyage_obj, voyages_service, pause_min)
    score -= len(voyages_service) * 5

    return score


# =============================================================================
# ALGORITHME GLOUTON
# =============================================================================

def trouver_meilleur_service(voyage_obj, services_info, pause_min):
    """Trouve le meilleur service pour un voyage donné."""
    meilleur_service = None
    meilleur_score = -1

    for service_info in services_info:
        if not est_service_compatible(voyage_obj, service_info, pause_min):
            continue

        score = calculer_score_assignation(voyage_obj, service_info, pause_min)

        if score > meilleur_score:
            meilleur_score = score
            meilleur_service = service_info

    return meilleur_service


def assigner_voyage(voy_info, service_info):
    """Assigne un voyage à un service."""
    service_info['voyages'].append({
        'index': voy_info['index'],
        'voyage_obj': voy_info['voyage'],
        'fixe': False
    })
    voy_info['assigne'] = True

    logger.debug(f"Voyage {voy_info['index']} → service {service_info['id']}")


def executer_algorithme_glouton(voyages_non_assignes, services_info, pause_min):
    """Exécute l'algorithme glouton pour assigner les voyages."""
    nb_non_assignes = 0

    for voy_info in voyages_non_assignes:
        voyage_obj = voy_info['voyage']

        try:
            meilleur_service = trouver_meilleur_service(voyage_obj, services_info, pause_min)

            if meilleur_service:
                assigner_voyage(voy_info, meilleur_service)
            else:
                nb_non_assignes += 1
                logger.debug(f"Voyage {voy_info['index']} non assignable")

        except Exception as e:
            nb_non_assignes += 1
            logger.error(f"Erreur assignation voyage {voy_info['index']}: {e}", exc_info=True)

    return nb_non_assignes


# =============================================================================
# CONSTRUCTION DE LA SOLUTION
# =============================================================================

def trier_voyages_par_service(services_info):
    """Trie les voyages de chaque service par heure de début."""
    for serv in services_info:
        serv['voyages'].sort(key=lambda v: v['voyage_obj'].hdebut)


def construire_solution(services_info, nom_strategie, nb_non_assignes):
    """Construit l'objet solution final."""
    solution = {
        "services": {},
        "strategie": nom_strategie,
        "nb_non_assignes": nb_non_assignes
    }

    for serv in services_info:
        solution["services"][serv['id']] = serv['voyages']

    return solution


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def generer_solution_gloutonne(voyages_list, services_list, tri_func, nom_strategie, pause_min=5):
    """Génère UNE solution avec une stratégie de tri donnée."""
    logger.info(f"Génération solution: {nom_strategie}")

    try:
        services_info = preparer_services(services_list)
        voyages_info = preparer_voyages(voyages_list)
        preassigner_voyages_fixes(services_info, voyages_info)
        voyages_non_assignes = trier_voyages_non_assignes(voyages_info, tri_func)

        nb_non_assignes = executer_algorithme_glouton(
            voyages_non_assignes, services_info, pause_min
        )

        trier_voyages_par_service(services_info)
        solution = construire_solution(services_info, nom_strategie, nb_non_assignes)

        total_assignes = sum(len(serv['voyages']) for serv in services_info)
        logger.info(f"Résultat: {total_assignes}/{len(voyages_list)} assignés ({nb_non_assignes} échecs)")

        return solution

    except Exception as e:
        logger.critical(f"Échec génération solution '{nom_strategie}': {e}", exc_info=True)
        return None


def optimiser_services(voyages_list, services_list, max_solutions=5, pause_min=5):
    """
    Algorithme glouton générant plusieurs solutions.

    Args:
        voyages_list: Liste des voyages à optimiser
        services_list: Liste des services disponibles
        max_solutions: Nombre maximum de solutions à générer
        pause_min: Temps minimum entre deux voyages (en minutes)

    Returns:
        Liste des solutions générées
    """
    logger.info("=" * 60)
    logger.info("DÉBUT OPTIMISATION")
    logger.info(f"Paramètres: pause_min={pause_min}, max_solutions={max_solutions}")
    logger.info(f"Données: {len(voyages_list)} voyages, {len(services_list)} services")

    if not voyages_list or not services_list:
        logger.error("Données manquantes: pas de voyages ou services")
        return []

    solutions = []

    for strat_idx, (strat_nom, strat_tri) in enumerate(STRATEGIES_TRI[:max_solutions]):
        logger.info(f"--- Solution {strat_idx + 1}/{max_solutions} ---")

        solution = generer_solution_gloutonne(
            voyages_list, services_list, strat_tri, strat_nom, pause_min
        )

        if solution:
            solutions.append(solution)
        else:
            logger.warning(f"Solution {strat_idx + 1} non générée")

    logger.info("=" * 60)
    logger.info(f"FIN OPTIMISATION: {len(solutions)} solution(s) générée(s)")

    return solutions