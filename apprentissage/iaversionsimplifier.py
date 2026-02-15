"""
🎯 EXERCICES PRATIQUES PROGRESSIFS
Système de Classification des Services Bus
===========================================

Ces exercices vous permettent de maîtriser progressivement chaque partie du code.
Commencez par l'exercice 1 et avancez dans l'ordre.
"""

# ============================================
# NIVEAU 1 : EXERCICES DE BASE
# ============================================

print("=" * 80)
print("NIVEAU 1 : MANIPULATION DES HEURES")
print("=" * 80)

# ─────────────────────────────────────
# EXERCICE 1.1 : Convertir des heures en minutes
# ─────────────────────────────────────
print("\n📝 EXERCICE 1.1 : Conversion d'heures")
print("─" * 80)


def heure_to_minutes(heure_str):
    """Convertit une heure en minutes"""
    if ':' in str(heure_str):
        parts = str(heure_str).split(':')
        heures = int(parts[0])
        minutes = int(parts[1])
        return heures * 60 + minutes
    return None


# TODO : Complétez les conversions suivantes
heures_test = ["6:00", "6:30", "12:00", "18:45", "23:59"]

print("Heures à convertir :")
for heure in heures_test:
    resultat = heure_to_minutes(heure)
    print(f"  {heure} = {resultat} minutes")

    # TODO : Vérifiez vos résultats
    # 6:00 devrait donner 360
    # 6:30 devrait donner 390
    # 12:00 devrait donner 720
    # etc.

print("\n✅ Si tous les résultats sont corrects, passez à l'exercice suivant !")

# ─────────────────────────────────────
# EXERCICE 1.2 : Convertir des minutes en heures
# ─────────────────────────────────────
print("\n\n📝 EXERCICE 1.2 : Conversion inverse")
print("─" * 80)


def minutes_to_heure(minutes):
    """TODO : Complétez cette fonction

    Indice : Utilisez // pour la division entière et % pour le modulo

    Exemples attendus :
        390 → "06:30"
        825 → "13:45"
    """
    # TODO : Écrivez votre code ici
    h = 0  # À remplacer
    m = 0  # À remplacer
    return f"{h:02d}:{m:02d}"


# Test
minutes_test = [360, 390, 720, 1125, 1439]
print("Minutes à convertir :")
for minutes in minutes_test:
    resultat = minutes_to_heure(minutes)
    print(f"  {minutes} minutes = {resultat}")

print("\n💡 SOLUTION :")
print("""
def minutes_to_heure(minutes):
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h:02d}:{m:02d}"
""")

# ─────────────────────────────────────
# EXERCICE 1.3 : Calculer une durée
# ─────────────────────────────────────
print("\n\n📝 EXERCICE 1.3 : Calculer la durée d'un voyage")
print("─" * 80)


def calculer_duree_voyage(heure_debut, heure_fin):
    """TODO : Calculez la durée en minutes entre deux heures

    Exemple : de 6:00 à 6:35 = 35 minutes
    """
    # TODO : Convertissez les heures en minutes
    debut_min = heure_to_minutes(heure_debut)
    fin_min = heure_to_minutes(heure_fin)

    # TODO : Calculez la différence
    duree = 0  # À remplacer

    return duree


# Test
voyages_test = [
    ("6:00", "6:35"),
    ("14:20", "15:05"),
    ("18:00", "19:15")
]

print("Durée des voyages :")
for debut, fin in voyages_test:
    duree = calculer_duree_voyage(debut, fin)
    print(f"  {debut} → {fin} = {duree} minutes")

# ============================================
# NIVEAU 2 : DÉTECTION DES COUPURES
# ============================================

print("\n\n" + "=" * 80)
print("NIVEAU 2 : DÉTECTION DES COUPURES")
print("=" * 80)

# ─────────────────────────────────────
# EXERCICE 2.1 : Identifier une coupure simple
# ─────────────────────────────────────
print("\n📝 EXERCICE 2.1 : Y a-t-il une coupure ?")
print("─" * 80)


def a_une_coupure(heures_debut, heures_fin, seuil=90):
    """TODO : Déterminez s'il y a une coupure

    Une coupure = un écart > seuil entre la fin d'un voyage et le début du suivant

    Args:
        heures_debut: [360, 395, 840] (liste des heures de début en minutes)
        heures_fin: [390, 425, 870] (liste des heures de fin en minutes)
        seuil: 90 (écart minimum pour considérer une coupure)

    Returns:
        True si coupure détectée, False sinon
    """
    # TODO : Complétez cette fonction

    # Indice 1 : Bouclez de 0 à len(heures_fin)-1
    # Indice 2 : Calculez l'écart = heures_debut[i+1] - heures_fin[i]
    # Indice 3 : Si un écart > seuil, retournez True

    return False  # À remplacer


# Test 1 : Service sans coupure
heures_d1 = [360, 395, 430, 465]  # 6:00, 6:35, 7:10, 7:45
heures_f1 = [390, 425, 460, 495]  # 6:30, 7:05, 7:40, 8:15

result1 = a_une_coupure(heures_d1, heures_f1)
print(f"Test 1 (pas de coupure) : {result1}")
print(f"  Attendu : False")

# Test 2 : Service avec coupure
heures_d2 = [360, 395, 840]  # 6:00, 6:35, 14:00
heures_f2 = [390, 425, 870]  # 6:30, 7:05, 14:30

result2 = a_une_coupure(heures_d2, heures_f2)
print(f"\nTest 2 (avec coupure) : {result2}")
print(f"  Attendu : True (écart de {840 - 425} minutes entre 7:05 et 14:00)")

print("\n💡 SOLUTION :")
print("""
def a_une_coupure(heures_debut, heures_fin, seuil=90):
    for i in range(len(heures_fin) - 1):
        ecart = heures_debut[i+1] - heures_fin[i]
        if ecart > seuil:
            return True
    return False
""")

# ─────────────────────────────────────
# EXERCICE 2.2 : Trouver la durée de la coupure
# ─────────────────────────────────────
print("\n\n📝 EXERCICE 2.2 : Quelle est la durée de la coupure ?")
print("─" * 80)


def trouver_duree_coupure(heures_debut, heures_fin, seuil=90):
    """TODO : Retournez la durée de la plus grande coupure

    Returns:
        duree: int (0 si pas de coupure)
    """
    # TODO : Complétez
    # Indice : Gardez le max_ecart au lieu de juste retourner True/False

    max_ecart = 0

    # Votre code ici

    return max_ecart if max_ecart > seuil else 0


# Test
heures_d = [360, 395, 840, 875]
heures_f = [390, 425, 870, 905]

duree = trouver_duree_coupure(heures_d, heures_f)
print(f"Durée de la coupure : {duree} minutes ({duree // 60}h{duree % 60:02d})")
print(f"Attendu : 415 minutes (6h55)")

# ============================================
# NIVEAU 3 : CLASSIFICATION DES SERVICES
# ============================================

print("\n\n" + "=" * 80)
print("NIVEAU 3 : CLASSIFIER LES SERVICES")
print("=" * 80)

# ─────────────────────────────────────
# EXERCICE 3.1 : Déterminer si c'est un service MATIN
# ─────────────────────────────────────
print("\n📝 EXERCICE 3.1 : Est-ce un service MATIN ?")
print("─" * 80)


def est_service_matin(heure_debut, heure_fin):
    """TODO : Déterminez si c'est un service du matin

    Règle : Un service MATIN finit avant 12h00 (720 minutes)

    Args:
        heure_debut: int (minutes)
        heure_fin: int (minutes)

    Returns:
        True si MATIN, False sinon
    """
    # TODO : Complétez
    MIDI = 720

    # Votre code ici

    return False


# Tests
services_test = [
    (360, 660, True),  # 6:00 → 11:00 = MATIN
    (360, 780, False),  # 6:00 → 13:00 = PAS MATIN
    (420, 690, True),  # 7:00 → 11:30 = MATIN
]

print("Tests :")
for debut, fin, attendu in services_test:
    resultat = est_service_matin(debut, fin)
    symbole = "✅" if resultat == attendu else "❌"
    print(f"  {symbole} {minutes_to_heure(debut)} → {minutes_to_heure(fin)} : {resultat} (attendu: {attendu})")

# ─────────────────────────────────────
# EXERCICE 3.2 : Classifier un service complet
# ─────────────────────────────────────
print("\n\n📝 EXERCICE 3.2 : Classifier un service (MATIN, APREM, JOURNEE)")
print("─" * 80)


def classifier_service(heure_debut, heure_fin, a_coupure=False):
    """TODO : Classifiez le service

    Règles :
        - Si coupure → "COUPE"
        - Si fin avant 12h → "MATIN"
        - Si début après 12h → "APREM"
        - Sinon → "JOURNEE"

    Returns:
        str : "MATIN", "APREM", "JOURNEE", ou "COUPE"
    """
    MIDI = 720

    # TODO : Complétez avec les if/elif/else

    if a_coupure:
        return "COUPE"

    # Votre code ici

    return "JOURNEE"


# Tests
tests = [
    (360, 690, False, "MATIN"),  # 6:00 → 11:30, pas de coupure
    (780, 1140, False, "APREM"),  # 13:00 → 19:00, pas de coupure
    (360, 1140, False, "JOURNEE"),  # 6:00 → 19:00, pas de coupure
    (360, 1140, True, "COUPE"),  # Peu importe, il y a une coupure
]

print("Tests de classification :")
for debut, fin, coupure, attendu in tests:
    resultat = classifier_service(debut, fin, coupure)
    symbole = "✅" if resultat == attendu else "❌"
    coupure_str = "avec coupure" if coupure else "sans coupure"
    print(
        f"  {symbole} {minutes_to_heure(debut)} → {minutes_to_heure(fin)} ({coupure_str}) : {resultat} (attendu: {attendu})")

# ============================================
# NIVEAU 4 : MANIPULATION DE DATAFRAMES
# ============================================

print("\n\n" + "=" * 80)
print("NIVEAU 4 : MANIPULATION DE DONNÉES (PANDAS)")
print("=" * 80)

import pandas as pd

# ─────────────────────────────────────
# EXERCICE 4.1 : Créer un DataFrame
# ─────────────────────────────────────
print("\n📝 EXERCICE 4.1 : Créer un DataFrame de voyages")
print("─" * 80)

# TODO : Créez un DataFrame avec ces colonnes :
# - num_service : "S001", "S001", "S001", "S002", "S002"
# - heure_debut : "6:00", "6:35", "7:10", "13:00", "13:35"
# - heure_fin : "6:30", "7:05", "7:40", "13:30", "14:05"

# Votre code ici :
df_voyages = pd.DataFrame({
    # TODO : Complétez
})

print("DataFrame créé :")
print(df_voyages)

# ─────────────────────────────────────
# EXERCICE 4.2 : Grouper par service
# ─────────────────────────────────────
print("\n\n📝 EXERCICE 4.2 : Regrouper les voyages par service")
print("─" * 80)

# TODO : Utilisez groupby pour compter le nombre de voyages par service
# Indice : df_voyages.groupby('num_service').size()

# Votre code ici :
nb_voyages_par_service = None  # À remplacer

print("Nombre de voyages par service :")
print(nb_voyages_par_service)

# ─────────────────────────────────────
# EXERCICE 4.3 : Convertir une colonne
# ─────────────────────────────────────
print("\n\n📝 EXERCICE 4.3 : Convertir les heures en minutes")
print("─" * 80)

# TODO : Ajoutez une colonne 'heure_debut_min' qui contient heure_debut en minutes
# Indice : df['nouvelle_colonne'] = df['ancienne_colonne'].apply(fonction)

# Votre code ici :
# df_voyages['heure_debut_min'] = ...

print("DataFrame avec conversion :")
print(df_voyages)

# ============================================
# NIVEAU 5 : PROJET COMPLET
# ============================================

print("\n\n" + "=" * 80)
print("NIVEAU 5 : MINI-PROJET COMPLET")
print("=" * 80)

print("""
🎯 MINI-PROJET : Créer votre propre système de classification simplifié

Objectif : Créer un script qui :
1. Charge des données de voyages (vous pouvez les générer)
2. Regroupe les voyages par service
3. Détecte les coupures
4. Classifie chaque service
5. Affiche un résumé

Étapes suggérées :
─────────────────

1. Créez un DataFrame avec au moins 3 services différents :
   - Un service MATIN
   - Un service APREM
   - Un service avec COUPURE

2. Écrivez une fonction qui regroupe les voyages par service

3. Pour chaque service, calculez :
   - Heure de début (min des heures de début)
   - Heure de fin (max des heures de fin)
   - Nombre de voyages
   - Y a-t-il une coupure ?
   - Type de service

4. Affichez un joli résumé

Bonus :
───────
- Ajoutez un graphique avec matplotlib
- Exportez les résultats dans un fichier Excel
- Créez une fonction qui prédit le type d'un nouveau service

Bon courage ! 🚀
""")

# ============================================
# SOLUTIONS
# ============================================

print("\n\n" + "=" * 80)
print("💡 SOLUTIONS (ne regardez qu'après avoir essayé !)")
print("=" * 80)

print("""
SOLUTION EXERCICE 1.2 :
───────────────────────
def minutes_to_heure(minutes):
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h:02d}:{m:02d}"


SOLUTION EXERCICE 1.3 :
───────────────────────
def calculer_duree_voyage(heure_debut, heure_fin):
    debut_min = heure_to_minutes(heure_debut)
    fin_min = heure_to_minutes(heure_fin)
    duree = fin_min - debut_min
    return duree


SOLUTION EXERCICE 2.1 :
───────────────────────
def a_une_coupure(heures_debut, heures_fin, seuil=90):
    for i in range(len(heures_fin) - 1):
        ecart = heures_debut[i+1] - heures_fin[i]
        if ecart > seuil:
            return True
    return False


SOLUTION EXERCICE 2.2 :
───────────────────────
def trouver_duree_coupure(heures_debut, heures_fin, seuil=90):
    max_ecart = 0
    for i in range(len(heures_fin) - 1):
        ecart = heures_debut[i+1] - heures_fin[i]
        if ecart > max_ecart:
            max_ecart = ecart
    return max_ecart if max_ecart > seuil else 0


SOLUTION EXERCICE 3.1 :
───────────────────────
def est_service_matin(heure_debut, heure_fin):
    MIDI = 720
    return heure_fin <= MIDI


SOLUTION EXERCICE 3.2 :
───────────────────────
def classifier_service(heure_debut, heure_fin, a_coupure=False):
    MIDI = 720

    if a_coupure:
        return "COUPE"

    if heure_fin <= MIDI:
        return "MATIN"
    elif heure_debut >= MIDI:
        return "APREM"
    else:
        return "JOURNEE"


SOLUTION EXERCICE 4.1 :
───────────────────────
df_voyages = pd.DataFrame({
    'num_service': ["S001", "S001", "S001", "S002", "S002"],
    'heure_debut': ["6:00", "6:35", "7:10", "13:00", "13:35"],
    'heure_fin': ["6:30", "7:05", "7:40", "13:30", "14:05"]
})


SOLUTION EXERCICE 4.2 :
───────────────────────
nb_voyages_par_service = df_voyages.groupby('num_service').size()


SOLUTION EXERCICE 4.3 :
───────────────────────
df_voyages['heure_debut_min'] = df_voyages['heure_debut'].apply(heure_to_minutes)
df_voyages['heure_fin_min'] = df_voyages['heure_fin'].apply(heure_to_minutes)
""")

print("\n" + "=" * 80)
print("✨ Fin des exercices ! Continuez à pratiquer pour maîtriser le code.")
print("=" * 80)