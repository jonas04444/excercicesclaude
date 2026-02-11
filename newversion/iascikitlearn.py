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
   5. Tracer une courbe d'apprentissage (learning curve)

Instructions : Lis le code, complète les parties marquées "À TOI DE JOUER"
               puis exécute le script pour voir les résultats.
=============================================================================
"""

# =============================================
# PARTIE 1 : LES IMPORTS
# =============================================
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, learning_curve
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt

print("✅ Bibliothèques importées avec succès !\n")


# =============================================
# PARTIE 2 : CRÉER DES DONNÉES SIMULÉES
# =============================================
# On simule des plannings historiques de 5 bus sur plusieurs jours
# Dans ton vrai projet, tu remplaceras ça par tes fichiers Excel

np.random.seed(42)


def generer_donnees(n_jours=60):
    """
    Génère des données de voyages simulées.
    On utilise 60 jours pour avoir assez de données
    pour la courbe d'apprentissage.
    """
    voyages = []
    lignes = ["L1", "L2", "L3"]
    terminus = ["A", "B", "C", "D"]

    for jour in range(n_jours):
        for heure_depart in range(360, 1320, 15):  # de 6h à 22h toutes les 15 min
            if np.random.random() > 0.3:
                continue

            ligne = np.random.choice(lignes)
            origine = np.random.choice(terminus)
            destination = np.random.choice([t for t in terminus if t != origine])
            duree = np.random.randint(20, 60)

            # Règles cachées que le modèle devra apprendre :
            # - Bus_1/Bus_2 → ligne L1 (matin/après-midi)
            # - Bus_3 → ligne L2
            # - Bus_4/Bus_5 → ligne L3 (matin/après-midi)
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
                "bus": bus,
            })

    return pd.DataFrame(voyages)


df = generer_donnees(n_jours=60)
print(f"📊 Données générées : {len(df)} voyages sur 60 jours")
print(f"   Colonnes : {list(df.columns)}")
print(f"\n🔍 Aperçu des 5 premières lignes :")
print(df.head().to_string())
print()


# =============================================
# PARTIE 3 : PRÉPARER LES DONNÉES (FEATURES)
# =============================================
print("=" * 50)
print("📐 PARTIE 3 : Préparation des features")
print("=" * 50)

# --- À TOI DE JOUER (Exercice 1) ---
# Crée la variable 'features' en utilisant pd.get_dummies()
# sur les colonnes : ligne, origine, destination
# Puis ajoute les colonnes numériques : heure_depart, duree
#
# 💡 DÉCOMMENTE ET COMPLÈTE :
# features = pd.get_dummies(df[[???]])
# features["heure_depart"] = ???
# features["duree"] = ???

# ---- SOLUTION ----
features = pd.get_dummies(df[["ligne", "origine", "destination"]])
features["heure_depart"] = df["heure_depart"]
features["duree"] = df["duree"]
# ---- FIN SOLUTION ----

cible = df["bus"]

print(f"\n✅ Features créées : {features.shape[1]} colonnes")
print(f"   Colonnes : {list(features.columns)}")
print(f"   Cible : {cible.nunique()} bus différents ({list(cible.unique())})")
print()


# =============================================
# PARTIE 4 : SÉPARER DONNÉES TRAIN / TEST
# =============================================
print("=" * 50)
print("🔀 PARTIE 4 : Séparation train / test")
print("=" * 50)

# --- À TOI DE JOUER (Exercice 2) ---
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

predictions = modele.predict(X_test)
precision = accuracy_score(y_test, predictions)
print(f"\n🎯 Précision du modèle : {precision:.1%}")
print(f"   (Le modèle attribue le bon bus {precision:.1%} du temps)\n")

print("📋 Détail par bus :")
print(classification_report(y_test, predictions))


# =============================================
# PARTIE 7 : COMPRENDRE LE MODÈLE
# =============================================
print("=" * 50)
print("🔍 PARTIE 7 : Quelles features sont les plus importantes ?")
print("=" * 50)

importances = pd.Series(
    modele.feature_importances_, index=features.columns
).sort_values(ascending=False)

print("\nImportance des features :")
for feature, importance in importances.items():
    barre = "█" * int(importance * 50)
    print(f"   {feature:20s} : {importance:.3f} {barre}")


# =============================================
# PARTIE 8 : PRÉDIRE PLUSIEURS VOYAGES 🔮
# =============================================
print("\n" + "=" * 50)
print("🔮 PARTIE 8 : Prédire plusieurs nouveaux voyages")
print("=" * 50)

# --- À TOI DE JOUER (Exercice 4) ---
# Modifie cette liste pour tester tes propres scénarios !
# Tu peux ajouter autant de voyages que tu veux.

nouveaux_voyages = [
    {"ligne": "L1", "origine": "A", "destination": "B", "heure_depart": 480, "duree": 35},   # L1, 8h00, matin
    {"ligne": "L1", "origine": "B", "destination": "A", "heure_depart": 840, "duree": 40},   # L1, 14h00, après-midi
    {"ligne": "L2", "origine": "C", "destination": "D", "heure_depart": 600, "duree": 45},   # L2, 10h00
    {"ligne": "L3", "origine": "D", "destination": "A", "heure_depart": 420, "duree": 30},   # L3, 7h00, matin
    {"ligne": "L3", "origine": "A", "destination": "C", "heure_depart": 960, "duree": 50},   # L3, 16h00, après-midi
    {"ligne": "L2", "origine": "D", "destination": "B", "heure_depart": 1080, "duree": 25},  # L2, 18h00, soir
]

# Préparation des voyages (même format que les données d'entraînement)
voyages_df = pd.DataFrame(nouveaux_voyages)
voyages_features = pd.get_dummies(voyages_df[["ligne", "origine", "destination"]])
voyages_features["heure_depart"] = voyages_df["heure_depart"]
voyages_features["duree"] = voyages_df["duree"]

# Assurer que toutes les colonnes sont présentes et dans le bon ordre
for col in features.columns:
    if col not in voyages_features.columns:
        voyages_features[col] = 0
voyages_features = voyages_features[features.columns]

# Prédictions pour tous les voyages
bus_predits = modele.predict(voyages_features)
probabilites = modele.predict_proba(voyages_features)

# Affichage des résultats
print(f"\n📌 {len(nouveaux_voyages)} voyages à attribuer :\n")
print(f"   {'#':<3} {'Ligne':<7} {'Trajet':<8} {'Heure':<8} {'Durée':<8} {'→ Bus attribué':<16} {'Confiance'}")
print(f"   {'─'*3} {'─'*7} {'─'*8} {'─'*8} {'─'*8} {'─'*16} {'─'*10}")

for i, (voyage, bus, proba) in enumerate(zip(nouveaux_voyages, bus_predits, probabilites)):
    heure = f"{voyage['heure_depart'] // 60}h{voyage['heure_depart'] % 60:02d}"
    trajet = f"{voyage['origine']}→{voyage['destination']}"
    confiance = max(proba)
    print(f"   {i+1:<3} {voyage['ligne']:<7} {trajet:<8} {heure:<8} {voyage['duree']:<8} → {bus:<14} {confiance:.0%}")

# Tableau récapitulatif par bus
print(f"\n📊 Récapitulatif par bus :")
recap = pd.Series(bus_predits).value_counts().sort_index()
for bus, count in recap.items():
    voyages_du_bus = [
        v for v, b in zip(nouveaux_voyages, bus_predits) if b == bus
    ]
    lignes_str = ", ".join(
        [f"{v['ligne']} {v['heure_depart']//60}h{v['heure_depart']%60:02d}" for v in voyages_du_bus]
    )
    print(f"   {bus} : {count} voyage(s) → {lignes_str}")


# =============================================
# PARTIE 9 : COURBE D'APPRENTISSAGE 📉
# =============================================
print("\n" + "=" * 50)
print("📉 PARTIE 9 : Courbe d'apprentissage (Learning Curve)")
print("=" * 50)
print("\n⏳ Calcul en cours (peut prendre quelques secondes)...")

# Calcul de la courbe d'apprentissage
# On entraîne le modèle avec de plus en plus de données
# et on mesure l'erreur à chaque fois
train_sizes, train_scores, test_scores = learning_curve(
    RandomForestClassifier(n_estimators=100, random_state=42),
    features,
    cible,
    train_sizes=np.linspace(0.05, 1.0, 15),  # de 5% à 100% des données
    cv=5,                                      # validation croisée 5 plis
    scoring="accuracy",
    n_jobs=-1,                                 # utiliser tous les cœurs CPU
    random_state=42,
)

# Convertir accuracy en erreur (erreur = 1 - accuracy)
train_errors_mean = (1 - train_scores.mean(axis=1)) * 100  # en %
test_errors_mean = (1 - test_scores.mean(axis=1)) * 100
train_errors_std = train_scores.std(axis=1) * 100
test_errors_std = test_scores.std(axis=1) * 100

# ---- Créer le graphique ----
fig, ax = plt.subplots(figsize=(10, 7))

# Courbe erreur test (ligne pleine) = validation
ax.plot(
    train_sizes, test_errors_mean,
    "b-", linewidth=2.5, label="Erreur validation (test)", zorder=3
)
# Zone d'incertitude test
ax.fill_between(
    train_sizes,
    test_errors_mean - test_errors_std,
    test_errors_mean + test_errors_std,
    alpha=0.15, color="blue"
)

# Courbe erreur entraînement (ligne pointillée)
ax.plot(
    train_sizes, train_errors_mean,
    "b--", linewidth=2.5, label="Erreur entraînement (train)", zorder=3
)
# Zone d'incertitude train
ax.fill_between(
    train_sizes,
    train_errors_mean - train_errors_std,
    train_errors_mean + train_errors_std,
    alpha=0.1, color="blue"
)

# Ligne de référence (erreur minimale théorique)
min_error = min(test_errors_mean)
ax.axhline(
    y=min_error, color="gray", linestyle=":", linewidth=1,
    label=f"Meilleure erreur atteinte ({min_error:.1f}%)"
)

# Mise en forme
ax.set_xlabel("Taille du jeu d'entraînement (nombre de voyages)", fontsize=12)
ax.set_ylabel("Erreur (%)", fontsize=12)
ax.set_title("Courbe d'apprentissage — Random Forest\nAttribution des voyages bus", fontsize=14, fontweight="bold")
ax.legend(fontsize=11, loc="upper right")
ax.grid(True, alpha=0.3)
ax.set_ylim(bottom=0)

# Annotations pédagogiques
# Flèche expliquant la zone entre les deux courbes
mid_idx = len(train_sizes) // 3
if test_errors_mean[mid_idx] - train_errors_mean[mid_idx] > 3:
    mid_x = train_sizes[mid_idx]
    mid_y = (test_errors_mean[mid_idx] + train_errors_mean[mid_idx]) / 2
    ax.annotate(
        "",
        xy=(mid_x, mid_y),
        xytext=(mid_x + len(df) * 0.15, mid_y + 5),
        fontsize=9, color="darkblue",
        arrowprops=dict(arrowstyle="->", color="darkblue", lw=1.5),
    )

# Annotation convergence
last_idx = -1
ax.annotate(
    f"Convergence\n~{test_errors_mean[last_idx]:.1f}% erreur",
    xy=(train_sizes[last_idx], test_errors_mean[last_idx]),
    xytext=(train_sizes[last_idx] - len(df) * 0.25, test_errors_mean[last_idx] + 8),
    fontsize=9, color="darkblue",
    arrowprops=dict(arrowstyle="->", color="darkblue", lw=1.5),
)

plt.tight_layout()
plt.savefig("learning_curve_bus.png", dpi=150, bbox_inches="tight")
print("\n✅ Graphique sauvegardé : learning_curve_bus.png")

# Interprétation automatique
print("\n📖 Comment lire ce graphique :")
print(f"   • Avec peu de données, l'erreur de test est élevée (~{test_errors_mean[0]:.0f}%)")
print(f"   • Plus on ajoute de données, plus l'erreur baisse")
print(f"   • L'erreur se stabilise autour de {test_errors_mean[-1]:.1f}%")

ecart_final = test_errors_mean[-1] - train_errors_mean[-1]
if ecart_final > 5:
    print(f"   • L'écart train/test reste de {ecart_final:.1f}% → le modèle overfitte encore")
    print(f"     💡 Solutions : plus de données, réduire max_depth, ou augmenter min_samples_leaf")
elif ecart_final > 2:
    print(f"   • L'écart train/test est de {ecart_final:.1f}% → léger overfitting, acceptable")
else:
    print(f"   • L'écart train/test est faible ({ecart_final:.1f}%) → bon équilibre !")

if test_errors_mean[-1] - test_errors_mean[-3] > 1:
    print(f"   • La courbe descend encore → ajouter des données pourrait améliorer le modèle")
else:
    print(f"   • La courbe est stable → ajouter des données n'améliorera pas beaucoup le modèle")


# =============================================
# 🎓 EXERCICES BONUS
# =============================================
print("\n" + "=" * 50)
print("🎓 EXERCICES BONUS POUR ALLER PLUS LOIN")
print("=" * 50)
print("""
1. MODIFIER LES PARAMÈTRES DU MODÈLE
   - Change n_estimators (50, 200, 500) et observe l'impact
   - Ajoute max_depth=10 pour limiter la profondeur
   - Ajoute min_samples_leaf=5
   → Relance la learning curve pour voir l'effet !

2. AJOUTER DES FEATURES
   - Crée "est_matin" : features["est_matin"] = (df["heure_depart"] < 720).astype(int)
   - Crée "heure_arrivee" : features["heure_arrivee"] = df["heure_depart"] + df["duree"]
   - La précision s'améliore-t-elle ?

3. AJOUTER TES PROPRES VOYAGES DE TEST
   - Ajoute des voyages dans la liste 'nouveaux_voyages' (Partie 8)
   - Teste des cas limites : voyage très tôt, très tard, longue durée...
   - Le modèle donne-t-il des résultats logiques ?

4. TESTER AVEC TES VRAIES DONNÉES
   - Remplace generer_donnees() par :
     df = pd.read_excel("ton_fichier.xlsx")
   - Adapte les noms de colonnes
   - Lance l'entraînement et la learning curve !

5. COMPARER AVEC UN AUTRE MODÈLE
   - from sklearn.ensemble import GradientBoostingClassifier
   - Trace les deux learning curves sur le même graphique
   - Quel modèle converge le plus vite ?

💡 Change UNE SEULE chose à la fois et observe l'impact !
""")