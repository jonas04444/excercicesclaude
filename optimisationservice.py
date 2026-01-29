"""**Partie 1 — Classes :**
1. Crée une classe `Voyage` (comme avant)
2. Crée une classe `Service` avec : `id`, `heure_debut`, `heure_fin`, `voyages_assignes`

**Partie 2 — Contraintes :**
3. Les voyages pré-assignés restent sur leur service (contrainte fixe)
4. Les autres voyages doivent être affectés à **exactement 1 service**
5. Pas de chevauchement temporel sur un même service
6. Un voyage doit être dans la **plage horaire** de son service

**Partie 3 — Bonus :**
7. Continuité géographique (optionnel)
8. Équilibrer la charge entre services (optionnel)"""

"""=== Service S1 (05:30 - 10:00) ===
  [FIXE] L1-1: DEPOT → CENTRE (06:00 - 06:30)
  [FIXE] L1-2: CENTRE → GARE (06:45 - 07:15)
  [AJOUTÉ] L1-3: GARE → DEPOT (07:30 - 08:00)

=== Service S2 (06:00 - 10:30) ===
  [FIXE] L2-1: DEPOT → NORD (06:15 - 06:45)
  [AJOUTÉ] L2-2: NORD → CENTRE (07:00 - 07:30)
  [AJOUTÉ] L2-3: CENTRE → DEPOT (07:45 - 08:15)

=== Service S3 (06:00 - 11:00) ===
  [AJOUTÉ] L3-1: DEPOT → SUD (06:30 - 07:00)
  [AJOUTÉ] L3-2: SUD → GARE (07:15 - 07:45)
  [AJOUTÉ] L3-3: GARE → DEPOT (08:00 - 08:30)"""

services = [
    {"id": "S1", "debut": "05:30", "fin": "10:00", "voyages_assignes": [0, 1]},
    {"id": "S2", "debut": "06:00", "fin": "10:30", "voyages_assignes": [3]},
    {"id": "S3", "debut": "06:00", "fin": "11:00", "voyages_assignes": []},
]

# Tous les voyages (certains déjà assignés, d'autres à placer)
voyages = [
    # Voyages pré-assignés à S1
    ("L1", 1, "DEPOT", "CENTRE", "06:00", "06:30"),  # v0 → S1
    ("L1", 2, "CENTRE", "GARE", "06:45", "07:15"),  # v1 → S1

    # Voyage pré-assigné à S2
    ("L2", 1, "DEPOT", "NORD", "06:15", "06:45"),  # v3 → S2

    # Voyages à affecter (trouver le bon service)
    ("L1", 3, "GARE", "DEPOT", "07:30", "08:00"),  # v2 → ?
    ("L2", 2, "NORD", "CENTRE", "07:00", "07:30"),  # v4 → ?
    ("L2", 3, "CENTRE", "DEPOT", "07:45", "08:15"),  # v5 → ?
    ("L3", 1, "DEPOT", "SUD", "06:30", "07:00"),  # v6 → ?
    ("L3", 2, "SUD", "GARE", "07:15", "07:45"),  # v7 → ?
    ("L3", 3, "GARE", "DEPOT", "08:00", "08:30"),  # v8 → ?
]

pause_min = 10