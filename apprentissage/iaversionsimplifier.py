"""
🎓 VERSION SIMPLIFIÉE ET COMMENTÉE
Système de Classification des Services Bus
============================================

Cette version est ULTRA commentée pour l'apprentissage.
Chaque ligne importante est expliquée.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# ============================================
# ÉTAPE 1 : FONCTIONS DE BASE
# ============================================

def heure_to_minutes(heure_str):
    """
    Convertit une heure en minutes.

    Pourquoi ? Les ordinateurs calculent mieux avec des nombres.

    Exemples:
        "6:30" → 390 minutes (6×60 + 30)
        "13:45" → 825 minutes

    📝 EXERCICE : Ajoutez un print() pour voir la conversion en action
    """
    try:
        # Si l'heure est vide, retourner None
        if pd.isna(heure_str):
            return None

        # Si c'est déjà un nombre, le retourner tel quel
        if isinstance(heure_str, (int, float)):
            return int(heure_str)

        # Convertir en texte et enlever les espaces
        heure_str = str(heure_str).strip()

        # Si l'heure contient ":", séparer heures et minutes
        if ':' in heure_str:
            parts = heure_str.split(':')  # ["6", "30"]
            heures = int(parts[0])        # 6
            minutes = int(parts[1])       # 30
            resultat = heures * 60 + minutes  # 6×60 + 30 = 390

            # 📝 Décommentez pour voir la conversion :
            # print(f"Conversion : {heure_str} → {resultat} minutes")

            return resultat

        # Si c'est juste un nombre
        return int(float(heure_str))

    except Exception as e:
        print(f"❌ Erreur avec '{heure_str}': {e}")
        return None


def minutes_to_heure(minutes):
    """
    Convertit des minutes en format HH:MM

    Exemples:
        390 → "06:30"
        825 → "13:45"
    """
    if pd.isna(minutes):
        return "N/A"

    h = int(minutes) // 60  # Division entière pour avoir les heures
    m = int(minutes) % 60   # Modulo pour avoir les minutes restantes

    # :02d signifie : afficher sur 2 chiffres avec des 0 devant si besoin
    return f"{h:02d}:{m:02d}"


def detecter_coupure(heures_debut, heures_fin, seuil=90):
    """
    Détecte s'il y a une pause (coupure) dans le service.

    Une coupure = un écart > seuil minutes entre deux voyages.

    Args:
        heures_debut: Liste des heures de début [360, 395, 430, ...]
        heures_fin: Liste des heures de fin [390, 425, 460, ...]
        seuil: Écart minimum pour considérer qu'il y a une coupure (défaut: 90 min)

    Returns:
        (a_coupure: bool, duree_coupure: int, position: str)

    Exemple:
        Voyage 1: 6:00 → 6:30 (360 → 390)
        Voyage 2: 6:35 → 7:05 (395 → 425)  ← Écart de 5 min = OK
        Voyage 3: 14:00 → 14:30 (840 → 870) ← Écart de 7h35 = COUPURE !

    📝 EXERCICE : Changez seuil=90 en seuil=60 et voyez la différence
    """
    # Si il n'y a qu'un seul voyage, pas de coupure possible
    if len(heures_debut) <= 1:
        return False, 0, "Aucune"

    # Calculer tous les écarts entre fin d'un voyage et début du suivant
    ecarts = []
    for i in range(len(heures_fin) - 1):
        ecart = heures_debut[i+1] - heures_fin[i]
        ecarts.append(ecart)

        # 📝 Décommentez pour voir tous les écarts :
        # print(f"  Écart voyage {i+1} → {i+2} : {ecart} minutes")

    # Pas d'écart calculé ? Pas de coupure
    if not ecarts:
        return False, 0, "Aucune"

    # Trouver l'écart maximum
    max_ecart = max(ecarts)

    # Si l'écart max dépasse le seuil, c'est une coupure !
    if max_ecart > seuil:
        # Déterminer où se trouve la coupure
        position_idx = ecarts.index(max_ecart)

        if position_idx < len(ecarts) / 2:
            position = "DEBUT"  # Coupure dans la première moitié
        else:
            position = "FIN"    # Coupure dans la seconde moitié

        return True, max_ecart, position

    # Sinon, pas de coupure
    return False, 0, "Aucune"


def determiner_type(heure_debut, heure_fin, a_coupure, position_coupure):
    """
    Détermine le type de service selon des règles simples.

    Types possibles :
        - MATIN : Service qui finit avant 12h
        - APREM : Service qui commence après 12h
        - COUPE_DEBUT : Service avec coupure en début de journée
        - COUPE_FIN : Service avec coupure en fin de journée
        - JOURNEE : Service qui dure toute la journée

    📝 C'EST ICI QUE VOUS POUVEZ CHANGER LA DÉFINITION DES TYPES !
    """
    # Définir les seuils (en minutes depuis minuit)
    MIDI = 720  # 12h00

    # Si le service a une coupure, c'est soit COUPE_DEBUT soit COUPE_FIN
    if a_coupure:
        if position_coupure == "DEBUT":
            return "COUPE_DEBUT"
        else:
            return "COUPE_FIN"

    # Sinon, classifier selon les horaires
    if heure_fin <= MIDI:
        return "MATIN"
    elif heure_debut >= MIDI:
        return "APREM"
    else:
        return "JOURNEE"


# ============================================
# ÉTAPE 2 : CHARGER LES DONNÉES
# ============================================

def charger_donnees(fichier_excel):
    """
    Charge les données depuis Excel et les prépare pour l'analyse.

    📝 IMPORTANT : Adaptez cette fonction à VOTRE fichier Excel
    """
    print("📂 Chargement du fichier Excel...")

    # Lire le fichier Excel
    df = pd.read_excel(fichier_excel)

    print(f"✅ {len(df)} lignes chargées")
    print(f"📊 Colonnes détectées : {list(df.columns)}")

    # Renommer les colonnes avec des noms standards
    # 📝 MODIFIEZ CES NOMS SELON VOTRE FICHIER
    colonnes_standard = [
        "periode",
        "depot",
        "num_service",
        "num_ligne",
        "num_voyage",
        "sens",
        "arret_debut",
        "arret_fin",
        "heure_debut",
        "heure_fin",
        "num_voiture",
        "jours_semaine"
    ]

    if len(df.columns) >= len(colonnes_standard):
        df.columns = colonnes_standard + list(df.columns[len(colonnes_standard):])

    # Convertir les heures en minutes
    print("⏱️  Conversion des heures en minutes...")
    df['heure_debut_min'] = df['heure_debut'].apply(heure_to_minutes)
    df['heure_fin_min'] = df['heure_fin'].apply(heure_to_minutes)

    # Supprimer les lignes avec des heures invalides
    avant = len(df)
    df = df.dropna(subset=['num_service', 'heure_debut_min', 'heure_fin_min'])
    apres = len(df)

    if avant != apres:
        print(f"⚠️  {avant - apres} lignes supprimées (heures invalides)")

    print(f"✅ {len(df)} voyages valides")
    print(f"   {df['num_service'].nunique()} services uniques")

    return df


# ============================================
# ÉTAPE 3 : REGROUPER LES VOYAGES PAR SERVICE
# ============================================

def regrouper_services(df_voyages):
    """
    Transforme plusieurs lignes (voyages) en une seule ligne par service.

    Avant :
        Service S001 | Voyage 1 | 6:00 → 6:30
        Service S001 | Voyage 2 | 6:35 → 7:05
        Service S001 | Voyage 3 | 7:10 → 7:40

    Après :
        Service S001 | Début: 6:00 | Fin: 7:40 | Nb: 3 | Type: MATIN
    """
    print("\n🔄 Regroupement des voyages par service...")

    services = []

    # Boucle sur chaque service unique
    for num_service, groupe in df_voyages.groupby('num_service'):
        # Trier les voyages par heure de début
        groupe = groupe.sort_values('heure_debut_min')

        # Extraire toutes les heures
        heures_debut = groupe['heure_debut_min'].tolist()
        heures_fin = groupe['heure_fin_min'].tolist()

        # Calculer les caractéristiques du service
        heure_debut_service = min(heures_debut)  # Plus tôt
        heure_fin_service = max(heures_fin)      # Plus tard
        nb_voyages = len(groupe)

        # Détecter les coupures
        a_coupure, duree_coupure, position = detecter_coupure(
            heures_debut, heures_fin
        )

        # Calculer les durées
        duree_totale = heure_fin_service - heure_debut_service
        duree_travail = duree_totale - duree_coupure

        # Déterminer le type
        type_service = determiner_type(
            heure_debut_service, heure_fin_service,
            a_coupure, position
        )

        # Informations supplémentaires
        depot = groupe['depot'].iloc[0] if 'depot' in groupe.columns else "N/A"
        ligne = groupe['num_ligne'].mode()[0] if len(groupe) > 0 else "N/A"

        # Stocker tout ça
        services.append({
            'num_service': num_service,
            'type_service': type_service,
            'depot': depot,
            'ligne': ligne,
            'heure_debut': heure_debut_service,
            'heure_fin': heure_fin_service,
            'nb_voyages': nb_voyages,
            'duree_totale': duree_totale,
            'duree_coupure': duree_coupure,
            'duree_travail': duree_travail,
            'a_coupure': a_coupure,
        })

    # Convertir en DataFrame
    df_services = pd.DataFrame(services)

    print(f"✅ {len(df_services)} services créés")
    print("\n📊 Répartition par type :")
    print(df_services['type_service'].value_counts())

    return df_services


# ============================================
# ÉTAPE 4 : PRÉPARER LES DONNÉES POUR LE ML
# ============================================

def preparer_features(df_services):
    """
    Crée les "features" (caractéristiques) pour le Machine Learning.

    Une feature = une colonne que le modèle utilise pour apprendre.

    📝 VOUS POUVEZ AJOUTER VOS PROPRES FEATURES ICI !
    """
    print("\n🧮 Création des features...")

    # Features de base
    features = df_services[[
        'heure_debut', 'heure_fin', 'nb_voyages',
        'duree_totale', 'duree_coupure', 'duree_travail'
    ]].copy()

    # Features dérivées
    features['a_coupure'] = df_services['a_coupure'].astype(int)
    features['est_matin'] = (df_services['heure_debut'] < 480).astype(int)  # Avant 8h
    features['est_soir'] = (df_services['heure_fin'] > 1140).astype(int)   # Après 19h

    # 📝 EXERCICE : Ajoutez une feature "service_court" (< 6h)
    # features['service_court'] = ...

    # One-hot encoding pour depot et ligne
    depot_dummies = pd.get_dummies(df_services['depot'], prefix='depot')
    ligne_dummies = pd.get_dummies(df_services['ligne'], prefix='ligne')

    features = pd.concat([features, depot_dummies, ligne_dummies], axis=1)

    print(f"✅ {features.shape[1]} features créées")

    return features


# ============================================
# ÉTAPE 5 : ENTRAÎNER LE MODÈLE
# ============================================

def entrainer_modele(features, cible):
    """
    Entraîne le modèle de Machine Learning.

    📝 VOUS POUVEZ MODIFIER LES PARAMÈTRES ICI
    """
    print("\n🧠 Entraînement du modèle...")

    # Séparer en train (75%) et test (25%)
    X_train, X_test, y_train, y_test = train_test_split(
        features, cible,
        test_size=0.25,  # 25% pour le test
        random_state=42  # Pour avoir toujours les mêmes résultats
    )

    print(f"   Train : {len(X_train)} services")
    print(f"   Test : {len(X_test)} services")

    # Créer et entraîner le modèle
    # 📝 EXERCICE : Essayez de changer n_estimators ou max_depth
    modele = RandomForestClassifier(
        n_estimators=200,    # Nombre d'arbres
        max_depth=12,        # Profondeur max
        min_samples_leaf=2,  # Min d'échantillons par feuille
        random_state=42,
        n_jobs=-1
    )

    modele.fit(X_train, y_train)

    # Évaluer
    predictions = modele.predict(X_test)
    precision = (predictions == y_test).sum() / len(y_test)

    print(f"\n🎯 Précision : {precision:.1%}")

    # Afficher les erreurs
    print("\n📊 Détail par type :")
    for type_service in sorted(y_test.unique()):
        mask = y_test == type_service
        nb_total = mask.sum()
        nb_correct = (predictions[mask] == type_service).sum()
        taux = nb_correct / nb_total if nb_total > 0 else 0
        print(f"   {type_service:15s} : {nb_correct}/{nb_total} ({taux:.1%})")

    return modele, features.columns


# ============================================
# ÉTAPE 6 : PRÉDIRE UN NOUVEAU SERVICE
# ============================================

def predire_service(voyages, modele, colonnes_features, depot="N/A"):
    """
    Prédit le type d'un nouveau service.

    Args:
        voyages: Liste de dict avec 'heure_debut' et 'heure_fin'
        modele: Le modèle entraîné
        colonnes_features: Les colonnes attendues par le modèle
        depot: Le dépôt du service

    Example:
        voyages = [
            {"heure_debut": "6:00", "heure_fin": "6:35"},
            {"heure_debut": "6:40", "heure_fin": "7:15"},
        ]
        type_predit = predire_service(voyages, modele, colonnes)
    """
    # Convertir les heures en minutes
    heures_debut = [heure_to_minutes(v['heure_debut']) for v in voyages]
    heures_fin = [heure_to_minutes(v['heure_fin']) for v in voyages]

    # Retirer les None
    heures_debut = [h for h in heures_debut if h is not None]
    heures_fin = [h for h in heures_fin if h is not None]

    if not heures_debut:
        return None, {}

    # Calculer les caractéristiques
    heure_debut = min(heures_debut)
    heure_fin = max(heures_fin)
    nb_voyages = len(voyages)

    a_coupure, duree_coupure, _ = detecter_coupure(heures_debut, heures_fin)

    duree_totale = heure_fin - heure_debut
    duree_travail = duree_totale - duree_coupure

    # Créer le vecteur de features
    features_dict = {
        'heure_debut': heure_debut,
        'heure_fin': heure_fin,
        'nb_voyages': nb_voyages,
        'duree_totale': duree_totale,
        'duree_coupure': duree_coupure,
        'duree_travail': duree_travail,
        'a_coupure': 1 if a_coupure else 0,
        'est_matin': 1 if heure_debut < 480 else 0,
        'est_soir': 1 if heure_fin > 1140 else 0,
    }

    # Initialiser toutes les autres features à 0
    for col in colonnes_features:
        if col not in features_dict:
            features_dict[col] = 0

    # Activer la bonne colonne de dépôt
    depot_col = f"depot_{depot}"
    if depot_col in features_dict:
        features_dict[depot_col] = 1

    # Créer le DataFrame
    service_df = pd.DataFrame([features_dict])
    service_df = service_df[colonnes_features]

    # Prédire
    type_predit = modele.predict(service_df)[0]
    probas = modele.predict_proba(service_df)[0]
    probas_dict = dict(zip(modele.classes_, probas))

    return type_predit, probas_dict


# ============================================
# PROGRAMME PRINCIPAL
# ============================================

if __name__ == "__main__":
    print("=" * 80)
    print("🚌 SYSTÈME DE CLASSIFICATION DES SERVICES BUS - VERSION SIMPLIFIÉE")
    print("=" * 80)

    # 📝 MODIFIEZ CE CHEMIN AVEC VOTRE FICHIER
    fichier = "template_donnees_voyages_v2.xlsx"

    try:
        # ÉTAPE 1 : Charger les données
        df_voyages = charger_donnees(fichier)

        # ÉTAPE 2 : Regrouper par service
        df_services = regrouper_services(df_voyages)

        # ÉTAPE 3 : Préparer les features
        features = preparer_features(df_services)
        cible = df_services['type_service']

        # ÉTAPE 4 : Entraîner le modèle
        modele, colonnes = entrainer_modele(features, cible)

        # ÉTAPE 5 : Tester une prédiction
        print("\n" + "=" * 80)
        print("🔮 TEST DE PRÉDICTION")
        print("=" * 80)

        test_voyages = [
            {"heure_debut": "6:00", "heure_fin": "6:35"},
            {"heure_debut": "6:40", "heure_fin": "7:15"},
            {"heure_debut": "7:20", "heure_fin": "7:55"},
            {"heure_debut": "8:00", "heure_fin": "8:35"},
        ]

        type_p, probas = predire_service(test_voyages, modele, colonnes, depot="DEPOT_A")

        print(f"\n✅ Type prédit : {type_p}")
        print(f"   Confiance : {max(probas.values()):.1%}")
        print(f"\n📊 Probabilités :")
        for type_s, prob in sorted(probas.items(), key=lambda x: -x[1]):
            print(f"   {type_s:15s} : {prob:.1%}")

        print("\n" + "=" * 80)
        print("✨ Script terminé avec succès !")
        print("=" * 80)

    except FileNotFoundError:
        print(f"\n❌ ERREUR : Fichier '{fichier}' introuvable")
        print("📝 Vérifiez le chemin ou générez des données d'exemple")

    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()