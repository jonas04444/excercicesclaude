"""
Module de logging centralisé.
Importer et utiliser dans tous les fichiers du projet.

Usage:
    from logger import get_logger
    logger = get_logger(__name__)

    logger.debug("Message détaillé")
    logger.info("Information")
    logger.warning("Attention")
    logger.error("Erreur")
    logger.critical("Erreur critique")
"""

import logging
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION PAR DÉFAUT
# =============================================================================

CONFIG = {
    "niveau_console": logging.INFO,
    "niveau_fichier": logging.DEBUG,
    "dossier_logs": "logs",
    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s",
    "format_date": "%Y-%m-%d %H:%M:%S",
}

# Variable globale pour le fichier log actif
_fichier_log_actif = None
_initialise = False


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def initialiser(
        fichier_log=None,
        niveau_console=None,
        niveau_fichier=None,
        dossier_logs=None
):
    """
    Initialise le système de logging (à appeler une fois au démarrage).

    Args:
        fichier_log: Nom du fichier log (ex: "optimisation.log")
                     Si None, génère un nom avec timestamp
        niveau_console: Niveau pour la console (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        niveau_fichier: Niveau pour le fichier
        dossier_logs: Dossier où stocker les logs

    Exemple:
        from logger import initialiser
        initialiser(fichier_log="mon_app.log", niveau_console=logging.DEBUG)
    """
    global _fichier_log_actif, _initialise

    # Mettre à jour la config si spécifié
    if niveau_console:
        CONFIG["niveau_console"] = niveau_console
    if niveau_fichier:
        CONFIG["niveau_fichier"] = niveau_fichier
    if dossier_logs:
        CONFIG["dossier_logs"] = dossier_logs

    # Créer le dossier logs si nécessaire
    if CONFIG["dossier_logs"] and not os.path.exists(CONFIG["dossier_logs"]):
        os.makedirs(CONFIG["dossier_logs"])

    # Définir le chemin du fichier log
    if fichier_log:
        if CONFIG["dossier_logs"]:
            _fichier_log_actif = os.path.join(CONFIG["dossier_logs"], fichier_log)
        else:
            _fichier_log_actif = fichier_log
    else:
        # Générer un nom avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_fichier = f"log_{timestamp}.log"
        if CONFIG["dossier_logs"]:
            _fichier_log_actif = os.path.join(CONFIG["dossier_logs"], nom_fichier)
        else:
            _fichier_log_actif = nom_fichier

    _initialise = True

    # Retourner le chemin pour info
    return _fichier_log_actif


def get_logger(nom=None):
    """
    Retourne un logger configuré.

    Args:
        nom: Nom du logger (utiliser __name__ pour le nom du module)

    Returns:
        Logger configuré

    Exemple:
        from logger import get_logger
        logger = get_logger(__name__)
        logger.info("Ça marche!")
    """
    if nom is None:
        nom = "app"

    logger = logging.getLogger(nom)

    # Éviter les doublons
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)  # Capturer tout, filtrer par handler

    # Formatter
    formatter = logging.Formatter(
        CONFIG["format"],
        datefmt=CONFIG["format_date"]
    )

    # Handler console
    handler_console = logging.StreamHandler()
    handler_console.setLevel(CONFIG["niveau_console"])
    handler_console.setFormatter(formatter)
    logger.addHandler(handler_console)

    # Handler fichier (si initialisé)
    if _fichier_log_actif:
        handler_fichier = logging.FileHandler(
            _fichier_log_actif,
            encoding="utf-8"
        )
        handler_fichier.setLevel(CONFIG["niveau_fichier"])
        handler_fichier.setFormatter(formatter)
        logger.addHandler(handler_fichier)

    return logger


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def set_niveau_console(niveau):
    """Change le niveau de log pour la console (pour tous les loggers)."""
    CONFIG["niveau_console"] = niveau

    # Mettre à jour les handlers existants
    for name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(niveau)


def set_niveau_fichier(niveau):
    """Change le niveau de log pour le fichier (pour tous les loggers)."""
    CONFIG["niveau_fichier"] = niveau

    for name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setLevel(niveau)


def get_chemin_log():
    """Retourne le chemin du fichier log actif."""
    return _fichier_log_actif


def log_exception(logger, message="Exception capturée"):
    """
    Log une exception avec sa stack trace complète.
    À utiliser dans un bloc except.

    Exemple:
        try:
            fonction_risquee()
        except Exception:
            log_exception(logger, "Erreur dans fonction_risquee")
    """
    logger.error(message, exc_info=True)


# =============================================================================
# DÉCORATEUR POUR TRACER LES FONCTIONS
# =============================================================================

def trace_fonction(logger):
    """
    Décorateur pour logger automatiquement l'entrée/sortie d'une fonction.

    Exemple:
        @trace_fonction(logger)
        def ma_fonction(x, y):
            return x + y
    """

    def decorateur(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"→ Entrée {func.__name__}(args={args}, kwargs={kwargs})")
            try:
                resultat = func(*args, **kwargs)
                logger.debug(f"← Sortie {func.__name__} = {resultat}")
                return resultat
            except Exception as e:
                logger.error(f"✗ Exception dans {func.__name__}: {e}", exc_info=True)
                raise

        return wrapper

    return decorateur