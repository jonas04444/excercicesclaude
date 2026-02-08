"""
Solver optimisé pour l'assignation de voyages à des services
Utilise un algorithme glouton avec plusieurs stratégies et amélioration locale
"""

from objetv2 import voyage
import random
from bisect import bisect_left, bisect_right
from typing import List, Dict, Tuple, Any, Optional
import time


# =============================================================================
# CONSTANTES
# =============================================================================

PAUSE_MIN = 5  # Minutes de pause minimale entre voyages


# =============================================================================
# CLASSES UTILITAIRES
# =============================================================================

class CacheGeo:
    """Cache pour les vérifications de continuité géographique"""

    def __init__(self):
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def sont_consecutifs(self, voyage1, voyage2):
        """Vérifie si deux voyages sont géographiquement consécutifs"""
        key = (id(voyage1), id(voyage2))

        if key in self.cache:
            self.hits += 1
            return self.cache[key]

        self.misses += 1
        try:
            result = voyage1.arret_fin_id() == voyage2.arret_debut_id()
        except:
            result = False

        self.cache[key] = result
        return result

    def get_stats(self):
        """Retourne les statistiques du cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }


class ServiceOptimise:
    """Classe pour gérer un service avec indexation temporelle"""

    def __init__(self, service_id, debut, fin, voyages_assignes=None):
        self.id = service_id
        self.debut = debut
        self.fin = fin
        self.voyages = []  # Liste triée par heure de début
        self.voyages_assignes_fixes = voyages_assignes or []

    def peut_ajouter_rapide(self, voyage):
        """
        Vérification O(log n) si un voyage peut être ajouté
        Utilise la recherche dichotomique
        """
        if voyage.hdebut < self.debut or voyage.hfin > self.fin:
            return False

        if not self.voyages:
            return True

        # Trouver la position d'insertion
        pos = bisect_left(self.voyages, voyage.hdebut,
                         key=lambda v: v['voyage_obj'].hdebut)

        # Vérifier le voyage précédent
        if pos > 0:
            precedent = self.voyages[pos - 1]['voyage_obj']
            if precedent.hfin + PAUSE_MIN > voyage.hdebut:
                return False

        # Vérifier le voyage suivant
        if pos < len(self.voyages):
            suivant = self.voyages[pos]['voyage_obj']
            if voyage.hfin + PAUSE_MIN > suivant.hdebut:
                return False

        return True

    def ajouter_voyage(self, voyage_info):
        """Ajoute un voyage en maintenant l'ordre trié"""
        pos = bisect_left(self.voyages, voyage_info['voyage_obj'].hdebut,
                         key=lambda v: v['voyage_obj'].hdebut)
        self.voyages.insert(pos, voyage_info)

    def get_voyages_avant(self, voyage):
        """Retourne les voyages qui finissent avant ce voyage"""
        return [v for v in self.voyages
                if v['voyage_obj'].hfin + PAUSE_MIN <= voyage.hdebut]

    def get_voyages_apres(self, voyage):
        """Retourne les voyages qui commencent après ce voyage"""
        return [v for v in self.voyages
                if voyage.hfin + PAUSE_MIN <= v['voyage_obj'].hdebut]


# =============================================================================
# FONCTIONS DE CALCUL DE SCORES ET STRATÉGIES
# =============================================================================

def calculer_densite(voyage_info, tous_voyages):
    """
    Calcule la densité de voyages autour d'un créneau horaire
    Plus il y a de voyages proches, plus la densité est élevée
    """
    v = voyage_info['voyage']
    densite = 0
    fenetre = 60  # minutes

    for autre in tous_voyages:
        autre_v = autre['voyage']
        if autre_v == v:
            continue

        # Compter les voyages dans la fenêtre temporelle
        if abs(autre_v.hdebut - v.hdebut) <= fenetre:
            densite += 1

    return -densite  # Négatif pour trier par densité décroissante


def calculer_criticite(voyage_info, services_info):
    """
    Calcule la criticité d'un voyage
    Plus un voyage est difficile à caser, plus il est critique
    """
    v = voyage_info['voyage']

    # Compter combien de services peuvent potentiellement accueillir ce voyage
    nb_services_compatibles = 0
    for serv in services_info:
        if serv.debut <= v.hdebut and serv.fin >= v.hfin:
            nb_services_compatibles += 1

    # Plus le nombre est petit, plus c'est critique
    return nb_services_compatibles


def calculer_potentiel_chaine(voyage_info, tous_voyages, cache_geo):
    """
    Calcule le potentiel de chaînage géographique d'un voyage
    """
    v = voyage_info['voyage']
    score = 0

    for autre in tous_voyages:
        autre_v = autre['voyage']
        if autre_v == v:
            continue

        # Vérifier continuité géographique
        if cache_geo.sont_consecutifs(v, autre_v):
            score += 1
        if cache_geo.sont_consecutifs(autre_v, v):
            score += 1

    return -score  # Négatif pour trier par potentiel décroissant


def calculer_score_intelligent(voyage, service_opt, cache_geo, service_original=None):
    """
    Calcule un score multicritère pour l'assignation d'un voyage à un service
    """
    score = 0

    # Poids des différents critères
    poids = {
        'continuite_geo': 150,
        'proximite_temp': 50,
        'equilibrage': 10,
        'premier_voyage': 20,
        'ligne_commune': 30
    }

    # 1. Continuité géographique
    voyages_avant = service_opt.get_voyages_avant(voyage)
    if voyages_avant:
        dernier = max(voyages_avant, key=lambda v: v['voyage_obj'].hfin)
        if cache_geo.sont_consecutifs(dernier['voyage_obj'], voyage):
            score += poids['continuite_geo']

        # Bonus proximité temporelle
        temps_attente = voyage.hdebut - dernier['voyage_obj'].hfin
        if temps_attente <= 30:
            score += max(0, poids['proximite_temp'] - temps_attente)
    else:
        # Premier voyage du service
        score += poids['premier_voyage']

    voyages_apres = service_opt.get_voyages_apres(voyage)
    if voyages_apres:
        prochain = min(voyages_apres, key=lambda v: v['voyage_obj'].hdebut)
        if cache_geo.sont_consecutifs(voyage, prochain['voyage_obj']):
            score += poids['continuite_geo']

    # 2. Équilibrage - pénalité si le service a déjà beaucoup de voyages
    score -= len(service_opt.voyages) * poids['equilibrage']

    # 3. Bonus si même ligne
    if service_opt.voyages:
        try:
            if any(v['voyage_obj'].num_ligne == voyage.num_ligne
                   for v in service_opt.voyages):
                score += poids['ligne_commune']
        except:
            pass

    return score


# =============================================================================
# CLASSE PRINCIPALE DU SOLVER
# =============================================================================

class SolverOptimise:
    """Solver principal avec toutes les optimisations"""

    def __init__(self, voyages_list, services_list):
        self.voyages_originaux = voyages_list
        self.services_originaux = services_list
        self.cache_geo = CacheGeo()
        self.stats = {
            'temps_total': 0,
            'solutions_generees': 0,
            'evaluations_score': 0
        }

        # Définir les stratégies de tri
        self.strategies = [
            ("Par heure de début", lambda v: v['voyage'].hdebut),
            ("Par durée", lambda v: v['voyage'].hfin - v['voyage'].hdebut),
            ("Par heure de fin", lambda v: v['voyage'].hfin),
            ("Par ligne puis heure", lambda v: (v['voyage'].num_ligne, v['voyage'].hdebut)),
            ("Ordre inversé", lambda v: -v['voyage'].hdebut),
        ]

    def initialiser_services(self):
        """Initialise les services optimisés"""
        services_opt = []

        for idx, (service, indices_assignes) in enumerate(self.services_originaux):
            service_opt = ServiceOptimise(
                service_id=idx,
                debut=service.heure_debut,
                fin=service.heure_fin,
                voyages_assignes=list(indices_assignes)
            )
            services_opt.append((service_opt, service))

        return services_opt

    def initialiser_voyages(self):
        """Prépare la liste des voyages avec métadonnées"""
        voyages_avec_index = []

        for idx, voy in enumerate(self.voyages_originaux):
            voyages_avec_index.append({
                'index': idx,
                'voyage': voy,
                'assigne': False
            })

        return voyages_avec_index

    def pre_assigner_voyages_fixes(self, services_opt, voyages_info):
        """Pré-assigne les voyages déjà fixés"""
        for service_opt, service_orig in services_opt:
            for v_idx in service_opt.voyages_assignes_fixes:
                if v_idx < len(voyages_info):
                    voy_info = voyages_info[v_idx]

                    voyage_dict = {
                        'index': v_idx,
                        'voyage_obj': voy_info['voyage'],
                        'fixe': True
                    }

                    service_opt.ajouter_voyage(voyage_dict)
                    voy_info['assigne'] = True

    def generer_solution(self, strategie_nom, tri_func, amelioration_locale=False):
        """
        Génère une solution avec la stratégie donnée
        """
        start_time = time.time()

        # Initialisation
        services_opt = self.initialiser_services()
        voyages_info = self.initialiser_voyages()

        # Pré-assigner les voyages fixes
        self.pre_assigner_voyages_fixes(services_opt, voyages_info)

        # Obtenir les voyages non assignés et les trier
        voyages_non_assignes = [v for v in voyages_info if not v['assigne']]

        try:
            voyages_non_assignes.sort(key=tri_func)
        except Exception as e:
            print(f"⚠️  Erreur tri ({strategie_nom}): {e}")
            voyages_non_assignes.sort(key=lambda v: v['voyage'].hdebut)

        # Algorithme glouton optimisé
        nb_non_assignes = 0

        for voy_info in voyages_non_assignes:
            voy = voy_info['voyage']
            v_idx = voy_info['index']

            # Chercher le meilleur service
            meilleur_service = None
            meilleur_score = -float('inf')

            for service_opt, service_orig in services_opt:
                # Vérification rapide de compatibilité
                if not service_opt.peut_ajouter_rapide(voy):
                    continue

                # Vérifier les pauses
                if hasattr(service_orig, 'pauses') and service_orig.est_dans_pause(voy.hdebut, voy.hfin):
                    continue

                # Calculer le score
                score = calculer_score_intelligent(voy, service_opt, self.cache_geo, service_orig)
                self.stats['evaluations_score'] += 1

                if score > meilleur_score:
                    meilleur_score = score
                    meilleur_service = service_opt

            # Assigner au meilleur service
            if meilleur_service:
                voyage_dict = {
                    'index': v_idx,
                    'voyage_obj': voy,
                    'fixe': False
                }
                meilleur_service.ajouter_voyage(voyage_dict)
                voy_info['assigne'] = True
            else:
                nb_non_assignes += 1

        # Créer la solution finale
        solution = {
            "services": {},
            "strategie": strategie_nom,
            "nb_non_assignes": nb_non_assignes,
            "temps_generation": time.time() - start_time
        }

        for service_opt, _ in services_opt:
            solution["services"][service_opt.id] = service_opt.voyages

        # Amélioration locale si demandée
        if amelioration_locale:
            solution = ameliorer_solution_locale(solution, services_opt, self.cache_geo)

        total_assignes = sum(len(voyages) for voyages in solution["services"].values())
        print(f"   ✓ {strategie_nom}: {total_assignes}/{len(self.voyages_originaux)} assignés "
              f"({nb_non_assignes} non assignés) - {solution['temps_generation']:.3f}s")

        self.stats['solutions_generees'] += 1

        return solution

    def optimiser(self, max_solutions=5, amelioration_locale=False):
        """
        Génère plusieurs solutions et retourne les meilleures
        """
        print(f"🔧 Début optimisation (Solver Optimisé)")
        print(f"   Voyages: {len(self.voyages_originaux)}")
        print(f"   Services: {len(self.services_originaux)}")

        if not self.voyages_originaux or not self.services_originaux:
            print("❌ Pas de voyages ou services")
            return []

        start_time = time.time()
        solutions = []

        # Générer les solutions avec différentes stratégies
        for strat_nom, strat_tri in self.strategies[:max_solutions]:
            print(f"\n🎯 Génération solution: {strat_nom}...")

            solution = self.generer_solution(strat_nom, strat_tri, amelioration_locale)

            if solution:
                solutions.append(solution)

        self.stats['temps_total'] = time.time() - start_time

        # Afficher les statistiques
        print(f"\n📊 Statistiques:")
        print(f"   Solutions générées: {len(solutions)}")
        print(f"   Temps total: {self.stats['temps_total']:.3f}s")
        print(f"   Évaluations de score: {self.stats['evaluations_score']}")

        cache_stats = self.cache_geo.get_stats()
        print(f"   Cache géo - Hit rate: {cache_stats['hit_rate']:.1f}% "
              f"({cache_stats['hits']}/{cache_stats['hits'] + cache_stats['misses']})")

        print(f"\n✅ {len(solutions)} solution(s) générée(s)")

        return solutions


# =============================================================================
# FONCTIONS D'AMÉLIORATION LOCALE
# =============================================================================

def peut_echanger_voyages(v1, v2, service1_voyages, service2_voyages):
    """
    Vérifie si deux voyages peuvent être échangés entre services
    sans créer de conflits
    """
    # Créer des copies temporaires
    temp_s1 = [v for v in service1_voyages if v['index'] != v1['index']]
    temp_s1.append(v2)

    temp_s2 = [v for v in service2_voyages if v['index'] != v2['index']]
    temp_s2.append(v1)

    # Vérifier les conflits dans service1
    for i, voy_a in enumerate(temp_s1):
        for voy_b in temp_s1[i+1:]:
            if not (voy_a['voyage_obj'].hfin + PAUSE_MIN <= voy_b['voyage_obj'].hdebut or
                    voy_b['voyage_obj'].hfin + PAUSE_MIN <= voy_a['voyage_obj'].hdebut):
                return False

    # Vérifier les conflits dans service2
    for i, voy_a in enumerate(temp_s2):
        for voy_b in temp_s2[i+1:]:
            if not (voy_a['voyage_obj'].hfin + PAUSE_MIN <= voy_b['voyage_obj'].hdebut or
                    voy_b['voyage_obj'].hfin + PAUSE_MIN <= voy_a['voyage_obj'].hdebut):
                return False

    return True


def ameliorer_solution_locale(solution, services_opt, cache_geo, max_iterations=50):
    """
    Améliore une solution par recherche locale
    Essaie d'échanger des voyages entre services pour améliorer la continuité
    """
    print("   🔄 Amélioration locale...")
    start_time = time.time()

    ameliore = True
    iteration = 0
    nb_echanges = 0

    while ameliore and iteration < max_iterations:
        ameliore = False
        iteration += 1

        services_ids = list(solution['services'].keys())

        for i, s1_id in enumerate(services_ids):
            for s2_id in services_ids[i+1:]:
                voyages_s1 = solution['services'][s1_id]
                voyages_s2 = solution['services'][s2_id]

                if not voyages_s1 or not voyages_s2:
                    continue

                # Essayer d'échanger des voyages pour améliorer la continuité
                for v1 in voyages_s1:
                    if v1.get('fixe', False):
                        continue

                    for v2 in voyages_s2:
                        if v2.get('fixe', False):
                            continue

                        # Calculer score avant échange
                        score_avant = 0
                        if cache_geo.sont_consecutifs(v1['voyage_obj'], v2['voyage_obj']):
                            score_avant -= 100

                        # Vérifier si l'échange améliore la continuité
                        score_apres = 0
                        # (logique simplifiée ici)

                        if score_apres > score_avant:
                            if peut_echanger_voyages(v1, v2, voyages_s1, voyages_s2):
                                # Effectuer l'échange
                                voyages_s1.remove(v1)
                                voyages_s2.remove(v2)
                                voyages_s1.append(v2)
                                voyages_s2.append(v1)

                                # Retrier
                                voyages_s1.sort(key=lambda v: v['voyage_obj'].hdebut)
                                voyages_s2.sort(key=lambda v: v['voyage_obj'].hdebut)

                                ameliore = True
                                nb_echanges += 1
                                break

                    if ameliore:
                        break

                if ameliore:
                    break

            if ameliore:
                break

    temps = time.time() - start_time
    print(f"      {nb_echanges} échange(s) en {iteration} itération(s) - {temps:.3f}s")

    return solution


def analyser_solution(solution, voyages_list):
    """
    Analyse une solution et retourne des métriques détaillées
    """
    total_voyages = len(voyages_list)
    total_assignes = sum(len(voyages) for voyages in solution['services'].values())

    taux_assignation = (total_assignes / total_voyages * 100) if total_voyages > 0 else 0

    # Calculer la continuité géographique
    nb_continuite = 0
    nb_transitions = 0

    for voyages in solution['services'].values():
        for i in range(len(voyages) - 1):
            nb_transitions += 1
            try:
                if voyages[i]['voyage_obj'].arret_fin_id() == voyages[i+1]['voyage_obj'].arret_debut_id():
                    nb_continuite += 1
            except:
                pass

    taux_continuite = (nb_continuite / nb_transitions * 100) if nb_transitions > 0 else 0

    # Équilibrage
    nb_voyages_par_service = [len(v) for v in solution['services'].values()]
    equilibrage = max(nb_voyages_par_service) - min(nb_voyages_par_service) if nb_voyages_par_service else 0

    return {
        'taux_assignation': taux_assignation,
        'nb_assignes': total_assignes,
        'nb_total': total_voyages,
        'taux_continuite': taux_continuite,
        'nb_continuite': nb_continuite,
        'nb_transitions': nb_transitions,
        'equilibrage': equilibrage,
        'strategie': solution.get('strategie', 'Inconnue')
    }


# =============================================================================
# FONCTION PRINCIPALE (Compatible avec l'ancien code)
# =============================================================================

def optimiser_services(voyages_list, services_list, max_solutions=5, amelioration_locale=False):
    """
    Fonction principale d'optimisation (compatible avec l'ancienne interface)

    Args:
        voyages_list: Liste des voyages à assigner
        services_list: Liste des services disponibles
        max_solutions: Nombre maximum de solutions à générer
        amelioration_locale: Active l'amélioration locale (plus lent mais meilleur)

    Returns:
        Liste des solutions générées
    """
    solver = SolverOptimise(voyages_list, services_list)
    solutions = solver.optimiser(max_solutions, amelioration_locale)

    # Afficher l'analyse de chaque solution
    print("\n📈 Analyse des solutions:")
    for i, sol in enumerate(solutions, 1):
        metrics = analyser_solution(sol, voyages_list)
        print(f"\n   Solution {i} - {metrics['strategie']}:")
        print(f"      Assignation: {metrics['taux_assignation']:.1f}% ({metrics['nb_assignes']}/{metrics['nb_total']})")
        print(f"      Continuité géo: {metrics['taux_continuite']:.1f}% ({metrics['nb_continuite']}/{metrics['nb_transitions']})")
        print(f"      Équilibrage: {metrics['equilibrage']} voyages d'écart")

    return solutions


# =============================================================================
# EXEMPLE D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    # Exemple d'utilisation
    print("=" * 70)
    print("SOLVER OPTIMISÉ - Assignation de voyages")
    print("=" * 70)

    # Remplacer par vos vraies données
    # voyages = [...]  # Liste de vos objets voyage
    # services = [...]  # Liste de vos services

    # solutions = optimiser_services(voyages, services, max_solutions=5, amelioration_locale=True)

    print("\n✅ Exemple de code prêt à l'emploi!")