"""
=============================================================================
🚌 SYSTÈME DE RÉPARTITION INTELLIGENTE DES SERVICES BUS
=============================================================================

Objectif : Apprendre la logique de répartition des voyages en services,
           puis créer automatiquement de nouveaux services quand on modifie
           les lignes ou les horaires.

Types de services gérés :
   • MATIN : Service du matin (ex: 5h-13h)
   • APREM : Service d'après-midi (ex: 13h-21h)
   • COUPE_DEBUT : Service coupé en début de journée (ex: 6h-10h puis 14h-18h)
   • COUPE_FIN : Service coupé en fin de journée (ex: 10h-14h puis 18h-22h)

=============================================================================
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

print("=" * 80)
print("🚌 SYSTÈME DE RÉPARTITION INTELLIGENTE DES SERVICES BUS")
print("=" * 80)


# =============================================
# PARTIE 1 : GÉNÉRATION DE DONNÉES D'EXEMPLE
# =============================================
# (À remplacer par vos vraies données Excel)

def generer_services_exemple():
    """
    Génère des services d'exemple avec différents types.
    Dans votre cas, remplacez ceci par : pd.read_excel("vos_services.xlsx")
    """
    np.random.seed(42)
    services = []

    for service_id in range(200):  # 200 services historiques
        type_service = np.random.choice([
            "MATIN", "APREM", "COUPE_DEBUT", "COUPE_FIN"
        ], p=[0.35, 0.35, 0.15, 0.15])

        ligne = np.random.choice(["L1", "L2", "L3", "L4"])

        # Générer les caractéristiques selon le type
        if type_service == "MATIN":
            heure_debut = np.random.randint(300, 420)  # 5h-7h
            heure_fin = np.random.randint(720, 840)  # 12h-14h
            nb_voyages = np.random.randint(8, 15)
            duree_coupure = 0

        elif type_service == "APREM":
            heure_debut = np.random.randint(720, 840)  # 12h-14h
            heure_fin = np.random.randint(1200, 1320)  # 20h-22h
            nb_voyages = np.random.randint(8, 15)
            duree_coupure = 0

        elif type_service == "COUPE_DEBUT":
            heure_debut = np.random.randint(330, 420)  # 5h30-7h
            heure_fin = np.random.randint(1050, 1150)  # 17h30-19h10
            nb_voyages = np.random.randint(12, 18)
            duree_coupure = np.random.randint(180, 300)  # 3h-5h de coupure

        else:  # COUPE_FIN
            heure_debut = np.random.randint(570, 660)  # 9h30-11h
            heure_fin = np.random.randint(1260, 1350)  # 21h-22h30
            nb_voyages = np.random.randint(12, 18)
            duree_coupure = np.random.randint(180, 300)

        duree_totale = heure_fin - heure_debut
        duree_travail = duree_totale - duree_coupure

        services.append({
            "service_id": f"S{service_id:03d}",
            "type_service": type_service,
            "ligne": ligne,
            "heure_debut": heure_debut,
            "heure_fin": heure_fin,
            "nb_voyages": nb_voyages,
            "duree_totale": duree_totale,
            "duree_coupure": duree_coupure,
            "duree_travail": duree_travail,
        })

    return pd.DataFrame(services)


def minutes_vers_heure(minutes):
    """Convertit des minutes depuis minuit en format HHhMM"""
    h = minutes // 60
    m = minutes % 60
    return f"{h}h{m:02d}"


# =============================================
# PARTIE 2 : CHARGER ET ANALYSER LES DONNÉES
# =============================================
print("\n📊 PARTIE 1 : Chargement des données")
print("=" * 80)

# 🔧 POUR UTILISER VOS DONNÉES RÉELLES, DÉCOMMENTEZ ET ADAPTEZ :
# df = pd.read_excel("vos_services.xlsx")
# Colonnes attendues : service_id, type_service, ligne, heure_debut, heure_fin,
#                      nb_voyages, duree_coupure

df = generer_services_exemple()

print(f"✅ {len(df)} services chargés")
print(f"\n📋 Types de services :")
print(df["type_service"].value_counts())
print(f"\n🔍 Aperçu des premières lignes :")
print(df.head(10).to_string())

# =============================================
# PARTIE 3 : CRÉER LES FEATURES INTELLIGENTES
# =============================================
print("\n\n📐 PARTIE 2 : Création des features")
print("=" * 80)

# Calculer des features dérivées
df["duree_travail"] = df["duree_totale"] - df["duree_coupure"]
df["a_coupure"] = (df["duree_coupure"] > 0).astype(int)
df["est_matin"] = (df["heure_debut"] < 480).astype(int)  # Commence avant 8h
df["est_soir"] = (df["heure_fin"] > 1140).astype(int)  # Finit après 19h
df["voyages_par_heure"] = df["nb_voyages"] / (df["duree_travail"] / 60)

# Créer les features pour le ML
features_numeriques = [
    "heure_debut", "heure_fin", "nb_voyages", "duree_totale",
    "duree_coupure", "duree_travail", "a_coupure",
    "est_matin", "est_soir", "voyages_par_heure"
]

# One-hot encoding pour la ligne
features = pd.get_dummies(df[["ligne"]], prefix="ligne")
features = pd.concat([features, df[features_numeriques]], axis=1)

print(f"✅ {features.shape[1]} features créées :")
print(f"   {list(features.columns)}")

cible = df["type_service"]

# =============================================
# PARTIE 4 : ENTRAÎNER LE MODÈLE
# =============================================
print("\n\n🧠 PARTIE 3 : Entraînement du modèle")
print("=" * 80)

X_train, X_test, y_train, y_test = train_test_split(
    features, cible, test_size=0.25, random_state=42, stratify=cible
)

modele = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_leaf=3,
    random_state=42
)
modele.fit(X_train, y_train)

print(f"✅ Modèle entraîné avec {modele.n_estimators} arbres")

# Évaluation
predictions = modele.predict(X_test)
precision = (predictions == y_test).sum() / len(y_test)

print(f"\n🎯 Précision globale : {precision:.1%}")
print(f"\n📊 Rapport détaillé par type de service :")
print(classification_report(y_test, predictions))

# =============================================
# PARTIE 5 : IMPORTANCE DES FEATURES
# =============================================
print("\n" + "=" * 80)
print("🔍 PARTIE 4 : Quelles caractéristiques sont les plus importantes ?")
print("=" * 80)

importances = pd.DataFrame({
    "feature": features.columns,
    "importance": modele.feature_importances_
}).sort_values("importance", ascending=False)

print("\n📊 Top 10 des features les plus importantes :")
for i, row in importances.head(10).iterrows():
    barre = "█" * int(row["importance"] * 100)
    print(f"   {row['feature']:25s} : {row['importance']:.3f} {barre}")

# =============================================
# PARTIE 6 : MATRICE DE CONFUSION
# =============================================
print("\n\n📊 PARTIE 5 : Matrice de confusion")
print("=" * 80)

cm = confusion_matrix(y_test, predictions, labels=modele.classes_)
cm_df = pd.DataFrame(
    cm,
    index=[f"Vrai: {c}" for c in modele.classes_],
    columns=[f"Prédit: {c}" for c in modele.classes_]
)

plt.figure(figsize=(10, 8))
sns.heatmap(cm_df, annot=True, fmt="d", cmap="Blues", cbar_kws={"label": "Nombre"})
plt.title("Matrice de confusion — Classification des services\n", fontsize=14, fontweight="bold")
plt.ylabel("Type réel")
plt.xlabel("Type prédit")
plt.tight_layout()
plt.savefig("confusion_matrix_services.png", dpi=150)
print("✅ Matrice de confusion sauvegardée : confusion_matrix_services.png")

# =============================================
# PARTIE 7 : PRÉDIRE DE NOUVEAUX SERVICES
# =============================================
print("\n\n" + "=" * 80)
print("🔮 PARTIE 6 : Créer automatiquement de nouveaux services")
print("=" * 80)


def predire_type_service(voyages_info):
    """
    Prédit le type de service optimal pour un ensemble de voyages.

    Args:
        voyages_info: dict avec clés:
            - ligne: str
            - heure_debut: int (minutes depuis minuit)
            - heure_fin: int
            - nb_voyages: int
            - duree_coupure: int (0 si service d'affilée)

    Returns:
        type_service, probabilites
    """
    # Calculer les features
    duree_totale = voyages_info["heure_fin"] - voyages_info["heure_debut"]
    duree_travail = duree_totale - voyages_info["duree_coupure"]

    features_dict = {
        "heure_debut": voyages_info["heure_debut"],
        "heure_fin": voyages_info["heure_fin"],
        "nb_voyages": voyages_info["nb_voyages"],
        "duree_totale": duree_totale,
        "duree_coupure": voyages_info["duree_coupure"],
        "duree_travail": duree_travail,
        "a_coupure": 1 if voyages_info["duree_coupure"] > 0 else 0,
        "est_matin": 1 if voyages_info["heure_debut"] < 480 else 0,
        "est_soir": 1 if voyages_info["heure_fin"] > 1140 else 0,
        "voyages_par_heure": voyages_info["nb_voyages"] / (duree_travail / 60),
    }

    # One-hot encoding pour la ligne
    for ligne in ["L1", "L2", "L3", "L4"]:
        features_dict[f"ligne_{ligne}"] = 1 if voyages_info["ligne"] == ligne else 0

    # Créer le DataFrame avec les bonnes colonnes
    voyage_features = pd.DataFrame([features_dict])
    voyage_features = voyage_features[features.columns]

    # Prédiction
    type_predit = modele.predict(voyage_features)[0]
    probas = modele.predict_proba(voyage_features)[0]
    probas_dict = dict(zip(modele.classes_, probas))

    return type_predit, probas_dict


# 🔧 EXEMPLES DE NOUVEAUX SERVICES À CRÉER
# Modifiez ces valeurs pour tester vos propres scénarios !

nouveaux_services = [
    {
        "ligne": "L1",
        "heure_debut": 360,  # 6h00
        "heure_fin": 780,  # 13h00
        "nb_voyages": 12,
        "duree_coupure": 0,
    },
    {
        "ligne": "L2",
        "heure_debut": 780,  # 13h00
        "heure_fin": 1260,  # 21h00
        "nb_voyages": 14,
        "duree_coupure": 0,
    },
    {
        "ligne": "L3",
        "heure_debut": 390,  # 6h30
        "heure_fin": 1140,  # 19h00
        "nb_voyages": 16,
        "duree_coupure": 240,  # 4h de coupure
    },
    {
        "ligne": "L1",
        "heure_debut": 600,  # 10h00
        "heure_fin": 1320,  # 22h00
        "nb_voyages": 15,
        "duree_coupure": 210,  # 3h30 de coupure
    },
    {
        "ligne": "L4",
        "heure_debut": 330,  # 5h30
        "heure_fin": 750,  # 12h30
        "nb_voyages": 10,
        "duree_coupure": 0,
    },
]

print(f"\n📋 Prédiction pour {len(nouveaux_services)} nouveaux services :\n")
print(f"{'#':<3} {'Ligne':<7} {'Horaire':<20} {'Voyages':<9} {'Coupure':<10} {'→ Type prédit':<18} {'Confiance'}")
print("─" * 90)

resultats = []
for i, service in enumerate(nouveaux_services):
    type_predit, probas = predire_type_service(service)

    horaire = f"{minutes_vers_heure(service['heure_debut'])} - {minutes_vers_heure(service['heure_fin'])}"
    coupure_str = f"{service['duree_coupure'] // 60}h{service['duree_coupure'] % 60:02d}" if service[
                                                                                                 "duree_coupure"] > 0 else "Non"
    confiance = max(probas.values())

    print(
        f"{i + 1:<3} {service['ligne']:<7} {horaire:<20} {service['nb_voyages']:<9} {coupure_str:<10} → {type_predit:<16} {confiance:.0%}")

    resultats.append({
        **service,
        "type_predit": type_predit,
        "confiance": confiance,
        "probas": probas
    })

# Détail des probabilités
print(f"\n\n📊 Détail des probabilités pour chaque service :")
print("=" * 80)
for i, res in enumerate(resultats):
    print(
        f"\n🚌 Service #{i + 1} : {res['ligne']} — {minutes_vers_heure(res['heure_debut'])} à {minutes_vers_heure(res['heure_fin'])}")
    print(f"   Type prédit : {res['type_predit']} (confiance : {res['confiance']:.0%})")
    print(f"   Probabilités détaillées :")
    for type_s, proba in sorted(res['probas'].items(), key=lambda x: -x[1]):
        barre = "█" * int(proba * 30)
        print(f"      {type_s:15s} : {proba:5.1%} {barre}")

# =============================================
# PARTIE 8 : OPTIMISATION GLOBALE
# =============================================
print("\n\n" + "=" * 80)
print("🎯 PARTIE 7 : Optimisation de la répartition")
print("=" * 80)


def generer_repartition_optimale(voyages_df, contraintes=None):
    """
    Génère une répartition optimale des voyages en services.

    Args:
        voyages_df: DataFrame avec colonnes [ligne, heure_depart, heure_arrivee]
        contraintes: dict avec:
            - max_duree_service: int (en minutes, ex: 540 pour 9h)
            - min_voyages_par_service: int
            - max_voyages_par_service: int

    Returns:
        Liste de services proposés
    """
    if contraintes is None:
        contraintes = {
            "max_duree_service": 540,  # 9h max
            "min_voyages_par_service": 6,
            "max_voyages_par_service": 18,
        }

    # Trier par heure de départ
    voyages = voyages_df.sort_values("heure_depart").reset_index(drop=True)

    services_proposes = []
    service_actuel = {
        "voyages": [],
        "ligne": None,
        "heure_debut": None,
        "heure_fin": None,
    }

    for idx, voyage in voyages.iterrows():
        # Premier voyage du service
        if not service_actuel["voyages"]:
            service_actuel["voyages"].append(voyage)
            service_actuel["ligne"] = voyage["ligne"]
            service_actuel["heure_debut"] = voyage["heure_depart"]
            service_actuel["heure_fin"] = voyage["heure_arrivee"]
            continue

        # Vérifier si on peut ajouter ce voyage au service actuel
        duree_service = voyage["heure_arrivee"] - service_actuel["heure_debut"]
        nb_voyages = len(service_actuel["voyages"])

        # Conditions pour ajouter au service actuel
        peut_ajouter = (
                voyage["ligne"] == service_actuel["ligne"]
                and duree_service <= contraintes["max_duree_service"]
                and nb_voyages < contraintes["max_voyages_par_service"]
        )

        if peut_ajouter:
            service_actuel["voyages"].append(voyage)
            service_actuel["heure_fin"] = voyage["heure_arrivee"]
        else:
            # Finaliser le service actuel
            if len(service_actuel["voyages"]) >= contraintes["min_voyages_par_service"]:
                services_proposes.append(service_actuel.copy())

            # Commencer un nouveau service
            service_actuel = {
                "voyages": [voyage],
                "ligne": voyage["ligne"],
                "heure_debut": voyage["heure_depart"],
                "heure_fin": voyage["heure_arrivee"],
            }

    # Ajouter le dernier service
    if len(service_actuel["voyages"]) >= contraintes["min_voyages_par_service"]:
        services_proposes.append(service_actuel)

    # Prédire les types de services
    for service in services_proposes:
        nb_voyages = len(service["voyages"])
        heure_debut = service["heure_debut"]
        heure_fin = service["heure_fin"]

        # Détecter automatiquement les coupures potentielles
        temps_entre_voyages = []
        for i in range(len(service["voyages"]) - 1):
            ecart = service["voyages"][i + 1]["heure_depart"] - service["voyages"][i]["heure_arrivee"]
            temps_entre_voyages.append(ecart)

        # Si un écart > 2h, c'est probablement une coupure
        duree_coupure = max(temps_entre_voyages) if temps_entre_voyages and max(temps_entre_voyages) > 120 else 0

        type_predit, probas = predire_type_service({
            "ligne": service["ligne"],
            "heure_debut": heure_debut,
            "heure_fin": heure_fin,
            "nb_voyages": nb_voyages,
            "duree_coupure": duree_coupure,
        })

        service["type_predit"] = type_predit
        service["duree_coupure"] = duree_coupure
        service["probas"] = probas

    return services_proposes


# Exemple d'utilisation
print("\n💡 Exemple : Générer automatiquement des services à partir d'une liste de voyages")
print("=" * 80)

# Créer des voyages d'exemple pour la ligne L1
voyages_exemple = pd.DataFrame([
    {"ligne": "L1", "heure_depart": 360, "heure_arrivee": 395},  # 6h-6h35
    {"ligne": "L1", "heure_depart": 400, "heure_arrivee": 435},  # 6h40-7h15
    {"ligne": "L1", "heure_depart": 440, "heure_arrivee": 475},  # 7h20-7h55
    {"ligne": "L1", "heure_depart": 480, "heure_arrivee": 515},  # 8h-8h35
    {"ligne": "L1", "heure_depart": 520, "heure_arrivee": 555},  # 8h40-9h15
    {"ligne": "L1", "heure_depart": 560, "heure_arrivee": 595},  # 9h20-9h55
    {"ligne": "L1", "heure_depart": 600, "heure_arrivee": 635},  # 10h-10h35
    {"ligne": "L1", "heure_depart": 640, "heure_arrivee": 675},  # 10h40-11h15
    {"ligne": "L1", "heure_depart": 780, "heure_arrivee": 815},  # 13h-13h35
    {"ligne": "L1", "heure_depart": 820, "heure_arrivee": 855},  # 13h40-14h15
    {"ligne": "L1", "heure_depart": 860, "heure_arrivee": 895},  # 14h20-14h55
    {"ligne": "L1", "heure_depart": 900, "heure_arrivee": 935},  # 15h-15h35
    {"ligne": "L1", "heure_depart": 1200, "heure_arrivee": 1235},  # 20h-20h35
    {"ligne": "L1", "heure_depart": 1240, "heure_arrivee": 1275},  # 20h40-21h15
    {"ligne": "L1", "heure_depart": 1280, "heure_arrivee": 1315},  # 21h20-21h55
])

services_generes = generer_repartition_optimale(voyages_exemple)

print(f"\n✅ {len(services_generes)} services générés automatiquement :\n")
for i, service in enumerate(services_generes):
    print(f"\n🚌 Service #{i + 1} — Type : {service['type_predit']}")
    print(f"   Ligne : {service['ligne']}")
    print(f"   Horaire : {minutes_vers_heure(service['heure_debut'])} → {minutes_vers_heure(service['heure_fin'])}")
    print(f"   Nombre de voyages : {len(service['voyages'])}")
    if service["duree_coupure"] > 0:
        print(f"   ⚠️  Coupure détectée : {service['duree_coupure'] // 60}h{service['duree_coupure'] % 60:02d}")
    print(f"   Confiance : {max(service['probas'].values()):.0%}")

# =============================================
# PARTIE 9 : SAUVEGARDER LE MODÈLE
# =============================================
print("\n\n" + "=" * 80)
print("💾 PARTIE 8 : Sauvegarde du modèle")
print("=" * 80)

import pickle

# Sauvegarder le modèle et les colonnes
with open("modele_services_bus.pkl", "wb") as f:
    pickle.dump({
        "modele": modele,
        "colonnes": list(features.columns),
        "classes": list(modele.classes_)
    }, f)

print("✅ Modèle sauvegardé : modele_services_bus.pkl")
print("\n💡 Pour le réutiliser plus tard :")
print("""
    import pickle
    with open("modele_services_bus.pkl", "rb") as f:
        donnees = pickle.load(f)
        modele = donnees["modele"]
        colonnes = donnees["colonnes"]
""")

# =============================================
# RÉSUMÉ ET PROCHAINES ÉTAPES
# =============================================
print("\n\n" + "=" * 80)
print("🎓 RÉSUMÉ ET PROCHAINES ÉTAPES")
print("=" * 80)
print("""
✅ Ce que fait ce système :
   1. Analyse vos services existants et apprend les règles de répartition
   2. Prédit automatiquement le type de service (matin, après-midi, coupé)
   3. Génère de nouveaux services quand vous modifiez les horaires
   4. Optimise la répartition des voyages selon vos contraintes

📋 Pour l'utiliser avec vos vraies données :

   1. PRÉPARER VOS DONNÉES EXCEL :
      Colonnes nécessaires :
      - service_id : identifiant du service
      - type_service : MATIN, APREM, COUPE_DEBUT, COUPE_FIN
      - ligne : nom de la ligne (L1, L2, etc.)
      - heure_debut : heure de début en minutes (ex: 360 pour 6h00)
      - heure_fin : heure de fin en minutes
      - nb_voyages : nombre de voyages du service
      - duree_coupure : durée de coupure en minutes (0 si aucune)

   2. CHARGER VOS DONNÉES :
      Remplacez ligne 80 par :
      df = pd.read_excel("vos_services.xlsx")

   3. ADAPTER LES TYPES DE SERVICES :
      Si vos noms sont différents, modifiez la ligne 269 :
      type_service = np.random.choice(["VOS_TYPES_ICI"])

   4. TESTER :
      Lancez le script et vérifiez la précision du modèle

🚀 FONCTIONNALITÉS AVANCÉES :

   1. PRÉDIRE UN NOUVEAU SERVICE :
      type_predit, probas = predire_type_service({
          "ligne": "L1",
          "heure_debut": 360,
          "heure_fin": 780,
          "nb_voyages": 12,
          "duree_coupure": 0
      })

   2. GÉNÉRER AUTOMATIQUEMENT DES SERVICES :
      voyages = pd.read_excel("nouveaux_voyages.xlsx")
      services = generer_repartition_optimale(voyages)

   3. PERSONNALISER LES CONTRAINTES :
      services = generer_repartition_optimale(voyages, contraintes={
          "max_duree_service": 600,  # 10h max
          "min_voyages_par_service": 8,
          "max_voyages_par_service": 20,
      })

📧 Questions ? Besoin d'aide pour l'adapter à votre cas ?
   N'hésitez pas à me contacter !
""")

print("\n" + "=" * 80)
print("✨ Fin du script — Modèle prêt à l'emploi !")
print("=" * 80)