# 🚀 GUIDE DE DÉMARRAGE RAPIDE — VERSION 2 (Structure Réelle)

## 📦 Ce que vous avez maintenant

Un système complet adapté à la **vraie structure** de vos données de planification bus !

### ✨ Nouveautés de la version 2

Cette version utilise directement la structure de vos fichiers Excel :
- ✅ Un voyage par ligne (pas besoin d'agréger manuellement)
- ✅ Détection automatique des services (regroupement par numéro de service)
- ✅ Analyse automatique des coupures
- ✅ Format d'heures HH:MM (plus besoin de convertir en minutes)
- ✅ Gestion des périodes, dépôts, lignes multiples

---

## 📊 Structure de vos données

Voici les **12 colonnes** attendues (dans l'ordre) :

| # | Colonne | Exemple | Description |
|---|---------|---------|-------------|
| 1 | **Période** | "sem N-3" | Type de période (sem N-3, mercredi, sem p3, samedi, etc.) |
| 2 | **Dépôt d'attache** | "DEPOT_A" | Dépôt du service |
| 3 | **Numéro de service** | "S0001" | ⭐ IMPORTANT : Même numéro pour tous les voyages d'un service |
| 4 | **Numéro de ligne** | "L1" | Ligne du voyage |
| 5 | **Numéro des voyages** | "V00001" | Identifiant unique du voyage |
| 6 | **Sens de circulation** | "ALLER" | ALLER ou RETOUR |
| 7 | **Arrêt de début** | "Terminus_Nord" | Point de départ |
| 8 | **Arrêt de fin** | "Terminus_Sud" | Point d'arrivée |
| 9 | **Heure de début** | "6:00" | Format HH:MM |
| 10 | **Heure de fin** | "6:35" | Format HH:MM |
| 11 | **Numéro de voiture** | "BUS_101" | Véhicule utilisé |
| 12 | **Jours de semaine** | "12345" | 12345 (lun-ven), 6 (sam), 7 (dim), etc. |

---

## ⚡ Démarrage en 5 minutes

### Étape 1 : Tester avec les données d'exemple

```bash
python systeme_repartition_services_v2.py
```

Le script va :
1. Générer des données d'exemple
2. Regrouper les voyages par service
3. Détecter automatiquement les types (MATIN, APREM, COUPE_DEBUT, COUPE_FIN)
4. Entraîner le modèle
5. Faire des prédictions sur de nouveaux services

### Étape 2 : Utiliser vos vraies données

1. **Ouvrez** le fichier `template_donnees_voyages_v2.xlsx`

2. **Consultez** les 3 onglets :
   - "Données Voyages" : Template à remplir
   - "📖 Guide" : Instructions détaillées
   - "📌 Exemples Services" : Types de services

3. **Copiez** vos données dans la feuille "Données Voyages"
   - Respectez l'ordre des colonnes
   - Un voyage = une ligne
   - Même numéro de service pour tous les voyages d'un service

4. **Sauvegardez** sous `mes_donnees_services.xlsx`

5. **Modifiez** le script Python (ligne ~240) :
   ```python
   # Remplacez :
   df_voyages = generer_donnees_exemple()
   
   # Par :
   df_voyages = charger_donnees_voyages("mes_donnees_services.xlsx")
   ```

6. **Lancez** :
   ```bash
   python systeme_repartition_services_v2.py
   ```

---

## 🎯 Exemple concret : Un service matin

Voici comment représenter un service matin (S0001) qui fait 4 voyages :

```
┌─────────┬────────┬─────────┬───────┬─────────┬──────┬────────┬─────────┬──────┬──────┬─────┬──────┐
│ Période │ Dépôt  │ Service │ Ligne │ Voyage  │ Sens │ Début  │   Fin   │Heure │Heure │ Bus │Jours │
│         │        │         │       │         │      │        │         │début │ fin  │     │      │
├─────────┼────────┼─────────┼───────┼─────────┼──────┼────────┼─────────┼──────┼──────┼─────┼──────┤
│ sem N-3 │DEPOT_A │  S0001  │  L1   │ V00001  │ALLER │Term_N  │Term_S   │ 6:00 │ 6:35 │B_101│12345 │
│ sem N-3 │DEPOT_A │  S0001  │  L1   │ V00002  │RETOUR│Term_S  │Term_N   │ 6:40 │ 7:15 │B_101│12345 │
│ sem N-3 │DEPOT_A │  S0001  │  L1   │ V00003  │ALLER │Term_N  │Term_S   │ 7:20 │ 7:55 │B_101│12345 │
│ sem N-3 │DEPOT_A │  S0001  │  L1   │ V00004  │RETOUR│Term_S  │Term_N   │ 8:00 │ 8:35 │B_101│12345 │
└─────────┴────────┴─────────┴───────┴─────────┴──────┴────────┴─────────┴──────┴──────┴─────┴──────┘

→ Le système comprendra :
   • Service S0001 = service MATIN
   • Horaire : 6:00 → 8:35
   • 4 voyages
   • Pas de coupure
```

---

## 🔍 Ce que fait le système

### 1️⃣ Chargement des données
```
📊 12 colonnes détectées
✅ 250 voyages chargés
   • 80 services uniques
   • 3 lignes différentes
   • 2 dépôts
```

### 2️⃣ Agrégation par service
Le système regroupe automatiquement les voyages ayant le même numéro de service :
```
Service S0001 :
   • 4 voyages (V00001, V00002, V00003, V00004)
   • Heure début : 6:00 (min des heures)
   • Heure fin : 8:35 (max des heures)
   • Durée totale : 2h35
   • Coupure détectée : Non
   → Type : MATIN
```

### 3️⃣ Détection automatique des coupures
Le système détecte les coupures (écarts > 1h30 entre deux voyages) :
```
Service S0003 :
   Voyages : 6:30, 7:15, 8:00, 9:00, 10:00
   [PAUSE DE 4H]
   Voyages : 14:00, 15:00, 16:00, 17:00
   
   → Coupure détectée : 4h00
   → Position : DEBUT
   → Type : COUPE_DEBUT
```

### 4️⃣ Entraînement du modèle
```
🧠 Modèle entraîné avec 200 arbres
🎯 Précision : 89.5%

Top features importantes :
   duree_coupure    : 0.2845 ████████████████
   heure_debut      : 0.2156 ████████████
   heure_fin        : 0.1892 ██████████
   nb_voyages       : 0.1423 ████████
```

### 5️⃣ Prédiction pour nouveaux services
```python
nouveaux_voyages = [
    {"heure_debut": "6:00", "heure_fin": "6:35", "ligne": "L1"},
    {"heure_debut": "6:40", "heure_fin": "7:15", "ligne": "L1"},
    # ... etc
]

type_predit, probas, details = predire_type_service_v2(
    nouveaux_voyages,
    depot="DEPOT_A"
)

# Résultat :
# Type : MATIN (confiance : 87%)
```

---

## 📋 Types de services détectés

Le système détecte automatiquement **5 types** :

### 🌅 MATIN
- Commence tôt (avant 8h)
- Finit avant 14h
- Pas de coupure significative
- Exemple : 6:00 → 13:00

### 🌆 APREM
- Commence après 12h
- Finit tard (après 17h)
- Pas de coupure significative
- Exemple : 13:00 → 21:00

### 🔄 COUPE_DEBUT
- Commence tôt
- **Coupure en milieu de journée** (pause déjeuner)
- Reprend l'après-midi
- Exemple : 6:30 → 10:00 [PAUSE] 14:00 → 18:00

### 🔄 COUPE_FIN
- Commence en milieu de journée
- **Coupure en après-midi**
- Finit tard
- Exemple : 10:00 → 14:00 [PAUSE] 17:00 → 22:00

### 📅 JOURNEE
- Service très long (>10h)
- Sans coupure significative
- Exemple : 7:00 → 20:00

---

## ⚠️ Points d'attention

### ✅ Bonnes pratiques
- **Même numéro de service** pour tous les voyages d'un service
- **Format heures : HH:MM** (pas de minutes)
- **Toutes les colonnes remplies**
- **Minimum 50-100 services** pour un bon modèle

### ❌ Erreurs courantes

| ❌ Erreur | ✅ Correction |
|-----------|---------------|
| Numéro de service différent pour chaque voyage | Même numéro pour tous les voyages du service |
| Heures en minutes (360) | Format HH:MM (6:00) |
| Colonnes dans le désordre | Respecter l'ordre exact du template |
| Données manquantes | Remplir toutes les colonnes |

---

## 💡 Utilisation avancée

### Prédire un nouveau service depuis un fichier Excel

```python
# Charger les nouveaux voyages
nouveaux_voyages = pd.read_excel("nouveaux_voyages.xlsx")

# Filtrer pour un service spécifique
voyages_service = nouveaux_voyages[
    nouveaux_voyages['num_service'] == 'S9999'
]

# Convertir en liste de dict
voyages_list = []
for _, row in voyages_service.iterrows():
    voyages_list.append({
        'heure_debut': row['heure_debut'],
        'heure_fin': row['heure_fin'],
        'ligne': row['num_ligne']
    })

# Prédire
type_p, probas, details = predire_type_service_v2(
    voyages_list,
    depot=voyages_service['depot'].iloc[0]
)

print(f"Type prédit : {type_p}")
print(f"Confiance : {max(probas.values()):.0%}")
```

### Analyser tous vos services

```python
# Charger vos données
df = charger_donnees_voyages("mes_donnees.xlsx")

# Agréger en services
services = agreger_services(df)

# Voir la répartition
print(services['type_service'].value_counts())

# Export
services.to_excel("analyse_services.xlsx", index=False)
```

---

## 🎓 Pour aller plus loin

1. **Ajuster les seuils** (dans le script, fonction `determiner_type_service`) :
   - Seuil de coupure (actuellement 90 min)
   - Horaires matin/après-midi

2. **Ajouter des règles métier** :
   - Contraintes spécifiques à votre réseau
   - Règles par dépôt ou période

3. **Créer une interface web** :
   - Upload Excel → Prédiction → Export
   - Streamlit ou Flask

---

## ✅ Checklist de mise en route

- [ ] Python 3.7+ installé
- [ ] Dépendances installées (`pip install pandas numpy scikit-learn matplotlib seaborn openpyxl`)
- [ ] Template Excel ouvert et consulté
- [ ] Script testé avec données d'exemple
- [ ] Structure de mes données comprise
- [ ] Données copiées dans le template
- [ ] Script modifié pour charger mes données
- [ ] Premier entraînement effectué
- [ ] Précision du modèle vérifiée (>80%)
- [ ] Premières prédictions testées

---

## 📞 Résolution de problèmes

### Le script ne trouve pas mes colonnes
→ Vérifiez que vous avez exactement 12 colonnes dans l'ordre du template

### "KeyError" sur une colonne
→ Renommez vos colonnes pour correspondre au template

### Précision très faible (<60%)
→ Vérifiez la cohérence de vos données et types de services

### "Not enough values to unpack"
→ Problème de format d'heures. Utilisez HH:MM (avec deux-points)

### Le modèle prédit toujours le même type
→ Pas assez de diversité dans les données. Ajoutez plus de services différents.

---

**🎉 Vous êtes prêt à utiliser le système avec vos vraies données !**

N'hésitez pas si vous avez des questions ou besoin d'adaptations !
