"""
=============================================================================
🚌 SYSTÈME DE RÉPARTITION INTELLIGENTE DES SERVICES BUS - VERSION RÉELLE
=============================================================================

Adapté à la structure réelle des données de planification bus.

Structure des données d'entrée :
- Période : sem N-3, mercredi, sem p3, sem p8, samedi, dimanche, samedi P8, dimanche P8
- Dépôt d'attache : Dépôt du service
- Numéro de service : Identifiant du service (plusieurs lignes = même service)
- Numéro de ligne : Ligne du voyage
- Numéro des voyages : Identifiant du voyage
- Sens de circulation : Aller/Retour
- Arrêt de début : Point de départ
- Arrêt de fin : Point d'arrivée
- Heure de début : Heure de départ
- Heure de fin : Heure d'arrivée
- Numéro de voiture : Véhicule utilisé
- Jours de semaine : 12345 (lun-ven), 6 (sam), 7 (dim), etc.

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
import warnings
warnings.filterwarnings('ignore')

print("=" * 100)
print("🚌 SYSTÈME DE RÉPARTITION INTELLIGENTE DES SERVICES BUS")
print("=" * 100)


# =============================================
# PARTIE 1 : FONCTIONS UTILITAIRES
# =============================================

def heure_to_minutes(heure_str):
    """
    Convertit une heure au format HH:MM ou H:MM en minutes depuis minuit.
    
    Exemples:
        "6:00"  → 360
        "13:45" → 825
        "21:30" → 1290
    """
    try:
        if pd.isna(heure_str):
            return None
        
        # Si c'est déjà un nombre
        if isinstance(heure_str, (int, float)):
            return int(heure_str)
        
        # Si c'est une chaîne
        heure_str = str(heure_str).strip()
        
        # Gérer le format HH:MM
        if ':' in heure_str:
            parts = heure_str.split(':')
            heures = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return heures * 60 + minutes
        
        # Si c'est juste un nombre
        return int(float(heure_str))
    
    except Exception as e:
        print(f"⚠️  Erreur conversion heure '{heure_str}': {e}")
        return None


def minutes_to_heure(minutes):
    """Convertit des minutes en format HH:MM"""
    if pd.isna(minutes):
        return "N/A"
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h:02d}:{m:02d}"


def analyser_coupure(heures_debut, heures_fin, seuil_minutes=90):
    """
    Détecte s'il y a une coupure dans un service.
    Une coupure = écart > seuil_minutes entre fin d'un voyage et début du suivant.
    
    Returns:
        (a_coupure: bool, duree_coupure_max: int, position_coupure: str)
    """
    if len(heures_debut) <= 1:
        return False, 0, "Aucune"
    
    ecarts = []
    positions = []
    
    for i in range(len(heures_fin) - 1):
        ecart = heures_debut[i+1] - heures_fin[i]
        ecarts.append(ecart)
        positions.append(i)
    
    if not ecarts:
        return False, 0, "Aucune"
    
    max_ecart = max(ecarts)
    
    if max_ecart > seuil_minutes:
        idx_max = ecarts.index(max_ecart)
        position = positions[idx_max]
        
        # Déterminer si c'est plutôt en début ou fin de service
        if position < len(ecarts) / 2:
            pos_str = "DEBUT"
        else:
            pos_str = "FIN"
        
        return True, max_ecart, pos_str
    
    return False, 0, "Aucune"


def determiner_type_service(heure_debut_min, heure_fin_max, a_coupure, position_coupure, duree_totale):
    """
    Détermine le type de service selon des règles métier.
    
    Returns:
        type_service: str (MATIN, APREM, COUPE_DEBUT, COUPE_FIN, JOURNEE)
    """
    # Seuils d'horaires (en minutes)
    SEUIL_MATIN = 480      # 8h00
    SEUIL_DEBUT_APREM = 720  # 12h00
    SEUIL_FIN_APREM = 1020   # 17h00
    
    if a_coupure:
        if position_coupure == "DEBUT":
            return "COUPE_DEBUT"
        else:
            return "COUPE_FIN"
    
    # Service sans coupure
    if heure_fin_max <= SEUIL_DEBUT_APREM:
        return "MATIN"
    elif heure_debut_min >= SEUIL_DEBUT_APREM:
        return "APREM"
    elif duree_totale > 600:  # Plus de 10h
        return "JOURNEE"
    elif heure_debut_min < SEUIL_MATIN and heure_fin_max < SEUIL_FIN_APREM:
        return "MATIN"
    elif heure_debut_min >= SEUIL_MATIN and heure_fin_max > SEUIL_FIN_APREM:
        return "APREM"
    else:
        return "JOURNEE"


# =============================================
# PARTIE 2 : CHARGEMENT ET PRÉPARATION DES DONNÉES
# =============================================

print("\n📊 PARTIE 1 : Chargement des données")
print("=" * 100)

def charger_donnees_voyages(fichier_excel, nom_feuille=0):
    """
    Charge les données depuis Excel avec la structure réelle.
    
    Colonnes attendues (dans l'ordre) :
    0:  Période
    1:  Dépôt d'attache
    2:  Numéro de service
    3:  Numéro de ligne
    4:  Numéro des voyages
    5:  Sens de circulation
    6:  Arrêt de début
    7:  Arrêt de fin
    8:  Heure de début
    9:  Heure de fin
    10: Numéro de voiture
    11: Jours de semaine
    """
    # Charger le fichier
    df = pd.read_excel(fichier_excel, sheet_name=nom_feuille)
    
    # Renommer les colonnes pour faciliter le traitement
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
    
    # Si le nombre de colonnes correspond
    if len(df.columns) >= len(colonnes_standard):
        df.columns = colonnes_standard + list(df.columns[len(colonnes_standard):])
    else:
        print(f"⚠️  Attention : {len(df.columns)} colonnes trouvées, {len(colonnes_standard)} attendues")
        print(f"Colonnes détectées : {list(df.columns)}")
    
    # Convertir les heures en minutes
    df['heure_debut_min'] = df['heure_debut'].apply(heure_to_minutes)
    df['heure_fin_min'] = df['heure_fin'].apply(heure_to_minutes)
    
    # Nettoyer les données
    df = df.dropna(subset=['num_service', 'heure_debut_min', 'heure_fin_min'])
    
    print(f"✅ {len(df)} voyages chargés")
    print(f"   {df['num_service'].nunique()} services uniques")
    print(f"   {df['num_ligne'].nunique()} lignes différentes")
    print(f"   Périodes : {df['periode'].unique()}")
    
    return df


def agreger_services(df_voyages):
    """
    Agrège les voyages par service pour créer les features du modèle ML.
    
    Returns:
        DataFrame avec une ligne par service
    """
    services = []
    
    for num_service, groupe in df_voyages.groupby('num_service'):
        # Trier par heure de début
        groupe = groupe.sort_values('heure_debut_min')
        
        # Extraire les heures
        heures_debut = groupe['heure_debut_min'].tolist()
        heures_fin = groupe['heure_fin_min'].tolist()
        
        # Calculer les caractéristiques
        heure_debut_service = min(heures_debut)
        heure_fin_service = max(heures_fin)
        nb_voyages = len(groupe)
        
        # Analyser les coupures
        a_coupure, duree_coupure, position_coupure = analyser_coupure(heures_debut, heures_fin)
        
        # Durées
        duree_totale = heure_fin_service - heure_debut_service
        duree_travail = duree_totale - duree_coupure
        
        # Déterminer le type de service
        type_service = determiner_type_service(
            heure_debut_service, heure_fin_service,
            a_coupure, position_coupure, duree_totale
        )
        
        # Informations complémentaires
        depot = groupe['depot'].iloc[0] if 'depot' in groupe.columns else "N/A"
        periode = groupe['periode'].iloc[0] if 'periode' in groupe.columns else "N/A"
        lignes = groupe['num_ligne'].unique()
        ligne_principale = groupe['num_ligne'].mode()[0] if len(groupe) > 0 else lignes[0]
        
        services.append({
            'num_service': num_service,
            'type_service': type_service,
            'depot': depot,
            'periode': periode,
            'ligne_principale': ligne_principale,
            'nb_lignes': len(lignes),
            'heure_debut': heure_debut_service,
            'heure_fin': heure_fin_service,
            'nb_voyages': nb_voyages,
            'duree_totale': duree_totale,
            'duree_coupure': duree_coupure,
            'duree_travail': duree_travail,
            'a_coupure': a_coupure,
            'position_coupure': position_coupure,
        })
    
    df_services = pd.DataFrame(services)
    
    print(f"\n✅ {len(df_services)} services agrégés")
    print(f"\n📊 Répartition par type de service :")
    print(df_services['type_service'].value_counts())
    
    return df_services


# 🔧 CHARGEZ VOS DONNÉES ICI
# Option 1 : Générer des données d'exemple
def generer_donnees_exemple():
    """Génère des données d'exemple pour tester le système"""
    np.random.seed(42)
    voyages = []
    
    periodes = ["sem N-3", "mercredi", "sem p3", "samedi", "dimanche"]
    depots = ["DEPOT_A", "DEPOT_B"]
    lignes = ["L1", "L2", "L3"]
    sens_options = ["ALLER", "RETOUR"]
    
    service_id = 1
    for _ in range(80):  # 80 services
        type_service = np.random.choice(["MATIN", "APREM", "COUPE_DEBUT", "COUPE_FIN"])
        
        if type_service == "MATIN":
            heure_debut_service = np.random.randint(300, 420)  # 5h-7h
            heure_fin_service = np.random.randint(720, 840)    # 12h-14h
            nb_voyages = np.random.randint(6, 12)
            coupure = 0
        elif type_service == "APREM":
            heure_debut_service = np.random.randint(720, 840)   # 12h-14h
            heure_fin_service = np.random.randint(1200, 1320)   # 20h-22h
            nb_voyages = np.random.randint(6, 12)
            coupure = 0
        elif type_service == "COUPE_DEBUT":
            heure_debut_service = np.random.randint(330, 420)
            heure_fin_service = np.random.randint(1050, 1150)
            nb_voyages = np.random.randint(10, 16)
            coupure = np.random.randint(180, 300)
        else:  # COUPE_FIN
            heure_debut_service = np.random.randint(570, 660)
            heure_fin_service = np.random.randint(1260, 1350)
            nb_voyages = np.random.randint(10, 16)
            coupure = np.random.randint(180, 300)
        
        # Générer les voyages pour ce service
        duree_travail = (heure_fin_service - heure_debut_service) - coupure
        intervalle = duree_travail // nb_voyages if nb_voyages > 0 else 30
        
        heure_actuelle = heure_debut_service
        moment_coupure = heure_debut_service + (duree_travail // 2) if coupure > 0 else None
        coupure_effectuee = False
        
        for v in range(nb_voyages):
            # Gérer la coupure
            if coupure > 0 and not coupure_effectuee and heure_actuelle >= moment_coupure:
                heure_actuelle += coupure
                coupure_effectuee = True
            
            duree_voyage = np.random.randint(25, 45)
            heure_fin_voyage = heure_actuelle + duree_voyage
            
            voyages.append({
                "periode": np.random.choice(periodes),
                "depot": np.random.choice(depots),
                "num_service": f"S{service_id:04d}",
                "num_ligne": np.random.choice(lignes),
                "num_voyage": f"V{len(voyages)+1:05d}",
                "sens": np.random.choice(sens_options),
                "arret_debut": f"Arret_{np.random.randint(1, 20)}",
                "arret_fin": f"Arret_{np.random.randint(1, 20)}",
                "heure_debut": minutes_to_heure(heure_actuelle),
                "heure_fin": minutes_to_heure(heure_fin_voyage),
                "num_voiture": f"BUS_{np.random.randint(100, 200)}",
                "jours_semaine": "12345",
            })
            
            heure_actuelle = heure_fin_voyage + np.random.randint(5, 15)
        
        service_id += 1
    
    return pd.DataFrame(voyages)


# Option 2 : Charger vos vraies données (décommentez et modifiez)
# df_voyages = charger_donnees_voyages("mes_donnees.xlsx", nom_feuille=0)

# Pour l'exemple, on génère des données
df_voyages = generer_donnees_exemple()

print(f"\n🔍 Aperçu des 10 premiers voyages :")
print(df_voyages.head(10).to_string())


# =============================================
# PARTIE 3 : AGRÉGER LES SERVICES
# =============================================

print("\n\n📐 PARTIE 2 : Agrégation des voyages en services")
print("=" * 100)

df_services = agreger_services(df_voyages)

print(f"\n🔍 Aperçu des services agrégés :")
print(df_services.head(10).to_string())


# =============================================
# PARTIE 4 : CRÉER LES FEATURES POUR LE ML
# =============================================

print("\n\n🧮 PARTIE 3 : Création des features pour le Machine Learning")
print("=" * 100)

# Features numériques
features_numeriques = [
    'heure_debut', 'heure_fin', 'nb_voyages',
    'duree_totale', 'duree_coupure', 'duree_travail', 'nb_lignes'
]

# Features binaires
df_services['a_coupure_bin'] = df_services['a_coupure'].astype(int)
df_services['est_matin'] = (df_services['heure_debut'] < 480).astype(int)
df_services['est_soir'] = (df_services['heure_fin'] > 1140).astype(int)
df_services['voyages_par_heure'] = df_services['nb_voyages'] / (df_services['duree_travail'] / 60)

features_numeriques.extend(['a_coupure_bin', 'est_matin', 'est_soir', 'voyages_par_heure'])

# One-hot encoding pour les features catégorielles
features = pd.get_dummies(df_services[['depot', 'ligne_principale']], prefix=['depot', 'ligne'])
features = pd.concat([features, df_services[features_numeriques]], axis=1)

cible = df_services['type_service']

print(f"✅ {features.shape[1]} features créées")
print(f"   Features catégorielles : depot, ligne_principale")
print(f"   Features numériques : {len(features_numeriques)} variables")
print(f"\n📊 Distribution de la cible (type_service) :")
print(cible.value_counts())


# =============================================
# PARTIE 5 : ENTRAÎNEMENT DU MODÈLE
# =============================================

print("\n\n🧠 PARTIE 4 : Entraînement du modèle Random Forest")
print("=" * 100)

# Vérifier qu'on a assez de données
if len(df_services) < 20:
    print("⚠️  ATTENTION : Moins de 20 services. Le modèle risque d'être peu fiable.")
    print("   Recommandation : Au moins 100 services pour de bons résultats.")

# Split train/test
try:
    X_train, X_test, y_train, y_test = train_test_split(
        features, cible, test_size=0.25, random_state=42, stratify=cible
    )
except ValueError:
    # Si pas assez de données pour stratifier
    print("⚠️  Impossible de stratifier (pas assez de données par classe)")
    X_train, X_test, y_train, y_test = train_test_split(
        features, cible, test_size=0.25, random_state=42
    )

print(f"   Données d'entraînement : {len(X_train)} services")
print(f"   Données de test : {len(X_test)} services")

# Entraîner le modèle
modele = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

modele.fit(X_train, y_train)

print(f"\n✅ Modèle entraîné avec {modele.n_estimators} arbres")

# Évaluation
predictions = modele.predict(X_test)
precision = (predictions == y_test).sum() / len(y_test)

print(f"\n🎯 Précision globale : {precision:.1%}")
print(f"\n📊 Rapport détaillé :")
print(classification_report(y_test, predictions, zero_division=0))


# =============================================
# PARTIE 6 : IMPORTANCE DES FEATURES
# =============================================

print("\n" + "=" * 100)
print("🔍 PARTIE 5 : Importance des features")
print("=" * 100)

importances = pd.DataFrame({
    'feature': features.columns,
    'importance': modele.feature_importances_
}).sort_values('importance', ascending=False)

print("\n📊 Top 15 des features les plus importantes :")
for i, row in importances.head(15).iterrows():
    barre = "█" * int(row['importance'] * 80)
    print(f"   {row['feature']:30s} : {row['importance']:.4f} {barre}")


# =============================================
# PARTIE 7 : PRÉDICTION POUR NOUVEAUX SERVICES
# =============================================

print("\n\n" + "=" * 100)
print("🔮 PARTIE 6 : Prédiction pour de nouveaux services")
print("=" * 100)

def predire_type_service_v2(voyages_list, depot="N/A", periode="N/A"):
    """
    Prédit le type de service à partir d'une liste de voyages.
    
    Args:
        voyages_list: Liste de dict avec clés:
            - heure_debut: str ou int (ex: "6:30" ou 390)
            - heure_fin: str ou int
            - ligne: str (optionnel)
        depot: str
        periode: str
    
    Returns:
        type_predit: str
        probabilites: dict
        details: dict (détails du service)
    """
    # Convertir les heures en minutes
    heures_debut = []
    heures_fin = []
    lignes = []
    
    for voyage in voyages_list:
        h_deb = heure_to_minutes(voyage['heure_debut'])
        h_fin = heure_to_minutes(voyage['heure_fin'])
        
        if h_deb is not None and h_fin is not None:
            heures_debut.append(h_deb)
            heures_fin.append(h_fin)
            if 'ligne' in voyage:
                lignes.append(voyage['ligne'])
    
    if not heures_debut:
        return None, {}, {"erreur": "Aucune heure valide"}
    
    # Calculer les caractéristiques
    heure_debut_service = min(heures_debut)
    heure_fin_service = max(heures_fin)
    nb_voyages = len(voyages_list)
    
    # Analyser les coupures
    a_coupure, duree_coupure, position_coupure = analyser_coupure(heures_debut, heures_fin)
    
    duree_totale = heure_fin_service - heure_debut_service
    duree_travail = duree_totale - duree_coupure
    
    ligne_principale = lignes[0] if lignes else "L1"
    nb_lignes = len(set(lignes)) if lignes else 1
    
    # Créer le vecteur de features
    features_dict = {
        'heure_debut': heure_debut_service,
        'heure_fin': heure_fin_service,
        'nb_voyages': nb_voyages,
        'duree_totale': duree_totale,
        'duree_coupure': duree_coupure,
        'duree_travail': duree_travail,
        'nb_lignes': nb_lignes,
        'a_coupure_bin': 1 if a_coupure else 0,
        'est_matin': 1 if heure_debut_service < 480 else 0,
        'est_soir': 1 if heure_fin_service > 1140 else 0,
        'voyages_par_heure': nb_voyages / (duree_travail / 60) if duree_travail > 0 else 0,
    }
    
    # One-hot encoding pour depot et ligne
    for col in features.columns:
        if col.startswith('depot_') or col.startswith('ligne_'):
            features_dict[col] = 0
    
    # Activer le bon depot et la bonne ligne
    depot_col = f"depot_{depot}"
    ligne_col = f"ligne_{ligne_principale}"
    
    if depot_col in features_dict:
        features_dict[depot_col] = 1
    if ligne_col in features_dict:
        features_dict[ligne_col] = 1
    
    # Créer le DataFrame
    service_features = pd.DataFrame([features_dict])
    service_features = service_features[features.columns]
    
    # Prédiction
    type_predit = modele.predict(service_features)[0]
    probas = modele.predict_proba(service_features)[0]
    probas_dict = dict(zip(modele.classes_, probas))
    
    details = {
        'heure_debut': minutes_to_heure(heure_debut_service),
        'heure_fin': minutes_to_heure(heure_fin_service),
        'nb_voyages': nb_voyages,
        'duree_totale': f"{duree_totale//60}h{duree_totale%60:02d}",
        'duree_coupure': f"{duree_coupure//60}h{duree_coupure%60:02d}" if duree_coupure > 0 else "Aucune",
        'a_coupure': a_coupure,
    }
    
    return type_predit, probas_dict, details


# Exemples de prédiction
print("\n📋 Exemples de prédiction :\n")

exemples = [
    {
        "nom": "Service matin classique",
        "voyages": [
            {"heure_debut": "6:00", "heure_fin": "6:35", "ligne": "L1"},
            {"heure_debut": "6:40", "heure_fin": "7:15", "ligne": "L1"},
            {"heure_debut": "7:20", "heure_fin": "7:55", "ligne": "L1"},
            {"heure_debut": "8:00", "heure_fin": "8:35", "ligne": "L1"},
            {"heure_debut": "8:40", "heure_fin": "9:15", "ligne": "L1"},
            {"heure_debut": "9:20", "heure_fin": "9:55", "ligne": "L1"},
            {"heure_debut": "10:00", "heure_fin": "10:35", "ligne": "L1"},
            {"heure_debut": "10:40", "heure_fin": "11:15", "ligne": "L1"},
        ],
        "depot": "DEPOT_A"
    },
    {
        "nom": "Service après-midi",
        "voyages": [
            {"heure_debut": "13:00", "heure_fin": "13:35", "ligne": "L2"},
            {"heure_debut": "13:40", "heure_fin": "14:15", "ligne": "L2"},
            {"heure_debut": "14:20", "heure_fin": "14:55", "ligne": "L2"},
            {"heure_debut": "15:00", "heure_fin": "15:35", "ligne": "L2"},
            {"heure_debut": "15:40", "heure_fin": "16:15", "ligne": "L2"},
            {"heure_debut": "16:20", "heure_fin": "16:55", "ligne": "L2"},
            {"heure_debut": "17:00", "heure_fin": "17:35", "ligne": "L2"},
            {"heure_debut": "18:00", "heure_fin": "18:35", "ligne": "L2"},
            {"heure_debut": "19:00", "heure_fin": "19:35", "ligne": "L2"},
        ],
        "depot": "DEPOT_B"
    },
    {
        "nom": "Service coupé (pause déjeuner)",
        "voyages": [
            {"heure_debut": "6:30", "heure_fin": "7:05", "ligne": "L1"},
            {"heure_debut": "7:10", "heure_fin": "7:45", "ligne": "L1"},
            {"heure_debut": "7:50", "heure_fin": "8:25", "ligne": "L1"},
            {"heure_debut": "8:30", "heure_fin": "9:05", "ligne": "L1"},
            {"heure_debut": "9:10", "heure_fin": "9:45", "ligne": "L1"},
            # --- COUPURE DE 4H ---
            {"heure_debut": "13:45", "heure_fin": "14:20", "ligne": "L1"},
            {"heure_debut": "14:25", "heure_fin": "15:00", "ligne": "L1"},
            {"heure_debut": "15:05", "heure_fin": "15:40", "ligne": "L1"},
            {"heure_debut": "15:45", "heure_fin": "16:20", "ligne": "L1"},
            {"heure_debut": "16:25", "heure_fin": "17:00", "ligne": "L1"},
            {"heure_debut": "17:05", "heure_fin": "17:40", "ligne": "L1"},
        ],
        "depot": "DEPOT_A"
    },
]

for i, exemple in enumerate(exemples, 1):
    print(f"{'─'*100}")
    print(f"🚌 Exemple {i} : {exemple['nom']}")
    print(f"{'─'*100}")
    
    type_p, probas, details = predire_type_service_v2(
        exemple['voyages'],
        depot=exemple['depot']
    )
    
    print(f"   📍 Dépôt : {exemple['depot']}")
    print(f"   📅 Horaire : {details['heure_debut']} → {details['heure_fin']}")
    print(f"   🚍 Nombre de voyages : {details['nb_voyages']}")
    print(f"   ⏱️  Durée totale : {details['duree_totale']}")
    if details['a_coupure']:
        print(f"   ⚠️  Coupure détectée : {details['duree_coupure']}")
    
    print(f"\n   🎯 Type prédit : {type_p} (confiance : {max(probas.values()):.1%})")
    print(f"\n   📊 Probabilités détaillées :")
    for type_s, proba in sorted(probas.items(), key=lambda x: -x[1]):
        barre = "█" * int(proba * 40)
        print(f"      {type_s:15s} : {proba:5.1%} {barre}")
    print()


# =============================================
# PARTIE 8 : SAUVEGARDER LE MODÈLE
# =============================================

print("\n" + "=" * 100)
print("💾 PARTIE 7 : Sauvegarde du modèle")
print("=" * 100)

import pickle

with open("modele_services_v2.pkl", "wb") as f:
    pickle.dump({
        'modele': modele,
        'colonnes': list(features.columns),
        'classes': list(modele.classes_),
    }, f)

print("✅ Modèle sauvegardé : modele_services_v2.pkl")
print("\n💡 Pour réutiliser :")
print("""
    import pickle
    with open("modele_services_v2.pkl", "rb") as f:
        data = pickle.load(f)
        modele = data['modele']
        colonnes = data['colonnes']
""")


# =============================================
# RÉSUMÉ
# =============================================

print("\n\n" + "=" * 100)
print("✅ RÉSUMÉ DE L'EXÉCUTION")
print("=" * 100)
print(f"""
📊 Données analysées :
   • {len(df_voyages)} voyages au total
   • {len(df_services)} services uniques
   • {df_services['num_ligne'].nunique()} lignes différentes
   • {df_services['depot'].nunique()} dépôts

🎯 Performance du modèle :
   • Précision globale : {precision:.1%}
   • {len(modele.classes_)} types de services détectés : {', '.join(modele.classes_)}

📈 Prochaines étapes :
   1. Vérifiez les prédictions sur vos exemples
   2. Ajustez les seuils de détection si nécessaire
   3. Ajoutez plus de données historiques pour améliorer le modèle
   4. Utilisez predire_type_service_v2() pour prédire de nouveaux services

💡 Pour charger vos vraies données :
   df_voyages = charger_donnees_voyages("votre_fichier.xlsx")
   
   Puis relancez le script !
""")

print("=" * 100)
print("✨ Script terminé avec succès !")
print("=" * 100)
