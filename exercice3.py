menu = {
    "burger": 12.50,
    "pizza": 14.00,
    "salade": 9.50,
    "pates": 11.00,
    "dessert": 6.50,
    "boisson": 3.50
}

commandes = [
    {"id": 1, "client": "Alice", "plats": ["burger", "boisson"], "statut": "livrée"},
    {"id": 2, "client": "Bob", "plats": ["pizza", "pizza", "boisson", "dessert"], "statut": "en cours"},
    {"id": 3, "client": "Clara", "plats": ["salade"], "statut": "annulée"},
    {"id": 4, "client": "David", "plats": ["pates", "dessert", "boisson"], "statut": "livrée"},
    {"id": 5, "client": "Alice", "plats": ["pizza", "salade", "boisson"], "statut": "en cours"},
]
"""
**Ta mission :**
1. `calculer_total(plats, menu)` → retourne le prix total d'une liste de plats
2. `afficher_commande(commande, menu)` → affiche les détails d'une commande formatée
3. `commandes_par_statut(commandes, statut)` → retourne les commandes filtrées par statut
4. `chiffre_affaires(commandes, menu)` → retourne le CA total (seulement les commandes "livrée")
5. `client_fidele(commandes)` → retourne le nom du client avec le plus de commandes
6. `plat_populaire(commandes)` → retourne le plat le plus commandé (tous statuts confondus)
**Résultat attendu :**
=== Commande #2 ===
Client : Bob
Plats : pizza, pizza, boisson, dessert
Total : 38.0€
Statut : en cours
Commandes en cours : 2
Chiffre d'affaires : 37.0€
Client fidèle : Alice (2 commandes)
Plat populaire : boisson (4 fois)
"""

def calculer_total(plats, menu):
    total = 0
    for plat in plats:
        if plat in menu:
            total += menu[plat]
    return total

def afficher_commande(commande, menu):
    pass

def commandes_par_statut(commandes, statut):
    resultat = []
    for commande in commandes:
        if commande["statut"] == statut:
            resultat.append(commande)
    return resultat

def chiffre_affaires(commandes, menu):
    ca = 0
    for commande in commandes:
        if commande["statut"] == "livrée":
            compte = calculer_total(commande["plats"], menu)
            ca += compte
    return ca


def client_fidele(commandes):
    compteur = {}
    for commande in commandes:
        client = commande["client"]
        if client in compteur:
            compteur[client] += 1
        else:
            compteur[client] = 1
    return compteur

def plat_populaire(commandes):
    compteur = {}
    for commande in commandes:
        for plat in commande["plats"]:

            if plat in compteur:
                compteur[plat] += 1
            else:
                compteur[plat] = 1
    return compteur

commande1 = calculer_total(commandes[1]["plats"], menu)
status = commandes_par_statut(commandes, "en cours")
CA = chiffre_affaires(commandes, menu)
compteur = client_fidele(commandes)
client = max(compteur, key=compteur.get)
print(client)

meilleurplat = plat_populaire(commandes)
print(meilleurplat)
best = max(meilleurplat, key=meilleurplat.get)
print(best)