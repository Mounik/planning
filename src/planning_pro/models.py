from datetime import datetime, timedelta
from typing import List, Dict, Optional
import bcrypt
import secrets
from flask_login import UserMixin

from .database import db_manager
from .net_salary_calculator import net_salary_calculator


class User(UserMixin):
    """Modèle User avec stockage SQLite"""

    def __init__(
        self,
        email: str,
        password: str,
        nom: str,
        prenom: str,
        id: Optional[int] = None,
    ):
        self.id = id
        self.email = email.lower().strip()
        self.password_hash = self._hash_password(password) if password else None
        self.nom = nom.strip()
        self.prenom = prenom.strip()
        self.created_at = datetime.now().isoformat()
        self.active = True
        self.reset_token: Optional[str] = None
        self.reset_token_expiry: Optional[str] = None

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
        """Sauvegarde l'utilisateur en base de données"""
        if self.id:
            # Mise à jour
            db_manager.execute_update(
                """UPDATE users SET email = ?, password_hash = ?, nom = ?, prenom = ?, 
                   is_active = ?, reset_token = ?, reset_token_expiry = ? WHERE id = ?""",
                (
                    self.email,
                    self.password_hash,
                    self.nom,
                    self.prenom,
                    self.active,
                    self.reset_token,
                    self.reset_token_expiry,
                    self.id,
                ),
            )
        else:
            # Création
            self.id = db_manager.execute_insert(
                """INSERT INTO users (email, password_hash, nom, prenom, created_at, is_active, 
                   reset_token, reset_token_expiry) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    self.email,
                    self.password_hash,
                    self.nom,
                    self.prenom,
                    self.created_at,
                    self.active,
                    self.reset_token,
                    self.reset_token_expiry,
                ),
            )

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
        rows = db_manager.execute_query(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        )
        if rows:
            return cls.from_row(rows[0])
        return None

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional["User"]:
        """Trouve un utilisateur par ID"""
        rows = db_manager.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
        if rows:
            return cls.from_row(rows[0])
        return None

    @classmethod
    def from_row(cls, row) -> "User":
        """Crée un utilisateur à partir d'une ligne de base de données"""
        user = cls.__new__(cls)
        user.id = row["id"]
        user.email = row["email"]
        user.password_hash = row["password_hash"]
        user.nom = row["nom"]
        user.prenom = row["prenom"]
        user.created_at = row["created_at"]
        user.active = bool(row["is_active"])
        user.reset_token = row["reset_token"]
        user.reset_token_expiry = row["reset_token_expiry"]
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
        rows = db_manager.execute_query(
            "SELECT * FROM users WHERE reset_token = ?", (token,)
        )
        if rows:
            user = cls.from_row(rows[0])
            if user.verify_reset_token(token):
                return user
        return None

    def __repr__(self):
        return f"<User {self.email}>"


class CreneauTravail:
    """Créneau de travail avec heures de début et fin"""

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
    """Jour de travail avec créneaux horaires"""

    def __init__(self, date: str, creneaux: Optional[List[CreneauTravail]] = None):
        self.date = date
        self.creneaux = creneaux if creneaux else []

    def ajouter_creneau(self, heure_debut: str, heure_fin: str):
        """Ajoute un créneau de travail à la journée"""
        self.creneaux.append(CreneauTravail(heure_debut, heure_fin))

    def calculer_heures(self) -> float:
        """Calcule le nombre total d'heures travaillées dans la journée"""
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
    """Planning de travail avec stockage SQLite"""

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
        self.id = id
        self.mois = mois
        self.annee = annee
        self.jours_travail = jours_travail
        self.taux_horaire = taux_horaire
        self.user_id = user_id
        self.heures_contractuelles = heures_contractuelles
        self.created_at = datetime.now().isoformat()

    def save(self):
        """Sauvegarde le planning en base de données"""
        if self.id:
            # Mise à jour
            db_manager.execute_update(
                """UPDATE plannings SET mois = ?, annee = ?, taux_horaire = ?, 
                   heures_contractuelles = ? WHERE id = ?""",
                (
                    self.mois,
                    self.annee,
                    self.taux_horaire,
                    self.heures_contractuelles,
                    self.id,
                ),
            )
            # Supprimer les anciens jours de travail
            db_manager.execute_delete(
                "DELETE FROM jours_travail WHERE planning_id = ?", (self.id,)
            )
        else:
            # Création
            self.id = db_manager.execute_insert(
                """INSERT INTO plannings (mois, annee, taux_horaire, user_id, 
                   heures_contractuelles, created_at) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    self.mois,
                    self.annee,
                    self.taux_horaire,
                    self.user_id,
                    self.heures_contractuelles,
                    self.created_at,
                ),
            )

        # Sauvegarder les jours de travail
        for jour in self.jours_travail:
            jour_id = db_manager.execute_insert(
                "INSERT INTO jours_travail (planning_id, date) VALUES (?, ?)",
                (self.id, jour["date"]),
            )

            # Sauvegarder les créneaux
            for creneau in jour.get("creneaux", []):
                db_manager.execute_insert(
                    "INSERT INTO creneaux_travail (jour_travail_id, heure_debut, heure_fin) VALUES (?, ?, ?)",
                    (jour_id, creneau["heure_debut"], creneau["heure_fin"]),
                )

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

    @classmethod
    def get_all(cls) -> List["Planning"]:
        """Récupère tous les plannings"""
        rows = db_manager.execute_query(
            "SELECT * FROM plannings ORDER BY annee DESC, mois DESC"
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_user(cls, user_id: int) -> List["Planning"]:
        """Récupère tous les plannings d'un utilisateur"""
        rows = db_manager.execute_query(
            "SELECT * FROM plannings WHERE user_id = ? ORDER BY annee DESC, mois DESC",
            (user_id,),
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_id(cls, planning_id: int) -> Optional["Planning"]:
        """Récupère un planning par ID"""
        rows = db_manager.execute_query(
            "SELECT * FROM plannings WHERE id = ?", (planning_id,)
        )
        if rows:
            return cls.from_row(rows[0])
        return None

    @classmethod
    def from_row(cls, row) -> "Planning":
        """Crée un planning à partir d'une ligne de base de données"""
        # Récupérer les jours de travail
        jours_rows = db_manager.execute_query(
            "SELECT * FROM jours_travail WHERE planning_id = ?", (row["id"],)
        )

        jours_travail = []
        for jour_row in jours_rows:
            # Récupérer les créneaux pour ce jour
            creneaux_rows = db_manager.execute_query(
                "SELECT * FROM creneaux_travail WHERE jour_travail_id = ?",
                (jour_row["id"],),
            )

            creneaux = [
                {
                    "heure_debut": creneau["heure_debut"],
                    "heure_fin": creneau["heure_fin"],
                }
                for creneau in creneaux_rows
            ]

            jours_travail.append({"date": jour_row["date"], "creneaux": creneaux})

        return cls(
            id=row["id"],
            mois=row["mois"],
            annee=row["annee"],
            jours_travail=jours_travail,
            taux_horaire=row["taux_horaire"],
            user_id=row["user_id"],
            heures_contractuelles=row["heures_contractuelles"],
        )

    def to_feuille_heures(self) -> "FeuilleDHeures":
        """Convertit le planning en feuille d'heures"""

        jours_travailles = []
        for jour in self.jours_travail:
            jour_travaille = JourTravaille(date=jour["date"])
            for creneau in jour.get("creneaux", []):
                jour_travaille.ajouter_creneau(
                    creneau["heure_debut"], creneau["heure_fin"]
                )
            jours_travailles.append(jour_travaille)

        # Vérifier si une feuille d'heures existe déjà
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


class FeuilleDHeures:
    """Feuille d'heures avec stockage SQLite"""

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
        self.id = id
        self.mois = mois
        self.annee = annee
        self.jours_travailles = jours_travailles
        self.taux_horaire = taux_horaire
        self.user_id = user_id
        self.heures_contractuelles = heures_contractuelles
        self.created_at = datetime.now().isoformat()

    def calculer_total_heures(self) -> float:
        """Calcule le total des heures travaillées"""
        return sum(jour.calculer_heures() for jour in self.jours_travailles)

    def calculer_heures_supplementaires(self) -> Dict:
        """Calcule les heures supplémentaires (méthode legacy)"""
        from .salary_calculator import salary_calculator

        total_heures = self.calculer_total_heures()
        result = salary_calculator.calculate_salary(
            total_heures, self.heures_contractuelles, self.taux_horaire
        )

        return {
            "heures_normales": result["heures_normales"],
            "heures_supplementaires": result["total_heures_supplementaires"],
            "total_heures": total_heures,
        }

    def calculer_salaire(self) -> Dict:
        """Calcule le salaire brut estimé avec le système hebdomadaire correct"""
        from .salary_calculator import salary_calculator
        from datetime import datetime, timedelta
        
        # Calculer le salaire semaine par semaine
        semaines_heures = self._regrouper_par_semaine()
        
        # Initialiser les totaux
        result = {
            "contrat": f"{self.heures_contractuelles}h",
            "heures_contractuelles": self.heures_contractuelles,
            "total_heures": self.calculer_total_heures(),
            "taux_horaire": self.taux_horaire,
            "heures_normales": 0,
            "heures_complementaires": 0,
            "heures_complementaires_majorees": 0,
            "heures_supplementaires": [],
            "salaire_normal": 0,
            "salaire_complementaire": 0,
            "salaire_complementaire_majore": 0,
            "salaire_supplementaire": 0,
            "salaire_brut_total": 0,
            "detail_supplementaires": [],
            "nb_semaines_calculees": len(semaines_heures),
            "detail_semaines": []
        }
        
        # Calculer chaque semaine
        for semaine_num, heures_semaine in enumerate(semaines_heures, 1):
            if heures_semaine > 0:
                result_semaine = salary_calculator.calculate_salary(
                    heures_semaine, self.heures_contractuelles, self.taux_horaire
                )
                
                # Additionner aux totaux
                result["heures_normales"] += result_semaine["heures_normales"]
                result["heures_complementaires"] += result_semaine["heures_complementaires"]
                result["heures_complementaires_majorees"] += result_semaine["heures_complementaires_majorees"]
                result["salaire_normal"] += result_semaine["salaire_normal"]
                result["salaire_complementaire"] += result_semaine["salaire_complementaire"]
                result["salaire_complementaire_majore"] += result_semaine["salaire_complementaire_majore"]
                result["salaire_supplementaire"] += result_semaine["salaire_supplementaire"]
                result["salaire_brut_total"] += result_semaine["salaire_brut_total"]
                
                # Additionner les heures supplémentaires
                for sup in result_semaine["heures_supplementaires"]:
                    result["heures_supplementaires"].append(sup)
                
                # Garder le détail de la semaine
                result["detail_semaines"].append({
                    "semaine": semaine_num,
                    "heures": heures_semaine,
                    "salaire": result_semaine["salaire_brut_total"]
                })
        
        # Calculer le total des heures supplémentaires
        result["total_heures_supplementaires"] = sum(
            sup["heures"] for sup in result["heures_supplementaires"]
        )
        
        return result

    def calculer_salaire_mensuel_legacy(self) -> Dict:
        """Ancienne méthode de calcul mensuel (pour compatibilité)"""
        from .salary_calculator import salary_calculator

        total_heures = self.calculer_total_heures()
        return salary_calculator.calculate_salary(
            total_heures, self.heures_contractuelles, self.taux_horaire
        )

    def _regrouper_par_semaine(self) -> List[float]:
        """Regroupe les jours travaillés par semaine (lundi à dimanche)"""
        from datetime import datetime, timedelta
        
        if not self.jours_travailles:
            return []
        
        # Créer un dictionnaire des heures par date
        heures_par_date = {}
        for jour in self.jours_travailles:
            date_str = jour.date
            heures = jour.calculer_heures()
            heures_par_date[date_str] = heures
        
        # Trouver la première et dernière date
        dates = sorted(heures_par_date.keys())
        if not dates:
            return []
        
        premiere_date = datetime.strptime(dates[0], "%Y-%m-%d")
        derniere_date = datetime.strptime(dates[-1], "%Y-%m-%d")
        
        # Trouver le lundi de la première semaine
        jours_depuis_lundi = premiere_date.weekday()  # 0=lundi, 6=dimanche
        debut_semaine = premiere_date - timedelta(days=jours_depuis_lundi)
        
        # Calculer les heures par semaine
        semaines_heures = []
        date_courante = debut_semaine
        
        while date_courante <= derniere_date:
            heures_semaine = 0
            
            # Calculer les heures pour les 7 jours de la semaine
            for jour in range(7):
                date_jour = date_courante + timedelta(days=jour)
                date_str = date_jour.strftime("%Y-%m-%d")
                
                if date_str in heures_par_date:
                    heures_semaine += heures_par_date[date_str]
            
            if heures_semaine > 0:  # Ne garder que les semaines avec des heures
                semaines_heures.append(heures_semaine)
            
            # Passer à la semaine suivante
            date_courante += timedelta(days=7)
        
        return semaines_heures

    def save(self):
        """Sauvegarde la feuille d'heures en base de données"""
        if self.id:
            # Mise à jour
            db_manager.execute_update(
                """UPDATE feuilles_heures SET mois = ?, annee = ?, taux_horaire = ?, 
                   heures_contractuelles = ? WHERE id = ?""",
                (
                    self.mois,
                    self.annee,
                    self.taux_horaire,
                    self.heures_contractuelles,
                    self.id,
                ),
            )
            # Supprimer les anciens jours travaillés
            db_manager.execute_delete(
                "DELETE FROM jours_travailles WHERE feuille_heures_id = ?", (self.id,)
            )
        else:
            # Création
            self.id = db_manager.execute_insert(
                """INSERT INTO feuilles_heures (mois, annee, taux_horaire, user_id, 
                   heures_contractuelles, created_at) VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    self.mois,
                    self.annee,
                    self.taux_horaire,
                    self.user_id,
                    self.heures_contractuelles,
                    self.created_at,
                ),
            )

        # Sauvegarder les jours travaillés
        for jour in self.jours_travailles:
            jour_id = db_manager.execute_insert(
                "INSERT INTO jours_travailles (feuille_heures_id, date) VALUES (?, ?)",
                (self.id, jour.date),
            )

            # Sauvegarder les créneaux
            for creneau in jour.creneaux:
                db_manager.execute_insert(
                    "INSERT INTO creneaux_feuille (jour_travaille_id, heure_debut, heure_fin) VALUES (?, ?, ?)",
                    (jour_id, creneau.heure_debut, creneau.heure_fin),
                )

    def to_dict(self) -> Dict:
        calcul_salaire = self.calculer_salaire()
        
        # Calcul du salaire net
        salaire_net_info = net_salary_calculator.calculer_salaire_net(
            calcul_salaire['salaire_brut_total']
        )
        
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
            "calcul_salaire": calcul_salaire,
            "salaire_net": salaire_net_info,
        }

    @classmethod
    def get_all(cls) -> List["FeuilleDHeures"]:
        """Récupère toutes les feuilles d'heures"""
        rows = db_manager.execute_query(
            "SELECT * FROM feuilles_heures ORDER BY annee DESC, mois DESC"
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_user(cls, user_id: int) -> List["FeuilleDHeures"]:
        """Récupère toutes les feuilles d'heures d'un utilisateur"""
        rows = db_manager.execute_query(
            "SELECT * FROM feuilles_heures WHERE user_id = ? ORDER BY annee DESC, mois DESC",
            (user_id,),
        )
        return [cls.from_row(row) for row in rows]

    @classmethod
    def get_by_id(cls, feuille_id: int) -> Optional["FeuilleDHeures"]:
        """Récupère une feuille d'heures par ID"""
        rows = db_manager.execute_query(
            "SELECT * FROM feuilles_heures WHERE id = ?", (feuille_id,)
        )
        if rows:
            return cls.from_row(rows[0])
        return None

    @classmethod
    def get_by_mois_annee_user(
        cls, mois: int, annee: int, user_id: int
    ) -> Optional["FeuilleDHeures"]:
        """Trouve une feuille d'heures pour un mois/année/utilisateur donné"""
        rows = db_manager.execute_query(
            "SELECT * FROM feuilles_heures WHERE mois = ? AND annee = ? AND user_id = ?",
            (mois, annee, user_id),
        )
        if rows:
            return cls.from_row(rows[0])
        return None

    @classmethod
    def from_row(cls, row) -> "FeuilleDHeures":
        """Crée une feuille d'heures à partir d'une ligne de base de données"""
        # Récupérer les jours travaillés
        jours_rows = db_manager.execute_query(
            "SELECT * FROM jours_travailles WHERE feuille_heures_id = ?", (row["id"],)
        )

        jours_travailles = []
        for jour_row in jours_rows:
            jour = JourTravaille(date=jour_row["date"])

            # Récupérer les créneaux pour ce jour
            creneaux_rows = db_manager.execute_query(
                "SELECT * FROM creneaux_feuille WHERE jour_travaille_id = ?",
                (jour_row["id"],),
            )

            for creneau in creneaux_rows:
                jour.ajouter_creneau(creneau["heure_debut"], creneau["heure_fin"])

            jours_travailles.append(jour)

        return cls(
            id=row["id"],
            mois=row["mois"],
            annee=row["annee"],
            jours_travailles=jours_travailles,
            taux_horaire=row["taux_horaire"],
            user_id=row["user_id"],
            heures_contractuelles=row["heures_contractuelles"],
        )
