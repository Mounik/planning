import sqlite3
import os
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime


class DatabaseManager:
    """Gestionnaire de base de données SQLite pour l'application"""

    def __init__(self, db_path: str = "data/planning.db"):
        self.db_path = db_path
        self.ensure_data_directory()
        self.init_database()

    def ensure_data_directory(self):
        """Assure que le répertoire data existe"""
        data_dir = os.path.dirname(self.db_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    @contextmanager
    def get_connection(self):
        """Context manager pour les connexions à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Table users
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    nom TEXT NOT NULL,
                    prenom TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    reset_token TEXT,
                    reset_token_expiry TEXT
                )
            """
            )

            # Table plannings
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS plannings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mois INTEGER NOT NULL,
                    annee INTEGER NOT NULL,
                    taux_horaire REAL NOT NULL,
                    user_id INTEGER NOT NULL,
                    heures_contractuelles REAL DEFAULT 35.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(mois, annee, user_id)
                )
            """
            )

            # Table jours_travail (pour les plannings)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jours_travail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    planning_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    FOREIGN KEY (planning_id) REFERENCES plannings (id) ON DELETE CASCADE
                )
            """
            )

            # Table creneaux_travail (pour les jours de travail)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS creneaux_travail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jour_travail_id INTEGER NOT NULL,
                    heure_debut TEXT NOT NULL,
                    heure_fin TEXT NOT NULL,
                    FOREIGN KEY (jour_travail_id) REFERENCES jours_travail (id) ON DELETE CASCADE
                )
            """
            )

            # Table feuilles_heures
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS feuilles_heures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mois INTEGER NOT NULL,
                    annee INTEGER NOT NULL,
                    taux_horaire REAL NOT NULL,
                    user_id INTEGER NOT NULL,
                    heures_contractuelles REAL DEFAULT 35.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    UNIQUE(mois, annee, user_id)
                )
            """
            )

            # Table jours_travailles (pour les feuilles d'heures)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jours_travailles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feuille_heures_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    FOREIGN KEY (feuille_heures_id) REFERENCES feuilles_heures (id) ON DELETE CASCADE
                )
            """
            )

            # Table creneaux_feuille (pour les jours travaillés des feuilles d'heures)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS creneaux_feuille (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jour_travaille_id INTEGER NOT NULL,
                    heure_debut TEXT NOT NULL,
                    heure_fin TEXT NOT NULL,
                    FOREIGN KEY (jour_travaille_id) REFERENCES jours_travailles (id) ON DELETE CASCADE
                )
            """
            )

            # Index pour améliorer les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_plannings_user_date ON plannings(user_id, mois, annee)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_feuilles_user_date ON feuilles_heures(user_id, mois, annee)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_jours_travail_planning ON jours_travail(planning_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_jours_travailles_feuille ON jours_travailles(feuille_heures_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_creneaux_travail_jour ON creneaux_travail(jour_travail_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_creneaux_feuille_jour ON creneaux_feuille(jour_travaille_id)"
            )

            conn.commit()

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Exécute une requête SELECT et retourne les résultats"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """Exécute une requête INSERT et retourne l'ID du nouvel enregistrement"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Exécute une requête UPDATE et retourne le nombre de lignes affectées"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def execute_delete(self, query: str, params: tuple = ()) -> int:
        """Exécute une requête DELETE et retourne le nombre de lignes supprimées"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()
