# solver_bus.py
from objet import voyage, service_agent, proposition


# ── Fonctions du solver (inchangées) ─────────────────────────────────────────

def voyage_compatible(service, nouveau_voyage, min_pause, max_pause):
    for v in service.get_voyages():
        if not (nouveau_voyage.hfin <= v.hdebut or nouveau_voyage.hdebut >= v.hfin):
            return False
    voyages_tries = sorted(service.get_voyages() + [nouveau_voyage], key=lambda v: v.hdebut)
    idx = voyages_tries.index(nouveau_voyage)
    if idx > 0:
        pause = nouveau_voyage.hdebut - voyages_tries[idx - 1].hfin
        if not (min_pause <= pause <= max_pause):
            return False
    if idx < len(voyages_tries) - 1:
        pause = voyages_tries[idx + 1].hdebut - nouveau_voyage.hfin
        if not (min_pause <= pause <= max_pause):
            return False
    return True


def creer_service(num, voy, petit=False):
    type_s = "matin" if voy.hdebut <= 600 else "après-midi"
    s = service_agent(num_service=num, type_service=type_s)
    s.petit_service = petit
    return s


def peut_ajouter_lignes(service, voy, voy2, nb_max_lignes):
    lignes = set(v.num_ligne for v in service.get_voyages())
    lignes.add(voy.num_ligne)
    lignes.add(voy2.num_ligne)
    return len(lignes) <= nb_max_lignes


def verifier_duree_service(service, min_duree, max_duree):
    duree = service.duree_travail_effective()
    if duree < min_duree:
        return False, f"Trop court : {duree} min"
    if duree > max_duree:
        return False, f"Trop long : {duree} min"
    return True, f"OK : {duree} min"


def tous_services_duree_valide(propo, min_duree, max_duree):
    for s in propo.service:
        if s.get_voyages() and not s.petit_service:
            valide, _ = verifier_duree_service(s, min_duree, max_duree)
            if not valide:
                return False
    return True


def petits_services_valides(propo, max_duree_petit=4 * 60):
    for s in propo.service:
        if s.get_voyages() and s.petit_service:
            if s.duree_travail_effective() > max_duree_petit:
                return False
    return True


def essayer_proposition(voyages, min_pause, max_pause, nb_max_lignes, max_services, num_proposition):
    for v in voyages:
        v.assigned = False

    propo = proposition(num_proposition=num_proposition)
    service_cible = creer_service(1, voyages[0])
    propo.ajout_service(service_cible)

    min_duree = 6 * 60
    max_duree = 8 * 60 + 30

    for i in range(len(voyages)):
        for j in range(i + 1, len(voyages)):
            voy = voyages[i]
            voy2 = voyages[j]
            pause_entre = voy2.hdebut - voy.hfin

            if (voy.hdebut <= voy2.hfin
                    and voy.hfin <= voy2.hdebut
                    and voy.arret_fin == voy2.arret_debut
                    and not voy.assigned
                    and not voy2.assigned
                    and min_pause <= pause_entre <= max_pause):

                service_cible = None
                for s in propo.service:
                    if s.petit_service:
                        continue
                    tous_voyages = s.get_voyages() + [voy, voy2]
                    debut_simule = min(v.hdebut for v in tous_voyages)
                    fin_simulee = max(v.hfin for v in tous_voyages)
                    duree_simulee = fin_simulee - debut_simule
                    if (voyage_compatible(s, voy, min_pause, max_pause)
                            and voyage_compatible(s, voy2, min_pause, max_pause)
                            and peut_ajouter_lignes(s, voy, voy2, nb_max_lignes)
                            and min_duree <= duree_simulee <= max_duree):
                        service_cible = s
                        break

                if service_cible is None:
                    if len(propo.service) >= max_services:
                        break
                    duree_paire = voy2.hfin - voy.hdebut
                    if not (min_duree <= duree_paire <= max_duree):
                        break
                    service_cible = creer_service(len(propo.service) + 1, voy, petit=False)
                    propo.ajout_service(service_cible)

                if service_cible is None:
                    break

                service_cible.ajouter_voyage(voy)
                service_cible.ajouter_voyage(voy2)
                voy.assigned = True
                voy2.assigned = True
                break

    max_duree_petit = 4 * 60
    for voy in [v for v in voyages if not v.assigned]:
        service_cible = None
        for s in propo.service:
            if not s.petit_service:
                continue
            tous_voyages = s.get_voyages() + [voy]
            debut_simule = min(v.hdebut for v in tous_voyages)
            fin_simulee = max(v.hfin for v in tous_voyages)
            duree_simulee = fin_simulee - debut_simule
            if (voyage_compatible(s, voy, min_pause, max_pause)
                    and peut_ajouter_lignes(s, voy, voy, nb_max_lignes)
                    and duree_simulee <= max_duree_petit):
                service_cible = s
                break
        if service_cible is None:
            if len(propo.service) >= max_services:
                continue
            service_cible = creer_service(len(propo.service) + 1, voy, petit=True)
            propo.ajout_service(service_cible)
        service_cible.ajouter_voyage(voy)
        voy.assigned = True

    return propo


# ── Fonction appelée par l'interface ─────────────────────────────────────────

def optimiser_services(voyages_list, services_data, max_solutions=5, pause_min=15):
    """
    Appelée par MainWindow.optimiser_services()
    Retourne une liste de solutions au format attendu par l'interface.
    """
    min_pause = pause_min
    max_pause = 60
    nb_max_lignes = 1
    max_services = 10
    cible_duree = 7 * 60 + 15
    variation = 0

    propositions_trouvees = []
    num_proposition = 1
    max_iterations = 200  # garde-fou contre boucle infinie

    while len(propositions_trouvees) < max_solutions and max_iterations > 0:
        max_iterations -= 1

        min_duree_service = max(360, cible_duree - variation)
        max_duree_service = min(510, cible_duree + variation)

        propo = essayer_proposition(
            voyages_list, min_pause, max_pause,
            nb_max_lignes, max_services, num_proposition
        )

        voyages_non_assignes = [v for v in voyages_list if not v.assigned]

        if (not voyages_non_assignes
                and tous_services_duree_valide(propo, min_duree_service, max_duree_service)
                and petits_services_valides(propo)):
            propositions_trouvees.append(propo)
            num_proposition += 1
            variation += 15
        else:
            variation += 15
            if min_pause > 0:
                min_pause = max(0, min_pause - 5)
            elif max_pause < 120:
                max_pause += 15
            elif nb_max_lignes < 4:
                nb_max_lignes += 1
            elif max_services < 15:
                max_services += 1
            else:
                break

    # ── Convertir au format attendu par l'interface ───────────────────────────
    solutions = []
    for propo in propositions_trouvees:
        services_dict = {}
        nb_non_assignes = len([v for v in voyages_list if not getattr(v, 'assigned', False)])

        for service_idx, s in enumerate(propo.service):
            if not s.get_voyages():
                continue  # ignorer les services vides

            voyages_in_service = []
            for voy in s.get_voyages():
                try:
                    voy_idx = voyages_list.index(voy)
                except ValueError:
                    voy_idx = -1
                voyages_in_service.append({
                    "voyage_obj": voy,
                    "fixe": False,
                    "index": voy_idx
                })
            services_dict[service_idx] = voyages_in_service

        solutions.append({
            "strategie": f"Proposition {propo.num_proposition}",
            "nb_non_assignes": nb_non_assignes,
            "services": services_dict,
            "_propo": propo  # référence brute si besoin
        })

    return solutions