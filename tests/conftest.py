"""
Configuration des tests pour Planning Pro
"""
import pytest
import os
import tempfile
from datetime import datetime
from src.planning_pro.app import create_app
from src.planning_pro.database import DatabaseManager
from src.planning_pro.models import User


@pytest.fixture
def app():
    """Fixture pour créer une instance de l'application de test"""
    # Créer un fichier de base de données temporaire
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Configuration de test
    config = {
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'DATABASE_PATH': db_path,
        'MAIL_SUPPRESS_SEND': True,
        'LOGIN_DISABLED': False
    }
    
    app = create_app(config)
    
    with app.app_context():
        # Initialiser la base de données de test
        db_manager = DatabaseManager(db_path)
        db_manager.init_db()
        
        yield app
    
    # Nettoyer après le test
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Fixture pour créer un client de test"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Fixture pour créer un runner CLI de test"""
    return app.test_cli_runner()


@pytest.fixture
def test_user():
    """Fixture pour créer un utilisateur de test"""
    return {
        'email': 'test@example.com',
        'password': 'TestPassword123',
        'nom': 'Test',
        'prenom': 'User'
    }


@pytest.fixture
def authenticated_user(client, test_user):
    """Fixture pour créer un utilisateur authentifié"""
    # Inscription
    client.post('/register', json=test_user)
    
    # Connexion
    response = client.post('/login', json={
        'email': test_user['email'],
        'password': test_user['password']
    })
    
    return test_user


@pytest.fixture
def sample_planning():
    """Fixture pour créer un planning de test"""
    return {
        'mois': 1,
        'annee': 2025,
        'taux_horaire': 15.0,
        'heures_contractuelles': 35,
        'jours_travail': [
            {
                'date': '2025-01-15',
                'creneaux': [
                    {'heure_debut': '09:00', 'heure_fin': '12:00'},
                    {'heure_debut': '13:00', 'heure_fin': '17:00'}
                ]
            },
            {
                'date': '2025-01-16',
                'creneaux': [
                    {'heure_debut': '09:00', 'heure_fin': '17:00'}
                ]
            }
        ]
    }


@pytest.fixture
def db_manager(app):
    """Fixture pour obtenir le gestionnaire de base de données"""
    with app.app_context():
        return DatabaseManager(app.config['DATABASE_PATH'])