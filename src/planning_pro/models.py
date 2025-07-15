from datetime import datetime, timedelta
from typing import List, Dict, Optional
import calendar
import json
import os
import bcrypt
import secrets
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer


class DataStore:
    """Simple file-based data storage"""

    def __init__(self, filename: str):
        self.filename = filename
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.filepath = os.path.join(self.data_dir, filename)

    def load(self) -> List[Dict]:
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def save(self, data: List[Dict]):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class User(UserMixin):
    store = DataStore("users.json")

    def __init__(
        self,
        email: str,
        password: str,
        nom: str,
        prenom: str,
        id: Optional[int] = None,
    ):
        self.id = id or self._get_next_id()
        self.email = email.lower().strip()
        self.password_hash = self._hash_password(password) if password else None
        self.nom = nom.strip()
        self.prenom = prenom.strip()
        self.created_at = datetime.now().isoformat()
        self.active = True
        self.reset_token: Optional[str] = None
        self.reset_token_expiry: Optional[str] = None

    def _get_next_id(self) -> int:
        users = self.store.load()
        return max([u.get("id", 0) for u in users], default=0) + 1

    def _hash_password(self, password: str) -> str:
        """Hache le mot de passe avec bcrypt"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """Vérifie si le mot de passe est correct"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def get_id(self):
        """Requis par Flask-Login"""
        return str(self.id)

    def save(self):
        users = self.store.load()

        # Mettre à jour ou ajouter
        for i, u in enumerate(users):
            if u.get("id") == self.id:
                users[i] = self.to_dict()
                break
        else:
            users.append(self.to_dict())

        self.store.save(users)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "email": self.email,
            "password_hash": self.password_hash,
            "nom": self.nom,
            "prenom": self.prenom,
            "created_at": self.created_at,
            "is_active": self.active,
            "reset_token": self.reset_token,
            "reset_token_expiry": self.reset_token_expiry,
        }

    @classmethod
    def get_by_email(cls, email: str) -> Optional["User"]:
        """Trouve un utilisateur par email"""
        users_data = cls.store.load()
        for u in users_data:
            if u.get("email", "").lower() == email.lower().strip():
                return cls.from_dict(u)
        return None

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional["User"]:
        """Trouve un utilisateur par ID"""
        users_data = cls.store.load()
        for u in users_data:
            if u.get("id") == user_id:
                return cls.from_dict(u)
        return None

    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        user = cls.__new__(cls)
        user.id = data["id"]
        user.email = data["email"]
        user.password_hash = data.get("password_hash")
        user.nom = data["nom"]
        user.prenom = data["prenom"]
        user.created_at = data["created_at"]
        user.active = data.get("is_active", True)
        user.reset_token = data.get("reset_token")
        user.reset_token_expiry = data.get("reset_token_expiry")
        return user

    def generate_reset_token(self) -> str:
        """Génère un token de réinitialisation de mot de passe"""
        token = secrets.token_urlsafe(32)
        expiry = (datetime.now() + timedelta(hours=1)).isoformat()
        self.reset_token = token
        self.reset_token_expiry = expiry
        self.save()
        return token

    def verify_reset_token(self, token: str) -> bool:
        """Vérifie si le token de réinitialisation est valide"""
        if not self.reset_token or not self.reset_token_expiry:
            return False

        if self.reset_token != token:
            return False

        expiry = datetime.fromisoformat(self.reset_token_expiry)
        if datetime.now() > expiry:
            return False

        return True

    def reset_password(self, new_password: str, token: str) -> bool:
        """Réinitialise le mot de passe avec un token valide"""
        if not self.verify_reset_token(token):
            return False

        self.password_hash = self._hash_password(new_password)
        self.reset_token = None
        self.reset_token_expiry = None
        self.save()
        return True

    @classmethod
    def get_by_reset_token(cls, token: str) -> Optional["User"]:
        """Trouve un utilisateur par token de réinitialisation"""
        users_data = cls.store.load()
        for u in users_data:
            if u.get("reset_token") == token:
                user = cls.from_dict(u)
                if user.verify_reset_token(token):
                    return user
        return None

    def __repr__(self):
        return f"<User {self.email}>"


class CreneauTravail:
    def __init__(self, heure_debut: str, heure_fin: str):
        self.heure_debut = heure_debut
        self.heure_fin = heure_fin

    def calculer_heures(self, date: str) -> float:
        """Calcule le nombre d'heures pour ce créneau"""
        debut = datetime.strptime(f"{date} {self.heure_debut}", "%Y-%m-%d %H:%M")
        fin = datetime.strptime(f"{date} {self.heure_fin}", "%Y-%m-%d %H:%M")

        # Gérer le cas où le créneau se termine le lendemain (ex: 23:00 - 02:00)
        if fin <= debut:
            fin += timedelta(days=1)

        duree = fin - debut
        return max(0, duree.total_seconds() / 3600)

    def to_dict(self) -> Dict:
        return {"heure_debut": self.heure_debut, "heure_fin": self.heure_fin}


class JourTravaille:
    def __init__(self, date: str, creneaux: Optional[List[CreneauTravail]] = None):
        self.date = date
        self.creneaux = creneaux if creneaux else []

    def ajouter_creneau(self, heure_debut: str, heure_fin: str):
        """Ajoute un créneau de travail à la journée"""
        self.creneaux.append(CreneauTravail(heure_debut, heure_fin))

    def calculer_heures(self) -> float:
        """Calcule le nombre total d'heures travaillees dans la journee"""
        total = 0.0
        for creneau in self.creneaux:
            total += creneau.calculer_heures(self.date)
        return total

    def to_dict(self) -> Dict:
        return {
            "date": self.date,
            "creneaux": [creneau.to_dict() for creneau in self.creneaux],
            "heures": self.calculer_heures(),
        }


class Planning:
    store = DataStore("plannings.json")

    def __init__(
        self,
        mois: int,
        annee: int,
        jours_travail: List[Dict],
        taux_horaire: float,
        user_id: int,
        heures_contractuelles: float = 35.0,
        id: Optional[int] = None,
    ):
        self.id = id or self._get_next_id()
        self.mois = mois
        self.annee = annee
        self.jours_travail = jours_travail
        self.taux_horaire = taux_horaire
        self.user_id = user_id
        self.heures_contractuelles = heures_contractuelles  # Heures par semaine
        self.created_at = datetime.now().isoformat()

    def _get_next_id(self) -> int:
        plannings = self.store.load()
        return max([p.get("id", 0) for p in plannings], default=0) + 1

    def save(self):
        plannings = self.store.load()

        # Mettre � jour ou ajouter
        for i, p in enumerate(plannings):
            if p.get("id") == self.id:
                plannings[i] = self.to_dict()
                break
        else:
            plannings.append(self.to_dict())

        self.store.save(plannings)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "mois": self.mois,
            "annee": self.annee,
            "jours_travail": self.jours_travail,
            "taux_horaire": self.taux_horaire,
            "user_id": self.user_id,
            "heures_contractuelles": self.heures_contractuelles,
            "created_at": self.created_at,
        }

    def to_feuille_heures(self) -> "FeuilleDHeures":
        """Convertit le planning en feuille d'heures (écrase si existante)"""
        jours_travailles = []

        for jour in self.jours_travail:
            jour_travaille = JourTravaille(date=jour["date"])

            # Ajouter les créneaux de travail
            for creneau in jour.get("creneaux", []):
                jour_travaille.ajouter_creneau(
                    creneau["heure_debut"], creneau["heure_fin"]
                )

            jours_travailles.append(jour_travaille)

        # Vérifier si une feuille d'heures existe déjà pour ce mois/année et cet utilisateur
        feuille_existante = FeuilleDHeures.get_by_mois_annee_user(
            self.mois, self.annee, self.user_id
        )

        if feuille_existante:
            # Mettre à jour la feuille existante
            feuille_existante.jours_travailles = jours_travailles
            feuille_existante.taux_horaire = self.taux_horaire
            feuille_existante.heures_contractuelles = self.heures_contractuelles
            feuille_existante.save()
            return feuille_existante
        else:
            # Créer une nouvelle feuille
            feuille = FeuilleDHeures(
                mois=self.mois,
                annee=self.annee,
                jours_travailles=jours_travailles,
                taux_horaire=self.taux_horaire,
                user_id=self.user_id,
                heures_contractuelles=self.heures_contractuelles,
            )
            feuille.save()
            return feuille

    @classmethod
    def get_all(cls) -> List["Planning"]:
        plannings_data = cls.store.load()
        return [cls.from_dict(p) for p in plannings_data]

    @classmethod
    def get_by_user(cls, user_id: int) -> List["Planning"]:
        """Récupère tous les plannings d'un utilisateur"""
        plannings_data = cls.store.load()
        return [cls.from_dict(p) for p in plannings_data if p.get("user_id") == user_id]

    @classmethod
    def get_by_id(cls, id: int) -> Optional["Planning"]:
        plannings_data = cls.store.load()
        for p in plannings_data:
            if p.get("id") == id:
                return cls.from_dict(p)
        return None

    @classmethod
    def from_dict(cls, data: Dict) -> "Planning":
        return cls(
            id=data["id"],
            mois=data["mois"],
            annee=data["annee"],
            jours_travail=data["jours_travail"],
            taux_horaire=data["taux_horaire"],
            user_id=data.get("user_id", 1),  # Compatibilité avec anciens plannings
            heures_contractuelles=data.get(
                "heures_contractuelles", 35.0
            ),  # Compatibilité avec anciens plannings
        )


class FeuilleDHeures:
    store = DataStore("feuilles_heures.json")

    def __init__(
        self,
        mois: int,
        annee: int,
        jours_travailles: List[JourTravaille],
        taux_horaire: float,
        user_id: int,
        heures_contractuelles: float = 35.0,
        id: Optional[int] = None,
    ):
        self.id = id or self._get_next_id()
        self.mois = mois
        self.annee = annee
        self.jours_travailles = jours_travailles
        self.taux_horaire = taux_horaire
        self.user_id = user_id
        self.heures_contractuelles = heures_contractuelles
        self.created_at = datetime.now().isoformat()

    def _get_next_id(self) -> int:
        feuilles = self.store.load()
        return max([f.get("id", 0) for f in feuilles], default=0) + 1

    def calculer_total_heures(self) -> float:
        """Calcule le total des heures travaillees"""
        return sum(jour.calculer_heures() for jour in self.jours_travailles)

    def calculer_heures_supplementaires(self) -> Dict:
        """Calcule les heures supplementaires"""
        from .config import Config

        total_heures = self.calculer_total_heures()
        heures_normales_mois = Config.calculer_heures_normales_mois(
            self.heures_contractuelles
        )

        if total_heures > heures_normales_mois:
            heures_sup = total_heures - heures_normales_mois
            return {
                "heures_normales": heures_normales_mois,
                "heures_supplementaires": heures_sup,
                "total_heures": total_heures,
            }
        else:
            return {
                "heures_normales": total_heures,
                "heures_supplementaires": 0,
                "total_heures": total_heures,
            }

    def calculer_salaire(self) -> Dict:
        """Calcule le salaire brut estime"""
        from .config import Config

        heures_detail = self.calculer_heures_supplementaires()

        salaire_normal = heures_detail["heures_normales"] * self.taux_horaire
        salaire_sup = (
            heures_detail["heures_supplementaires"]
            * self.taux_horaire
            * Config.TAUX_MAJORATION_HEURES_SUP
        )

        return {
            "heures_normales": heures_detail["heures_normales"],
            "heures_supplementaires": heures_detail["heures_supplementaires"],
            "total_heures": heures_detail["total_heures"],
            "heures_contractuelles": self.heures_contractuelles,
            "taux_horaire": self.taux_horaire,
            "salaire_normal": salaire_normal,
            "salaire_supplementaire": salaire_sup,
            "salaire_brut_total": salaire_normal + salaire_sup,
        }

    def save(self):
        feuilles = self.store.load()

        # Mettre � jour ou ajouter
        for i, f in enumerate(feuilles):
            if f.get("id") == self.id:
                feuilles[i] = self.to_dict()
                break
        else:
            feuilles.append(self.to_dict())

        self.store.save(feuilles)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "mois": self.mois,
            "annee": self.annee,
            "jours_travailles": [jour.to_dict() for jour in self.jours_travailles],
            "taux_horaire": self.taux_horaire,
            "user_id": self.user_id,
            "heures_contractuelles": self.heures_contractuelles,
            "created_at": self.created_at,
            "total_heures": self.calculer_total_heures(),
            "calcul_salaire": self.calculer_salaire(),
        }

    @classmethod
    def get_all(cls) -> List["FeuilleDHeures"]:
        feuilles_data = cls.store.load()
        return [cls.from_dict(f) for f in feuilles_data]

    @classmethod
    def get_by_user(cls, user_id: int) -> List["FeuilleDHeures"]:
        """Récupère toutes les feuilles d'heures d'un utilisateur"""
        feuilles_data = cls.store.load()
        return [cls.from_dict(f) for f in feuilles_data if f.get("user_id") == user_id]

    @classmethod
    def get_by_id(cls, id: int) -> Optional["FeuilleDHeures"]:
        feuilles_data = cls.store.load()
        for f in feuilles_data:
            if f.get("id") == id:
                return cls.from_dict(f)
        return None

    @classmethod
    def get_by_mois_annee(cls, mois: int, annee: int) -> Optional["FeuilleDHeures"]:
        """Trouve une feuille d'heures existante pour un mois/année donné (compatibilité)"""
        feuilles_data = cls.store.load()
        for f in feuilles_data:
            if f.get("mois") == mois and f.get("annee") == annee:
                return cls.from_dict(f)
        return None

    @classmethod
    def get_by_mois_annee_user(
        cls, mois: int, annee: int, user_id: int
    ) -> Optional["FeuilleDHeures"]:
        """Trouve une feuille d'heures existante pour un mois/année/utilisateur donné"""
        feuilles_data = cls.store.load()
        for f in feuilles_data:
            if (
                f.get("mois") == mois
                and f.get("annee") == annee
                and f.get("user_id") == user_id
            ):
                return cls.from_dict(f)
        return None

    @classmethod
    def from_dict(cls, data: Dict) -> "FeuilleDHeures":
        jours_travailles = []
        for jour_data in data["jours_travailles"]:
            jour = JourTravaille(date=jour_data["date"])

            # Charger les créneaux de travail
            for creneau_data in jour_data.get("creneaux", []):
                jour.ajouter_creneau(
                    creneau_data["heure_debut"], creneau_data["heure_fin"]
                )

            jours_travailles.append(jour)

        return cls(
            id=data["id"],
            mois=data["mois"],
            annee=data["annee"],
            jours_travailles=jours_travailles,
            taux_horaire=data["taux_horaire"],
            user_id=data.get("user_id", 1),  # Compatibilité avec anciennes feuilles
            heures_contractuelles=data.get(
                "heures_contractuelles", 35.0
            ),  # Compatibilité avec anciennes feuilles
        )
