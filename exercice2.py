inventaire = [
    {"produit": "Pommes", "prix": 2.50, "stock": 45},
    {"produit": "Pain", "prix": 1.20, "stock": 12},
    {"produit": "Lait", "prix": 1.80, "stock": 0},
    {"produit": "Œufs", "prix": 3.40, "stock": 30},
    {"produit": "Beurre", "prix": 2.10, "stock": 8},
]
"""
**Ta mission :**

1. Écris une fonction `valeur_stock(produit)` qui retourne la valeur totale d'un produit (prix × stock)

2. Écris une fonction `produits_en_rupture(inventaire)` qui retourne une **liste** des noms de produits avec un stock de 0

3. Écris une fonction `valeur_totale_magasin(inventaire)` qui retourne la somme des valeurs de tous les produits

4. Écris une fonction `produits_a_commander(inventaire, seuil)` qui retourne la liste des produits dont le stock est **inférieur ou égal** au seuil

**Résultat attendu :**
```
Valeur stock Pommes : 112.5€
Produits en rupture : ['Lait']
Valeur totale du magasin : 243.9€
Produits à commander (seuil 10) : ['Pain', 'Lait', 'Beurre']

"""

def valeur_stock(inventaire):
    return inventaire["prix"] * inventaire["stock"]

def produits_en_rupture(inventaire):
    for produit in inventaire:
        if produit["stock"] == 0:
            return produit["produit"]

def valeur_totale_magasin(inventaire):
    total = 0
    for produit in inventaire:
        total += valeur_stock(produit)
    return total

def produits_a_commander(inventaire, seuil):
    nom_produit_seuil = []
    for produit in inventaire:
        if produit["stock"] <= seuil:
            nom_produit_seuil.append(produit["produit"])
    return nom_produit_seuil
produit = "Pommes"
for invent in inventaire:
    if produit == invent["produit"]:
        valeur = valeur_stock(invent)
        print(f"Valeur stock",produit,":", valeur,"€")

rupture = produits_en_rupture(inventaire)
print(f"Produits en rupture : ['",rupture,"']")
total =valeur_totale_magasin(inventaire)
print("Valeur totale du magasin :",total,"€")
max = 10
seuilproduit = produits_a_commander(inventaire,max)
print(f"Produits à commander (seuil {max}) :", seuilproduit)