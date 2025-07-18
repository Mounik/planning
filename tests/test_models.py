"""
Tests pour les modèles de données
"""
import pytest
from datetime import datetime
from src.planning_pro.models import User, Planning, CreneauTravail, JourTravaille, FeuilleDHeures
from src.planning_pro.database import DatabaseManager


class TestUser:
    """Tests pour le modèle User"""
    
    def test_user_creation(self, db_manager):
        """Test de création d'un utilisateur"""
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        user = User.create(db_manager, **user_data)
        assert user is not None
        assert user.email == 'test@example.com'
        assert user.nom == 'Test'
        assert user.prenom == 'User'
        assert user.check_password('TestPassword123')
    
    def test_user_password_hashing(self, db_manager):
        """Test du hachage des mots de passe"""
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        user = User.create(db_manager, **user_data)
        
        # Le mot de passe ne doit pas être stocké en clair
        assert user.password_hash != 'TestPassword123'
        
        # Mais check_password doit fonctionner
        assert user.check_password('TestPassword123')
        assert not user.check_password('WrongPassword')
    
    def test_user_duplicate_email(self, db_manager):
        """Test de validation d'email unique"""
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        # Créer le premier utilisateur
        User.create(db_manager, **user_data)
        
        # Tenter de créer un deuxième utilisateur avec le même email
        with pytest.raises(Exception):
            User.create(db_manager, **user_data)
    
    def test_user_find_by_email(self, db_manager):
        """Test de recherche par email"""
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        created_user = User.create(db_manager, **user_data)
        found_user = User.find_by_email(db_manager, 'test@example.com')
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == created_user.email
    
    def test_user_find_by_id(self, db_manager):
        """Test de recherche par ID"""
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        created_user = User.create(db_manager, **user_data)
        found_user = User.find_by_id(db_manager, created_user.id)
        
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == created_user.email


class TestPlanning:
    """Tests pour le modèle Planning"""
    
    def test_planning_creation(self, db_manager):
        """Test de création d'un planning"""
        # Créer un utilisateur d'abord
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        user = User.create(db_manager, **user_data)
        
        # Créer un planning
        planning_data = {
            'user_id': user.id,
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
                }
            ]
        }
        
        planning = Planning.create(db_manager, **planning_data)
        assert planning is not None
        assert planning.user_id == user.id
        assert planning.mois == 1
        assert planning.annee == 2025
        assert planning.taux_horaire == 15.0
        assert planning.heures_contractuelles == 35
    
    def test_planning_find_by_user(self, db_manager):
        """Test de recherche de plannings par utilisateur"""
        # Créer un utilisateur
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        user = User.create(db_manager, **user_data)
        
        # Créer plusieurs plannings
        for mois in [1, 2, 3]:
            planning_data = {
                'user_id': user.id,
                'mois': mois,
                'annee': 2025,
                'taux_horaire': 15.0,
                'heures_contractuelles': 35,
                'jours_travail': []
            }
            Planning.create(db_manager, **planning_data)
        
        # Rechercher les plannings de l'utilisateur
        plannings = Planning.find_by_user(db_manager, user.id)
        assert len(plannings) == 3
        assert all(p.user_id == user.id for p in plannings)
    
    def test_planning_calculate_total_hours(self, db_manager):
        """Test du calcul des heures totales"""
        # Créer un utilisateur
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        user = User.create(db_manager, **user_data)
        
        # Créer un planning avec des heures spécifiques
        planning_data = {
            'user_id': user.id,
            'mois': 1,
            'annee': 2025,
            'taux_horaire': 15.0,
            'heures_contractuelles': 35,
            'jours_travail': [
                {
                    'date': '2025-01-15',
                    'creneaux': [
                        {'heure_debut': '09:00', 'heure_fin': '12:00'},  # 3h
                        {'heure_debut': '13:00', 'heure_fin': '17:00'}   # 4h
                    ]
                },
                {
                    'date': '2025-01-16',
                    'creneaux': [
                        {'heure_debut': '09:00', 'heure_fin': '17:00'}   # 8h
                    ]
                }
            ]
        }
        
        planning = Planning.create(db_manager, **planning_data)
        total_hours = planning.calculate_total_hours()
        
        # Total: 3h + 4h + 8h = 15h
        assert total_hours == 15.0


class TestCreneauTravail:
    """Tests pour le modèle CreneauTravail"""
    
    def test_creneau_duration_calculation(self):
        """Test du calcul de durée d'un créneau"""
        creneau = CreneauTravail(
            id=1,
            jour_travaille_id=1,
            heure_debut='09:00',
            heure_fin='12:00'
        )
        
        assert creneau.calculate_duration() == 3.0
        
        # Test avec minutes
        creneau.heure_debut = '09:30'
        creneau.heure_fin = '12:15'
        assert creneau.calculate_duration() == 2.75
    
    def test_creneau_invalid_times(self):
        """Test avec des heures invalides"""
        creneau = CreneauTravail(
            id=1,
            jour_travaille_id=1,
            heure_debut='12:00',
            heure_fin='09:00'  # Heure de fin avant début
        )
        
        # Devrait retourner 0 pour des heures invalides
        assert creneau.calculate_duration() == 0.0


class TestJourTravaille:
    """Tests pour le modèle JourTravaille"""
    
    def test_jour_calculate_total_hours(self):
        """Test du calcul des heures totales d'un jour"""
        jour = JourTravaille(
            id=1,
            planning_id=1,
            date='2025-01-15',
            creneaux=[
                CreneauTravail(1, 1, '09:00', '12:00'),  # 3h
                CreneauTravail(2, 1, '13:00', '17:00')   # 4h
            ]
        )
        
        assert jour.calculate_total_hours() == 7.0