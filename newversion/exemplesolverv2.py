"""
Exemple d'utilisation du solver optimisé
Démonstration avec des données de test
"""

from solverv2 import optimiser_services, analyser_solution, SolverOptimise


# =============================================================================
# EXEMPLE 1 : Utilisation Simple (remplacement direct)
# =============================================================================

def exemple_simple():
    """
    Remplacer simplement ton ancien solver par celui-ci
    """
    print("=" * 70)
    print("EXEMPLE 1 : Utilisation Simple")
    print("=" * 70)

    # Tes données (à remplacer par tes vraies données)
    voyages = []  # Liste de tes objets voyage
    services = []  # Liste de tes tuples (service, indices_assignes)

    # EXACTEMENT comme avant !
    solutions = optimiser_services(
        voyages_list=voyages,
        services_list=services,
        max_solutions=5
    )

    print(f"\n✅ {len(solutions)} solutions générées")

    return solutions


# =============================================================================
# EXEMPLE 2 : Utilisation Avancée avec Analyse
# =============================================================================

def exemple_avance():
    """
    Utilisation avancée avec amélioration locale et analyse détaillée
    """
    print("\n" + "=" * 70)
    print("EXEMPLE 2 : Utilisation Avancée")
    print("=" * 70)

    # Tes données
    voyages = []  # Liste de tes objets voyage
    services = []  # Liste de tes tuples (service, indices_assignes)

    # Générer des solutions de haute qualité
    solutions = optimiser_services(
        voyages_list=voyages,
        services_list=services,
        max_solutions=5,
        amelioration_locale=True  # Active l'optimisation post-génération
    )

    # Analyser chaque solution
    print("\n📊 Analyse détaillée des solutions :")
    for i, solution in enumerate(solutions, 1):
        metrics = analyser_solution(solution, voyages)

        print(f"\n   Solution {i} - {solution['strategie']}")
        print(f"   {'─' * 60}")
        print(f"   Assignation    : {metrics['taux_assignation']:.1f}% "
              f"({metrics['nb_assignes']}/{metrics['nb_total']})")
        print(f"   Continuité géo : {metrics['taux_continuite']:.1f}% "
              f"({metrics['nb_continuite']}/{metrics['nb_transitions']})")
        print(f"   Équilibrage    : {metrics['equilibrage']} voyages d'écart")
        print(f"   Temps          : {solution.get('temps_generation', 0):.3f}s")

    # Sélectionner la meilleure solution
    meilleure = min(solutions, key=lambda s: s['nb_non_assignes'])

    print(f"\n🏆 Meilleure solution : {meilleure['strategie']}")
    print(f"   Non assignés : {meilleure['nb_non_assignes']}")

    return meilleure


# =============================================================================
# EXEMPLE 3 : Utilisation du Solver Directement
# =============================================================================

def exemple_solver_direct():
    """
    Utilisation directe du solver pour plus de contrôle
    """
    print("\n" + "=" * 70)
    print("EXEMPLE 3 : Utilisation Directe du Solver")
    print("=" * 70)

    # Tes données
    voyages = []  # Liste de tes objets voyage
    services = []  # Liste de tes tuples (service, indices_assignes)

    # Créer le solver
    solver = SolverOptimise(voyages, services)

    # Générer les solutions
    solutions = solver.optimiser(
        max_solutions=5,
        amelioration_locale=True
    )

    # Accéder aux statistiques détaillées
    print(f"\n📈 Statistiques du solver :")
    print(f"   Temps total        : {solver.stats['temps_total']:.3f}s")
    print(f"   Solutions générées : {solver.stats['solutions_generees']}")
    print(f"   Évaluations score  : {solver.stats['evaluations_score']}")

    # Statistiques du cache
    cache_stats = solver.cache_geo.get_stats()
    print(f"\n💾 Cache géographique :")
    print(f"   Hits   : {cache_stats['hits']}")
    print(f"   Misses : {cache_stats['misses']}")
    print(f"   Taux   : {cache_stats['hit_rate']:.1f}%")

    return solutions


# =============================================================================
# EXEMPLE 4 : Comparaison de Configurations
# =============================================================================

def exemple_comparaison():
    """
    Compare différentes configurations pour trouver la meilleure
    """
    print("\n" + "=" * 70)
    print("EXEMPLE 4 : Comparaison de Configurations")
    print("=" * 70)

    # Tes données
    voyages = []  # Liste de tes objets voyage
    services = []  # Liste de tes tuples (service, indices_assignes)

    configurations = [
        {
            'nom': 'Rapide',
            'max_solutions': 3,
            'amelioration_locale': False
        },
        {
            'nom': 'Équilibré',
            'max_solutions': 5,
            'amelioration_locale': False
        },
        {
            'nom': 'Qualité',
            'max_solutions': 5,
            'amelioration_locale': True
        }
    ]

    resultats = []

    for config in configurations:
        print(f"\n🔧 Test configuration : {config['nom']}")
        print(f"   max_solutions={config['max_solutions']}, "
              f"amelioration_locale={config['amelioration_locale']}")

        import time
        debut = time.time()

        solutions = optimiser_services(
            voyages_list=voyages,
            services_list=services,
            max_solutions=config['max_solutions'],
            amelioration_locale=config['amelioration_locale']
        )

        temps = time.time() - debut

        # Meilleure solution de cette config
        meilleure = min(solutions, key=lambda s: s['nb_non_assignes'])
        metrics = analyser_solution(meilleure, voyages)

        resultats.append({
            'config': config['nom'],
            'temps': temps,
            'nb_non_assignes': meilleure['nb_non_assignes'],
            'taux_assignation': metrics['taux_assignation'],
            'taux_continuite': metrics['taux_continuite']
        })

        print(f"   ✓ Temps : {temps:.3f}s")
        print(f"   ✓ Non assignés : {meilleure['nb_non_assignes']}")
        print(f"   ✓ Assignation : {metrics['taux_assignation']:.1f}%")
        print(f"   ✓ Continuité : {metrics['taux_continuite']:.1f}%")

    # Afficher le comparatif
    print("\n" + "=" * 70)
    print("📊 COMPARATIF DES CONFIGURATIONS")
    print("=" * 70)
    print(f"\n{'Config':<12} {'Temps':<10} {'Non Ass.':<12} {'Assign %':<12} {'Contin %':<12}")
    print("─" * 70)

    for r in resultats:
        print(f"{r['config']:<12} {r['temps']:<10.3f} {r['nb_non_assignes']:<12} "
              f"{r['taux_assignation']:<12.1f} {r['taux_continuite']:<12.1f}")

    # Recommandation
    print("\n💡 Recommandation :")
    meilleur_qualite = min(resultats, key=lambda r: r['nb_non_assignes'])
    meilleur_temps = min(resultats, key=lambda r: r['temps'])

    print(f"   Meilleure qualité : {meilleur_qualite['config']} "
          f"({meilleur_qualite['nb_non_assignes']} non assignés)")
    print(f"   Plus rapide      : {meilleur_temps['config']} "
          f"({meilleur_temps['temps']:.3f}s)")

    return resultats


# =============================================================================
# EXEMPLE 5 : Personnalisation des Poids
# =============================================================================

def exemple_personnalisation():
    """
    Montre comment personnaliser les poids de scoring
    """
    print("\n" + "=" * 70)
    print("EXEMPLE 5 : Personnalisation des Poids")
    print("=" * 70)

    print("""
    Pour personnaliser les poids du scoring, modifier dans solver_optimise.py :

    Ligne ~186, dans calculer_score_intelligent() :

    poids = {
        'continuite_geo': 150,    # ← Augmenter pour favoriser la continuité
        'proximite_temp': 50,     # ← Importance du temps d'attente
        'equilibrage': 10,        # ← Force de l'équilibrage
        'premier_voyage': 20,     # ← Bonus premier voyage
        'ligne_commune': 30       # ← Bonus même ligne
    }

    Exemples de modifications :

    1. Maximiser la continuité géographique :
       'continuite_geo': 300  (au lieu de 150)

    2. Mieux équilibrer les services :
       'equilibrage': 20  (au lieu de 10)

    3. Regrouper par ligne :
       'ligne_commune': 100  (au lieu de 30)

    4. Minimiser les temps morts :
       'proximite_temp': 100  (au lieu de 50)
    """)


# =============================================================================
# EXEMPLE 6 : Débogage et Diagnostic
# =============================================================================

def exemple_debug():
    """
    Techniques de débogage et diagnostic
    """
    print("\n" + "=" * 70)
    print("EXEMPLE 6 : Débogage et Diagnostic")
    print("=" * 70)

    # Tes données
    voyages = []  # Liste de tes objets voyage
    services = []  # Liste de tes tuples (service, indices_assignes)

    # Créer le solver
    solver = SolverOptimise(voyages, services)

    # Vérifications de base
    print("\n🔍 Vérifications préliminaires :")
    print(f"   Nombre de voyages : {len(voyages)}")
    print(f"   Nombre de services : {len(services)}")

    if not voyages:
        print("   ⚠️  Aucun voyage à assigner !")
        return

    if not services:
        print("   ⚠️  Aucun service disponible !")
        return

    # Analyser les horaires
    print("\n📅 Analyse des horaires :")
    heures_debut = [v.hdebut for v in voyages]
    heures_fin = [v.hfin for v in voyages]

    print(f"   Voyages - Début : {min(heures_debut):.0f}h → {max(heures_debut):.0f}h")
    print(f"   Voyages - Fin   : {min(heures_fin):.0f}h → {max(heures_fin):.0f}h")

    for idx, (service, _) in enumerate(services):
        print(f"   Service {idx} : {service.heure_debut:.0f}h → {service.heure_fin:.0f}h")

    # Détecter les problèmes potentiels
    print("\n⚠️  Problèmes potentiels :")

    # Voyages hors plage
    nb_hors_plage = 0
    for v in voyages:
        compatible = False
        for service, _ in services:
            if service.heure_debut <= v.hdebut and service.heure_fin >= v.hfin:
                compatible = True
                break
        if not compatible:
            nb_hors_plage += 1

    if nb_hors_plage > 0:
        print(f"   ⚠️  {nb_hors_plage} voyage(s) hors plage horaire des services")
    else:
        print(f"   ✓ Tous les voyages dans les plages horaires")

    # Générer les solutions
    print("\n🚀 Génération des solutions...")
    solutions = solver.optimiser(max_solutions=3)

    # Diagnostic des solutions
    print("\n🔬 Diagnostic des solutions :")
    for i, sol in enumerate(solutions, 1):
        print(f"\n   Solution {i} - {sol['strategie']}")

        # Voyages par service
        nb_voyages_par_service = [len(v) for v in sol['services'].values()]
        print(f"      Min voyages/service : {min(nb_voyages_par_service)}")
        print(f"      Max voyages/service : {max(nb_voyages_par_service)}")
        print(f"      Moyenne : {sum(nb_voyages_par_service) / len(nb_voyages_par_service):.1f}")

        # Services vides
        services_vides = sum(1 for v in nb_voyages_par_service if v == 0)
        if services_vides > 0:
            print(f"      ⚠️  {services_vides} service(s) vide(s)")

    return solutions


# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================

def main():
    """
    Point d'entrée principal - Exécute tous les exemples
    """
    print("\n" + "🎯" * 35)
    print("EXEMPLES D'UTILISATION DU SOLVER OPTIMISÉ")
    print("🎯" * 35)

    # Décommenter les exemples que tu veux tester :

    # exemple_simple()
    # exemple_avance()
    # exemple_solver_direct()
    # exemple_comparaison()
    exemple_personnalisation()
    # exemple_debug()

    print("\n" + "=" * 70)
    print("✅ Exemples terminés !")
    print("=" * 70)

    print("""
    💡 Prochaines étapes :

    1. Remplacer les listes vides voyages=[] et services=[] 
       par tes vraies données

    2. Exécuter le script :
       python exemple_utilisation.py

    3. Comparer les différentes configurations

    4. Ajuster les poids si nécessaire (voir exemple_personnalisation)

    5. Intégrer dans ton projet :
       from solver_optimise import optimiser_services
    """)


if __name__ == "__main__":
    main()