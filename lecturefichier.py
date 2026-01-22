etudiants = [
    {"nom": "Alice", "notes": [15, 12, 18, 14]},
    {"nom": "Bob", "notes": [8, 10, 7, 12]},
    {"nom": "Clara", "notes": [16, 17, 15, 19]},
    {"nom": "David", "notes": [11, 9, 13, 10]},
]

def moyenne2(etudiants,i):
    return sum(etudiants[i]["notes"])/len(etudiants[i]["notes"])

def nom_etudiant(etudiants,i):
    return etudiants[i]["nom"]


def calculer_moyenne(notes):
    """Prend une liste de notes, retourne la moyenne"""
    return sum(notes) / len(notes)


def best_student(etudiants):
    meilleure_moyenne = 0
    meilleur_nom = ""

    for etudiant in etudiants:
        moyenne = calculer_moyenne(etudiant["notes"])
        if moyenne > meilleure_moyenne:
            meilleure_moyenne = moyenne
            meilleur_nom = etudiant["nom"]

    return meilleur_nom

for etudiant in range(len(etudiants)):
    print(nom_etudiant(etudiants,etudiant)," : ",moyenne2(etudiants,etudiant))

print(best_student(etudiants))