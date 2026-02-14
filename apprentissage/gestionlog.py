"""
EXERCICE : Système de Logging pour une Application de Gestion de Tâches
=========================================================================

Objectif : Créer un système de logging complet pour une application de gestion de tâches.

PARTIE 1 : Configuration de base (Facile)
------------------------------------------
Créez un logger qui :
- Enregistre dans un fichier 'todo_app.log'
- Affiche aussi les messages dans la console
- Utilise le format : '%(asctime)s - [%(levelname)s] - %(message)s'
- Capture tous les messages de niveau INFO et supérieur

TODO 1 : Configurez votre logger ici


"""

import logging

from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

# PARTIE 1 : Configuration de base
# ---------------------------------

# Créer un logger personnalisé
logger = logging.getLogger('todo_app')
logger.setLevel(logging.DEBUG)

# Handler pour fichier
timed_handler = logging.FileHandler('todo_app.log', encoding='utf-8')
timed_handler.setLevel(logging.INFO)

# Handler pour console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Format
formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
timed_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Ajouter les handlers
logger.addHandler(timed_handler)
logger.addHandler(console_handler)


"""
PARTIE 2 : Classe TaskManager avec Logging (Moyen)
---------------------------------------------------
Complétez la classe TaskManager ci-dessous en ajoutant des logs appropriés :
- INFO quand une tâche est ajoutée
- INFO quand une tâche est complétée
- WARNING quand on essaie de compléter une tâche inexistante
- ERROR quand on essaie d'ajouter une tâche vide
- DEBUG pour afficher le nombre total de tâches
"""


class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.task_id = 0
        # TODO 2 : Ajoutez un log INFO indiquant que le TaskManager est initialisé
        logger.info("TaskManager est initialisé")

    def add_task(self, description):
        """Ajoute une nouvelle tâche"""
        if not description or description.strip() == "":
            # TODO 3 : Ajoutez un log ERROR
            logger.error("ERROR")
            return None

        self.task_id += 1
        self.tasks[self.task_id] = {
            'description': description,
            'completed': False
        }
        # TODO 4 : Ajoutez un log INFO avec l'ID et la description
        logger.info(self.tasks.description)
        # TODO 5 : Ajoutez un log DEBUG avec le nombre total de tâches
        logger.debug(self.tasks[self.task_id])
        return self.task_id

    def complete_task(self, task_id):
        """Marque une tâche comme complétée"""
        if task_id not in self.tasks:
            # TODO 6 : Ajoutez un log WARNING
            logger.warning('todo6')
            return False

        self.tasks[task_id]['completed'] = True
        # TODO 7 : Ajoutez un log INFO
        logger.info(self.tasks)
        return True

    def list_tasks(self):
        """Liste toutes les tâches"""
        # TODO 8 : Ajoutez un log DEBUG
        logger.debug(self.tasks)
        return self.tasks


"""
PARTIE 3 : Rotation des logs (Avancé)
--------------------------------------
Modifiez votre configuration pour :
- Créer un nouveau fichier de log chaque jour (rotation quotidienne)
- Garder maximum 7 jours d'historique
- Limiter la taille du fichier à 1MB

TODO 9 : Utilisez RotatingFileHandler ou TimedRotatingFileHandler
Indice : from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
"""

# TODO 9 : Votre code ici
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

rotating_handler = RotatingFileHandler(
    "todo_app.log",
    maxBytes=1024*1024,
    backupCount=7,
    encoding="utf-8"
)
rotating_handler.setLevel(logging.INFO)
rotating_handler.setFormatter(formatter)

timed_handler = TimedRotatingFileHandler(
    "todo_app.log",
    when='midnight',
    interval=1,
    backupCount=7,
    encoding="utf-8"
)
timed_handler.setLevel(logging.INFO)
rotating_handler.setFormatter(formatter)


"""
PARTIE 4 : Test de votre système (Testez tout !)
-------------------------------------------------
"""

if __name__ == "__main__":
    print("=== Test du système de logging ===\n")

    # Créer une instance du TaskManager
    manager = TaskManager()

    # Ajout de tâches valides
    print("\n--- Ajout de tâches ---")
    manager.add_task("Apprendre Python")
    manager.add_task("Faire les courses")
    manager.add_task("Réviser le logging")

    # Tentative d'ajout de tâches vides
    print("\n--- Test des erreurs ---")
    manager.add_task("")
    manager.add_task("   ")

    # Compléter des tâches
    print("\n--- Complétion de tâches ---")
    manager.complete_task(1)
    manager.complete_task(3)

    # Tentative de compléter une tâche inexistante
    print("\n--- Test des warnings ---")
    manager.complete_task(999)

    print("\n--- Liste des tâches ---")
    tasks = manager.list_tasks()
    for task_id, task_info in tasks.items():
        status = "✓" if task_info['completed'] else "○"
        print(f"{status} Tâche {task_id}: {task_info['description']}")

    print("\n=== Vérifiez le fichier 'todo_app.log' pour voir tous les logs ===")

"""
BONUS : Challenges supplémentaires
-----------------------------------
1. Ajoutez un handler qui envoie les erreurs critiques dans un fichier séparé 'errors.log'
2. Créez un décorateur qui log automatiquement l'entrée et la sortie de chaque méthode
3. Ajoutez des informations contextuelles (nom de l'utilisateur, timestamp précis) à chaque log
4. Implémentez un système qui envoie un email (simulé) quand une erreur CRITICAL survient

Amusez-vous bien !
"""