"""
=============================================================================
🚌 EXERCICE : Apprendre le Random Forest avec un cas de transport bus
=============================================================================

Objectif : Entraîner une IA à prédire quel bus doit effectuer un voyage,
           en se basant sur des données historiques simulées.

Niveau : Débutant en Machine Learning
Prérequis : Bases Python (variables, fonctions, boucles)

🎯 Ce que tu vas apprendre :
   1. Préparer des données pour le ML
   2. Entraîner un modèle Random Forest
   3. Évaluer ses performances
   4. Faire des prédictions sur de nouveaux voyages

Instructions : Lis le code, complète les parties marquées "À TOI DE JOUER"
               puis exécute le script pour voir les résultats.
=============================================================================
"""

# =============================================
# PARTIE 1 : LES IMPORTS
# =============================================
# On importe les bibliothèques nécessaires
# Pour installer si besoin : pip install pandas scikit-learn

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

print("✅ Bibliothèques importées avec succès !\n")


# =============================================
# PARTIE 2 : CRÉER DES DONNÉES SIMULÉES
# =============================================
# On simule des plannings historiques de 5 bus sur plusieurs jours
# Dans ton vrai projet, tu remplaceras ça par tes fichiers Excel

np.random.seed(42)  # Pour avoir des résultats reproductibles

def generer_donnees(n_jours=30):
    """
    Génère des données de voyages simulées.
    Chaque voyage a :
    - une heure de départ (en minutes depuis minuit)
    - une ligne (L1, L2, L3)
    - un terminus de départ (A, B, C, D)
    - un terminus d'arrivée
    - un bus attribué (Bus_1 à Bus_5) -> c'est ce qu'on veut prédire !
    """
    voyages = []

    lignes = ["L1", "L2", "L3"]
    terminus = ["A", "B", "C", "D"]

    for jour in range(n_jours):
        for heure_depart in range(360, 1320, 15):  # de 6h à 22h toutes les 15 min
            # On ne crée pas un voyage à chaque créneau (aléatoire)
            if np.random.random() > 0.3:
                continue

            ligne = np.random.choice(lignes)
            origine = np.random.choice(terminus)
            destination = np.random.choice([t for t in terminus if t != origine])
            duree = np.random.randint(20, 60)  # durée du voyage en minutes

            # ---- Logique d'attribution simulée ----
            # On simule des RÈGLES que le modèle devra apprendre :
            # - Bus_1 et Bus_2 font surtout la ligne L1
            # - Bus_3 fait surtout la ligne L2
            # - Bus_4 et Bus_5 font surtout la ligne L3
            # - Le matin (avant 12h) : plutôt Bus_1, Bus_3, Bus_4
            # - L'après-midi : plutôt Bus_2, Bus_5

            if ligne == "L1":
                if heure_depart < 720:
                    bus = np.random.choice(["Bus_1", "Bus_1", "Bus_1", "Bus_2"])
                else:
                    bus = np.random.choice(["Bus_2", "Bus_2", "Bus_2", "Bus_1"])
            elif ligne == "L2":
                bus = np.random.choice(["Bus_3", "Bus_3", "Bus_3", "Bus_4"])
            else:
                if heure_depart < 720:
                    bus = np.random.choice(["Bus_4", "Bus_4", "Bus_4", "Bus_5"])
                else:
                    bus = np.random.choice(["Bus_5", "Bus_5", "Bus_5", "Bus_4"])

            voyages.append({
                "jour": jour,
                "heure_depart": heure_depart,
                "heure_arrivee": heure_depart + duree,
                "ligne": ligne,
                "origine": origine,
                "destination": destination,
                "duree": duree,
                "bus": bus  # <- C'est la colonne cible !
            })

    return pd.DataFrame(voyages)


# Générons les données
df = generer_donnees(n_jours=30)
print(f"📊 Données générées : {len(df)} voyages sur 30 jours")
print(f"   Colonnes : {list(df.columns)}")
print(f"\n🔍 Aperçu des 5 premières lignes :")
print(df.head().to_string())
print()


# =============================================
# PARTIE 3 : PRÉPARER LES DONNÉES (FEATURES)
# =============================================
# Le Random Forest ne comprend que les chiffres !
# Il faut convertir les textes (ligne, terminus) en nombres.
# On appelle ça "l'encodage des features"

print("=" * 50)
print("📐 PARTIE 3 : Préparation des features")
print("=" * 50)

# On utilise pd.get_dummies() pour transformer les catégories en colonnes 0/1
# Exemple : la colonne "ligne" avec valeurs L1, L2, L3
#           devient 3 colonnes : ligne_L1(0/1), ligne_L2(0/1), ligne_L3(0/1)

# --- À TOI DE JOUER (Exercice 1) ---
# Crée la variable 'features' en utilisant pd.get_dummies()
# sur les colonnes : ligne, origine, destination
# Puis ajoute les colonnes numériques : heure_depart, duree
#
# Indice : pd.get_dummies(df[["colonne1", "colonne2"]])
# Pour ajouter des colonnes : features["nom"] = df["nom"]

# 💡 DÉCOMMENTE ET COMPLÈTE LE CODE CI-DESSOUS :

# features = pd.get_dummies(df[[???]])
# features["heure_depart"] = ???
# features["duree"] = ???

# ---- SOLUTION (enlève les commentaires quand tu veux vérifier) ----
features = pd.get_dummies(df[["ligne", "origine", "destination"]])
features["heure_depart"] = df["heure_depart"]
features["duree"] = df["duree"]
# ---- FIN SOLUTION ----

# La cible (ce qu'on veut prédire)
cible = df["bus"]

print(f"\n✅ Features créées : {features.shape[1]} colonnes")
print(f"   Colonnes : {list(features.columns)}")
print(f"   Cible : {cible.nunique()} bus différents ({list(cible.unique())})")
print()


# =============================================
# PARTIE 4 : SÉPARER DONNÉES TRAIN / TEST
# =============================================
# Règle d'or du ML : on n'évalue JAMAIS un modèle sur les données
# qui ont servi à l'entraîner ! On garde 20% des données pour tester.

print("=" * 50)
print("🔀 PARTIE 4 : Séparation train / test")
print("=" * 50)

# --- À TOI DE JOUER (Exercice 2) ---
# Utilise train_test_split pour séparer les données
# avec test_size=0.2 (20% pour le test)
# et random_state=42 (pour la reproductibilité)
#
# Indice : X_train, X_test, y_train, y_test = train_test_split(???, ???, test_size=???)

# 💡 DÉCOMMENTE ET COMPLÈTE :

# X_train, X_test, y_train, y_test = train_test_split(???, ???, test_size=0.2, random_state=42)

# ---- SOLUTION ----
X_train, X_test, y_train, y_test = train_test_split(
    features, cible, test_size=0.2, random_state=42
)
# ---- FIN SOLUTION ----

print(f"   Données d'entraînement : {len(X_train)} voyages")
print(f"   Données de test :        {len(X_test)} voyages")
print()


# =============================================
# PARTIE 5 : ENTRAÎNER LE MODÈLE 🚀
# =============================================

print("=" * 50)
print("🧠 PARTIE 5 : Entraînement du Random Forest")
print("=" * 50)

# --- À TOI DE JOUER (Exercice 3) ---
# Crée un RandomForestClassifier avec :
#   - n_estimators=100 (nombre d'arbres dans la forêt)
#   - random_state=42
# Puis entraîne-le avec .fit(X_train, y_train)
#
# Indice :
# modele = RandomForestClassifier(n_estimators=???, random_state=???)
# modele.fit(???, ???)

# 💡 DÉCOMMENTE ET COMPLÈTE :

# modele = RandomForestClassifier(n_estimators=???, random_state=???)
# modele.???(X_train, y_train)

# ---- SOLUTION ----
modele = RandomForestClassifier(n_estimators=100, random_state=42)
modele.fit(X_train, y_train)
# ---- FIN SOLUTION ----

print("✅ Modèle entraîné !")
print(f"   Nombre d'arbres : {modele.n_estimators}")
print()


# =============================================
# PARTIE 6 : ÉVALUER LE MODÈLE
# =============================================

print("=" * 50)
print("📈 PARTIE 6 : Évaluation")
print("=" * 50)

# On fait des prédictions sur les données de TEST
predictions = modele.predict(X_test)

# Calcul de la précision
precision = accuracy_score(y_test, predictions)
print(f"\n🎯 Précision du modèle : {precision:.1%}")
print(f"   (Le modèle attribue le bon bus {precision:.1%} du temps)\n")

# Rapport détaillé par bus
print("📋 Détail par bus :")
print(classification_report(y_test, predictions))


# =============================================
# PARTIE 7 : COMPRENDRE LE MODÈLE
# =============================================
# Le Random Forest nous dit quelles features sont les plus importantes
# pour prendre sa décision. C'est un gros avantage de ce modèle !

print("=" * 50)
print("🔍 PARTIE 7 : Quelles features sont les plus importantes ?")
print("=" * 50)

importances = pd.Series(
    modele.feature_importances_,
    index=features.columns
).sort_values(ascending=False)

print("\nImportance des features (de la plus importante à la moins importante) :")
for feature, importance in importances.items():
    barre = "█" * int(importance * 50)
    print(f"   {feature:20s} : {importance:.3f} {barre}")


# =============================================
# PARTIE 8 : FAIRE UNE PRÉDICTION 🔮
# =============================================

print("\n" + "=" * 50)
print("🔮 PARTIE 8 : Prédire un nouveau voyage")
print("=" * 50)

# --- À TOI DE JOUER (Exercice 4) ---
# Crée un nouveau voyage et demande au modèle de prédire le bus !
# Modifie les valeurs ci-dessous pour tester différents scénarios :

nouveau_voyage = {
    "ligne": "L1",           # Essaie : L1, L2, L3
    "origine": "A",          # Essaie : A, B, C, D
    "destination": "B",      # Essaie : A, B, C, D (différent de origine)
    "heure_depart": 480,     # En minutes (480 = 8h00, 840 = 14h00)
    "duree": 35              # Durée en minutes
}

# Préparation du voyage (même format que les données d'entraînement)
voyage_df = pd.DataFrame([nouveau_voyage])
voyage_features = pd.get_dummies(voyage_df[["ligne", "origine", "destination"]])
voyage_features["heure_depart"] = voyage_df["heure_depart"]
voyage_features["duree"] = voyage_df["duree"]

# Assurer que toutes les colonnes sont présentes (même ordre)
for col in features.columns:
    if col not in voyage_features.columns:
        voyage_features[col] = 0
voyage_features = voyage_features[features.columns]

# Prédiction
bus_predit = modele.predict(voyage_features)[0]
probabilites = modele.predict_proba(voyage_features)[0]

heure_str = f"{nouveau_voyage['heure_depart'] // 60}h{nouveau_voyage['heure_depart'] % 60:02d}"
print(f"\n📌 Nouveau voyage :")
print(f"   Ligne {nouveau_voyage['ligne']} | {nouveau_voyage['origine']} → {nouveau_voyage['destination']}")
print(f"   Départ : {heure_str} | Durée : {nouveau_voyage['duree']} min")
print(f"\n🚌 Bus recommandé : {bus_predit}")
print(f"\n   Probabilités par bus :")
for bus, proba in zip(modele.classes_, probabilites):
    barre = "█" * int(proba * 30)
    print(f"   {bus} : {proba:.1%} {barre}")


# =============================================
# 🎓 EXERCICES BONUS
# =============================================
print("\n" + "=" * 50)
print("🎓 EXERCICES BONUS POUR ALLER PLUS LOIN")
print("=" * 50)
print("""
1. MODIFIER LES PARAMÈTRES DU MODÈLE
   - Change n_estimators (50, 200, 500) et observe l'impact sur la précision
   - Ajoute max_depth=10 pour limiter la profondeur des arbres
   - Ajoute min_samples_leaf=5

2. AJOUTER DES FEATURES
   - Crée une feature "est_matin" (1 si heure < 720, 0 sinon)
   - Crée une feature "heure_arrivee" = heure_depart + duree
   - Observe si la précision s'améliore

3. TESTER AVEC TES VRAIES DONNÉES
   - Remplace generer_donnees() par :
     df = pd.read_excel("ton_fichier.xlsx")
   - Adapte les noms de colonnes
   - Lance l'entraînement sur tes données réelles !

4. COMPARER AVEC UN AUTRE MODÈLE
   - Remplace RandomForestClassifier par :
     from sklearn.ensemble import GradientBoostingClassifier
   - Compare les précisions

💡 Astuce : Pour chaque exercice, change UNE SEULE chose à la fois
   et observe l'impact. C'est comme ça qu'on apprend le mieux !
""")