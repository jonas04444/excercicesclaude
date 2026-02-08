"""
Script de test pour la stratégie "Une ligne par service"
Démontre la différence entre les stratégies
"""


# NOTE: Ce script nécessite d'avoir tes vraies données
# Remplace les classes mock par tes vrais objets

class VoyageMock:
    """Mock d'un voyage pour tester"""

    def __init__(self, num_ligne, hdebut, hfin, arret_debut, arret_fin):
        self.num_ligne = num_ligne
        self.hdebut = hdebut
        self.hfin = hfin
        self._arret_debut = arret_debut
        self._arret_fin = arret_fin

    def arret_debut_id(self):
        return self._arret_debut

    def arret_fin_id(self):
        return self._arret_fin


class ServiceMock:
    """Mock d'un service pour tester"""

    def __init__(self, heure_debut, heure_fin):
        self.heure_debut = heure_debut
        self.heure_fin = heure_fin
        self.pauses = []

    def est_dans_pause(self, debut, fin):
        return False


def creer_donnees_test():
    """
    Crée des données de test pour démontrer la stratégie
    """

    # Créer des voyages de 3 lignes différentes
    voyages = [
        # Ligne 1 (5 voyages)
        VoyageMock(1, 8.0, 9.0, "A1", "A2"),
        VoyageMock(1, 9.5, 10.5, "A2", "A3"),
        VoyageMock(1, 11.0, 12.0, "A3", "A1"),
        VoyageMock(1, 13.0, 14.0, "A1", "A2"),
        VoyageMock(1, 14.5, 15.5, "A2", "A3"),

        # Ligne 2 (4 voyages)
        VoyageMock(2, 8.5, 9.5, "B1", "B2"),
        VoyageMock(2, 10.0, 11.0, "B2", "B3"),
        VoyageMock(2, 12.0, 13.0, "B3", "B1"),
        VoyageMock(2, 14.0, 15.0, "B1", "B2"),

        # Ligne 3 (3 voyages)
        VoyageMock(3, 9.0, 10.0, "C1", "C2"),
        VoyageMock(3, 11.5, 12.5, "C2", "C3"),
        VoyageMock(3, 13.5, 14.5, "C3", "C1"),
    ]

    # Créer des services (4 services disponibles)
    services = [
        (ServiceMock(7.0, 16.0), set()),  # Service 1
        (ServiceMock(7.0, 16.0), set()),  # Service 2
        (ServiceMock(7.0, 16.0), set()),  # Service 3
        (ServiceMock(7.0, 16.0), set()),  # Service 4
    ]

    return voyages, services


def afficher_comparaison():
    """
    Compare les résultats avec et sans la contrainte ligne unique
    """
    print("=" * 80)
    print("🧪 TEST - Stratégie 'Une ligne par service'")
    print("=" * 80)

    voyages, services = creer_donnees_test()

    print(f"\n📊 Données de test :")
    print(f"   12 voyages : 5 de ligne 1, 4 de ligne 2, 3 de ligne 3")
    print(f"   4 services disponibles (7h-16h)")

    # Importer le solver
    try:
        from solverv2 import optimiser_services, analyser_solution
    except ImportError:
        print("\n❌ Erreur : solver_optimise.py non trouvé")
        print("   Assurez-vous que le fichier est dans le même dossier")
        return

    # Générer toutes les solutions
    print(f"\n🔧 Génération de 6 solutions...")
    solutions = optimiser_services(voyages, services, max_solutions=6)

    print("\n" + "=" * 80)
    print("📈 COMPARAISON DES STRATÉGIES")
    print("=" * 80)

    # Analyser chaque solution
    for i, sol in enumerate(solutions, 1):
        metrics = analyser_solution(sol, voyages)

        print(f"\n{'─' * 80}")
        print(f"Solution {i} : {metrics['strategie']}")
        print(f"{'─' * 80}")

        print(
            f"  📍 Assignation    : {metrics['taux_assignation']:.1f}% ({metrics['nb_assignes']}/{metrics['nb_total']})")
        print(
            f"  🔗 Continuité géo : {metrics['taux_continuite']:.1f}% ({metrics['nb_continuite']}/{metrics['nb_transitions']})")
        print(f"  ⚖️  Équilibrage    : {metrics['equilibrage']} voyages d'écart")

        if metrics['respect_ligne_unique']:
            print(f"  ✅ Contrainte     : UNE ligne par service")
        else:
            print(f"  ⚠️  Contrainte     : {metrics['nb_services_multi_lignes']} service(s) avec plusieurs lignes")

        # Détail des services
        print(f"\n  📋 Détail des services :")
        for service_id, voyages_service in sol['services'].items():
            if voyages_service:
                lignes = set(v['voyage_obj'].num_ligne for v in voyages_service)
                nb_voyages = len(voyages_service)

                if len(lignes) == 1:
                    ligne = list(lignes)[0]
                    print(f"     Service {service_id} : {nb_voyages} voyages - Ligne {ligne} ✅")
                else:
                    lignes_str = ", ".join(str(l) for l in sorted(lignes))
                    print(f"     Service {service_id} : {nb_voyages} voyages - Lignes {lignes_str} ⚠️")

    # Recommandation
    print("\n" + "=" * 80)
    print("💡 RECOMMANDATION")
    print("=" * 80)

    # Trouver la meilleure solution classique
    solutions_classiques = solutions[:5]
    meilleure_classique = max(solutions_classiques,
                              key=lambda s: analyser_solution(s, voyages)['taux_assignation'])
    metrics_classique = analyser_solution(meilleure_classique, voyages)

    # Solution ligne unique
    solution_ligne_unique = solutions[5]
    metrics_ligne_unique = analyser_solution(solution_ligne_unique, voyages)

    print(f"\n📊 Meilleure solution classique : {metrics_classique['strategie']}")
    print(f"   Assignation : {metrics_classique['taux_assignation']:.1f}%")
    print(f"   Continuité  : {metrics_classique['taux_continuite']:.1f}%")
    print(f"   Services multi-lignes : {metrics_classique['nb_services_multi_lignes']}")

    print(f"\n🎯 Solution 'Une ligne par service' :")
    print(f"   Assignation : {metrics_ligne_unique['taux_assignation']:.1f}%")
    print(f"   Continuité  : {metrics_ligne_unique['taux_continuite']:.1f}%")
    print(f"   Services multi-lignes : {metrics_ligne_unique['nb_services_multi_lignes']}")

    print(f"\n{'─' * 80}")

    if metrics_ligne_unique['respect_ligne_unique']:
        print("✅ La stratégie 'Une ligne par service' respecte bien la contrainte !")
    else:
        print("⚠️  Attention : La contrainte n'est pas totalement respectée")
        print("   Possible si des voyages sont pré-assignés avec des lignes différentes")

    print("\n💡 Choisir selon vos priorités :")
    print("   • Maximiser assignation → Solution classique")
    print("   • Une ligne par service → Solution 6")
    print("   • Compromis → Comparer les métriques")


def test_rapide():
    """
    Test rapide pour vérifier que la contrainte fonctionne
    """
    print("\n" + "=" * 80)
    print("⚡ TEST RAPIDE - Vérification de la contrainte")
    print("=" * 80)

    voyages, services = creer_donnees_test()

    try:
        from solver_optimise import SolverOptimise
    except ImportError:
        print("\n❌ Erreur : solver_optimise.py non trouvé")
        return

    # Créer le solver
    solver = SolverOptimise(voyages, services)

    # Tester uniquement la stratégie ligne unique
    print("\n🎯 Test de la stratégie 'Une ligne par service'...")

    # Générer la solution
    strat_nom = "Une ligne par service"
    strat_func = lambda v: (v['voyage'].num_ligne, v['voyage'].hdebut)

    solution = solver.generer_solution(strat_nom, strat_func)

    # Vérifier la contrainte
    print("\n🔍 Vérification de la contrainte :")

    contrainte_respectee = True
    for service_id, voyages_service in solution['services'].items():
        if voyages_service:
            lignes = set(v['voyage_obj'].num_ligne for v in voyages_service)

            if len(lignes) == 1:
                print(f"   ✅ Service {service_id} : Ligne {list(lignes)[0]} uniquement")
            else:
                print(f"   ❌ Service {service_id} : Lignes {lignes} (ERREUR)")
                contrainte_respectee = False

    if contrainte_respectee:
        print("\n🎉 Succès ! La contrainte est bien respectée.")
    else:
        print("\n⚠️  Problème : La contrainte n'est pas respectée partout.")

    return contrainte_respectee


if __name__ == "__main__":
    print("\n" + "🚀" * 40)
    print("TEST - STRATÉGIE 'UNE LIGNE PAR SERVICE'")
    print("🚀" * 40)

    # Choisir le type de test
    print("\nChoisir le test à exécuter :")
    print("1. Test rapide (vérification contrainte)")
    print("2. Comparaison complète (6 stratégies)")

    # Pour l'exemple, on fait les deux
    print("\n" + "=" * 80)

    # Test rapide
    resultat = test_rapide()

    # Comparaison complète
    if resultat:
        print("\n\nTest rapide OK ✅ - Lancement de la comparaison complète...\n")
        afficher_comparaison()

    print("\n" + "=" * 80)
    print("✅ Tests terminés !")
    print("=" * 80)

    print("""

📝 Notes importantes :

1. Ce script utilise des données MOCK pour tester
2. Pour utiliser avec tes vraies données :
   - Remplace VoyageMock et ServiceMock par tes vraies classes
   - Charge tes vraies données dans creer_donnees_test()

3. La contrainte fonctionne si :
   - Chaque service ne contient que des voyages d'une seule ligne
   - Affiché avec ✅ dans l'analyse

4. Si tu vois des ⚠️ :
   - Vérifier les pré-assignations
   - Augmenter le nombre de services
   - Vérifier que tes objets voyage ont bien un attribut num_ligne
    """)