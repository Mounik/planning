"""
Module de sécurité pour l'application Planning Pro
"""

import re
import html
import logging
from functools import wraps
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from flask import request, jsonify, current_app
from werkzeug.exceptions import BadRequest


# Configuration du logging de sécurité
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Patterns de validation
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$")
NAME_PATTERN = re.compile(r"^[a-zA-ZÀ-ÿ\s\-\']{2,50}$")
TIME_PATTERN = re.compile(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class SecurityValidator:
    """Classe pour la validation et la sécurisation des données"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Valide un email"""
        if not email or len(email) > 254:
            return False
        return bool(EMAIL_PATTERN.match(email.strip().lower()))

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Valide un mot de passe fort"""
        if not password:
            return False, "Le mot de passe est requis"

        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"

        if len(password) > 128:
            return False, "Le mot de passe ne peut pas dépasser 128 caractères"

        if not re.search(r"[a-z]", password):
            return False, "Le mot de passe doit contenir au moins une minuscule"

        if not re.search(r"[A-Z]", password):
            return False, "Le mot de passe doit contenir au moins une majuscule"

        if not re.search(r"\d", password):
            return False, "Le mot de passe doit contenir au moins un chiffre"

        return True, "Mot de passe valide"

    @staticmethod
    def validate_name(name: str) -> bool:
        """Valide un nom/prénom"""
        if not name or len(name.strip()) < 2:
            return False
        return bool(NAME_PATTERN.match(name.strip()))

    @staticmethod
    def validate_time(time_str: str) -> bool:
        """Valide un horaire HH:MM"""
        if not time_str:
            return False
        return bool(TIME_PATTERN.match(time_str.strip()))

    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Valide une date YYYY-MM-DD"""
        if not date_str:
            return False
        if not DATE_PATTERN.match(date_str.strip()):
            return False

        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_numeric(
        value: Union[str, int, float], min_val: float = None, max_val: float = None
    ) -> bool:
        """Valide une valeur numérique"""
        try:
            num_value = float(value)
            if min_val is not None and num_value < min_val:
                return False
            if max_val is not None and num_value > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def sanitize_string(value: str) -> str:
        """Échappe les caractères HTML dangereux"""
        if not value:
            return ""
        return html.escape(value.strip())

    @staticmethod
    def validate_planning_data(data: Dict[str, Any]) -> tuple[bool, str]:
        """Valide les données d'un planning"""
        if not isinstance(data, dict):
            return False, "Données invalides"

        # Validation du mois
        if not SecurityValidator.validate_numeric(data.get("mois"), 1, 12):
            return False, "Mois invalide (1-12)"

        # Validation de l'année
        current_year = datetime.now().year
        if not SecurityValidator.validate_numeric(
            data.get("annee"), current_year - 5, current_year + 5
        ):
            return False, f"Année invalide ({current_year - 5}-{current_year + 5})"

        # Validation du taux horaire
        if not SecurityValidator.validate_numeric(data.get("taux_horaire"), 0.01, 1000):
            return False, "Taux horaire invalide (0.01-1000)"

        # Validation des heures contractuelles
        if not SecurityValidator.validate_numeric(
            data.get("heures_contractuelles"), 1, 60
        ):
            return False, "Heures contractuelles invalides (1-60)"

        # Validation des jours de travail
        jours_travail = data.get("jours_travail", [])
        if not isinstance(jours_travail, list):
            return False, "Jours de travail invalides"

        if len(jours_travail) > 31:
            return False, "Trop de jours de travail"

        for jour in jours_travail:
            if not isinstance(jour, dict):
                return False, "Format de jour invalide"

            # Validation de la date
            if not SecurityValidator.validate_date(jour.get("date")):
                return False, f"Date invalide: {jour.get('date')}"

            # Validation des créneaux
            creneaux = jour.get("creneaux", [])
            if not isinstance(creneaux, list):
                return False, "Créneaux invalides"

            if len(creneaux) > 10:  # Maximum 10 créneaux par jour
                return False, "Trop de créneaux par jour"

            for creneau in creneaux:
                if not isinstance(creneau, dict):
                    return False, "Format de créneau invalide"

                if not SecurityValidator.validate_time(creneau.get("heure_debut")):
                    return (
                        False,
                        f"Heure de début invalide: {creneau.get('heure_debut')}",
                    )

                if not SecurityValidator.validate_time(creneau.get("heure_fin")):
                    return False, f"Heure de fin invalide: {creneau.get('heure_fin')}"

        return True, "Données valides"


def require_json(f):
    """Décorateur pour exiger un Content-Type JSON"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            security_logger.warning(
                f"Non-JSON request to {request.endpoint} from {request.remote_addr}"
            )
            return jsonify({"error": "Content-Type must be application/json"}), 400
        return f(*args, **kwargs)

    return decorated_function


def rate_limit(max_requests: int = 100, window_seconds: int = 3600):
    """Décorateur simple de limitation de taux (rate limiting)"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implémentation basique - en production, utiliser Redis ou memcached
            client_ip = request.remote_addr
            current_time = datetime.now()

            # Pour cette implémentation, on accepte toutes les requêtes
            # En production, implémenter un vrai rate limiting
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_security_event(
    event_type: str,
    message: str,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
):
    """Log un événement de sécurité"""
    if not ip_address:
        ip_address = request.remote_addr if request else "unknown"

    security_logger.info(
        f"SECURITY_EVENT: {event_type} | IP: {ip_address} | User: {user_id} | Message: {message}"
    )


def validate_json_data(
    data: Dict[str, Any], schema: Dict[str, Any]
) -> tuple[bool, str]:
    """Valide les données JSON selon un schéma simple"""
    if not isinstance(data, dict):
        return False, "Les données doivent être un objet JSON"

    for field, requirements in schema.items():
        if requirements.get("required", False) and field not in data:
            return False, f"Le champ '{field}' est requis"

        if field in data:
            value = data[field]
            field_type = requirements.get("type")

            if field_type and not isinstance(value, field_type):
                return (
                    False,
                    f"Le champ '{field}' doit être de type {field_type.__name__}",
                )

            if (
                "min_length" in requirements
                and len(str(value)) < requirements["min_length"]
            ):
                return (
                    False,
                    f"Le champ '{field}' doit contenir au moins {requirements['min_length']} caractères",
                )

            if (
                "max_length" in requirements
                and len(str(value)) > requirements["max_length"]
            ):
                return (
                    False,
                    f"Le champ '{field}' ne peut pas dépasser {requirements['max_length']} caractères",
                )

    return True, "Données valides"


# Schémas de validation
USER_REGISTRATION_SCHEMA = {
    "email": {"type": str, "required": True, "max_length": 254},
    "password": {"type": str, "required": True, "min_length": 8, "max_length": 128},
    "nom": {"type": str, "required": True, "min_length": 2, "max_length": 50},
    "prenom": {"type": str, "required": True, "min_length": 2, "max_length": 50},
}

USER_LOGIN_SCHEMA = {
    "email": {"type": str, "required": True, "max_length": 254},
    "password": {"type": str, "required": True, "min_length": 1, "max_length": 128},
}

PLANNING_SCHEMA = {
    "mois": {"type": int, "required": True},
    "annee": {"type": int, "required": True},
    "taux_horaire": {"type": (int, float), "required": True},
    "heures_contractuelles": {"type": (int, float), "required": True},
    "jours_travail": {"type": list, "required": True},
}


# Instance globale du validateur
validator = SecurityValidator()
