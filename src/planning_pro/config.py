import os
from pathlib import Path


def load_env_file(env_file=".env"):
    """Charge les variables d'environnement depuis un fichier .env"""
    env_path = Path(env_file)
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Enlever les guillemets si présents
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ.setdefault(key, value)


# Charger le fichier .env s'il existe
load_env_file()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # Configuration pour les heures supplementaires
    TAUX_MAJORATION_HEURES_SUP = float(
        os.environ.get("TAUX_MAJORATION_HEURES_SUP", "1.25")
    )

    # Configuration email
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "smtp.gmail.com"
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in [
        "true",
        "on",
        "1",
    ]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # Configuration de débogage
    DEBUG = os.environ.get("DEBUG", "true").lower() in ["true", "on", "1"]
    TESTING = os.environ.get("TESTING", "false").lower() in ["true", "on", "1"]

    # Configuration de la base de données (optionnel)
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # Jours feries francais (a adapter selon vos besoins)
    JOURS_FERIES = [
        "01-01",  # Jour de l'an
        "05-01",  # Fete du travail
        "05-08",  # Victoire 1945
        "07-14",  # Fete nationale
        "08-15",  # Assomption
        "11-01",  # Toussaint
        "11-11",  # Armistice
        "12-25",  # Noel
    ]

    @staticmethod
    def calculer_heures_normales_mois(heures_semaine):
        """Calcule les heures normales mensuelles basees sur les heures hebdomadaires"""
        return heures_semaine * 52 / 12
