"""
Tests pour le module de sécurité
"""
import pytest
from src.planning_pro.security import (
    SecurityValidator, 
    validate_json_data,
    USER_REGISTRATION_SCHEMA,
    USER_LOGIN_SCHEMA,
    PLANNING_SCHEMA
)


class TestSecurityValidator:
    """Tests pour la classe SecurityValidator"""
    
    def test_validate_email_success(self):
        """Test de validation d'email valide"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            assert SecurityValidator.validate_email(email) is True
    
    def test_validate_email_failure(self):
        """Test de validation d'email invalide"""
        invalid_emails = [
            'invalid-email',
            '@domain.com',
            'user@',
            'user..name@domain.com',
            'user@domain',
            '',
            None,
            'a' * 250 + '@domain.com'  # Trop long
        ]
        
        for email in invalid_emails:
            assert SecurityValidator.validate_email(email) is False
    
    def test_validate_password_success(self):
        """Test de validation de mot de passe valide"""
        valid_passwords = [
            'TestPassword123',
            'SecurePass1',
            'MyP@ssw0rd',
            'ComplexPassword123456'
        ]
        
        for password in valid_passwords:
            is_valid, message = SecurityValidator.validate_password(password)
            assert is_valid is True
            assert message == "Mot de passe valide"
    
    def test_validate_password_failure(self):
        """Test de validation de mot de passe invalide"""
        invalid_passwords = [
            ('', 'Le mot de passe est requis'),
            ('123', 'au moins 8 caractères'),
            ('password', 'au moins une majuscule'),
            ('PASSWORD', 'au moins une minuscule'),
            ('Password', 'au moins un chiffre'),
            ('a' * 129, 'ne peut pas dépasser 128 caractères')
        ]
        
        for password, expected_error in invalid_passwords:
            is_valid, message = SecurityValidator.validate_password(password)
            assert is_valid is False
            assert expected_error in message
    
    def test_validate_name_success(self):
        """Test de validation de nom valide"""
        valid_names = [
            'Jean',
            'Marie-Claire',
            'Jean-François',
            'José',
            'François',
            'O\'Brien'
        ]
        
        for name in valid_names:
            assert SecurityValidator.validate_name(name) is True
    
    def test_validate_name_failure(self):
        """Test de validation de nom invalide"""
        invalid_names = [
            '',
            'A',  # Trop court
            'Jean123',  # Chiffres
            'Jean@',  # Caractères spéciaux
            'A' * 51  # Trop long
        ]
        
        for name in invalid_names:
            assert SecurityValidator.validate_name(name) is False
    
    def test_validate_time_success(self):
        """Test de validation d'heure valide"""
        valid_times = [
            '09:00',
            '12:30',
            '00:00',
            '23:59',
            '01:15'
        ]
        
        for time in valid_times:
            assert SecurityValidator.validate_time(time) is True
    
    def test_validate_time_failure(self):
        """Test de validation d'heure invalide"""
        invalid_times = [
            '',
            '24:00',
            '12:60',
            '9:00',  # Pas de zéro initial
            '12:5',  # Pas de zéro pour les minutes
            'invalid',
            '12:00:00'  # Avec secondes
        ]
        
        for time in invalid_times:
            assert SecurityValidator.validate_time(time) is False
    
    def test_validate_date_success(self):
        """Test de validation de date valide"""
        valid_dates = [
            '2025-01-01',
            '2024-12-31',
            '2025-02-29',  # Année bissextile
            '2025-06-15'
        ]
        
        for date in valid_dates:
            assert SecurityValidator.validate_date(date) is True
    
    def test_validate_date_failure(self):
        """Test de validation de date invalide"""
        invalid_dates = [
            '',
            '2025-13-01',  # Mois invalide
            '2025-02-30',  # Jour invalide
            '25-01-01',    # Année sur 2 chiffres
            '2025/01/01',  # Mauvais format
            'invalid'
        ]
        
        for date in invalid_dates:
            assert SecurityValidator.validate_date(date) is False
    
    def test_validate_numeric_success(self):
        """Test de validation numérique valide"""
        assert SecurityValidator.validate_numeric(10) is True
        assert SecurityValidator.validate_numeric(10.5) is True
        assert SecurityValidator.validate_numeric('15') is True
        assert SecurityValidator.validate_numeric('15.5') is True
        
        # Avec limites
        assert SecurityValidator.validate_numeric(10, min_val=5, max_val=15) is True
        assert SecurityValidator.validate_numeric(5, min_val=5) is True
        assert SecurityValidator.validate_numeric(15, max_val=15) is True
    
    def test_validate_numeric_failure(self):
        """Test de validation numérique invalide"""
        assert SecurityValidator.validate_numeric('invalid') is False
        assert SecurityValidator.validate_numeric(None) is False
        
        # Avec limites
        assert SecurityValidator.validate_numeric(10, min_val=15) is False
        assert SecurityValidator.validate_numeric(10, max_val=5) is False
    
    def test_sanitize_string(self):
        """Test de sanitisation de chaînes"""
        assert SecurityValidator.sanitize_string('<script>alert("xss")</script>') == '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'
        assert SecurityValidator.sanitize_string('Normal text') == 'Normal text'
        assert SecurityValidator.sanitize_string('  Text with spaces  ') == 'Text with spaces'
        assert SecurityValidator.sanitize_string('') == ''
        assert SecurityValidator.sanitize_string(None) == ''
    
    def test_validate_planning_data_success(self):
        """Test de validation de données de planning valides"""
        valid_planning = {
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
        
        is_valid, message = SecurityValidator.validate_planning_data(valid_planning)
        assert is_valid is True
        assert message == "Données valides"
    
    def test_validate_planning_data_failure(self):
        """Test de validation de données de planning invalides"""
        invalid_plannings = [
            # Mois invalide
            {
                'mois': 13,
                'annee': 2025,
                'taux_horaire': 15.0,
                'heures_contractuelles': 35,
                'jours_travail': []
            },
            # Année invalide
            {
                'mois': 1,
                'annee': 2030,
                'taux_horaire': 15.0,
                'heures_contractuelles': 35,
                'jours_travail': []
            },
            # Taux horaire invalide
            {
                'mois': 1,
                'annee': 2025,
                'taux_horaire': -5,
                'heures_contractuelles': 35,
                'jours_travail': []
            },
            # Heures contractuelles invalides
            {
                'mois': 1,
                'annee': 2025,
                'taux_horaire': 15.0,
                'heures_contractuelles': 0,
                'jours_travail': []
            }
        ]
        
        for planning in invalid_plannings:
            is_valid, message = SecurityValidator.validate_planning_data(planning)
            assert is_valid is False
            assert len(message) > 0


class TestJSONValidation:
    """Tests pour la validation JSON"""
    
    def test_validate_user_registration_success(self):
        """Test de validation d'inscription utilisateur valide"""
        valid_user = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        is_valid, message = validate_json_data(valid_user, USER_REGISTRATION_SCHEMA)
        assert is_valid is True
        assert message == "Données valides"
    
    def test_validate_user_registration_failure(self):
        """Test de validation d'inscription utilisateur invalide"""
        # Champ manquant
        invalid_user = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test'
            # prenom manquant
        }
        
        is_valid, message = validate_json_data(invalid_user, USER_REGISTRATION_SCHEMA)
        assert is_valid is False
        assert 'prenom' in message
        assert 'requis' in message
    
    def test_validate_user_login_success(self):
        """Test de validation de connexion utilisateur valide"""
        valid_login = {
            'email': 'test@example.com',
            'password': 'TestPassword123'
        }
        
        is_valid, message = validate_json_data(valid_login, USER_LOGIN_SCHEMA)
        assert is_valid is True
        assert message == "Données valides"
    
    def test_validate_planning_schema_success(self):
        """Test de validation de schéma planning valide"""
        valid_planning = {
            'mois': 1,
            'annee': 2025,
            'taux_horaire': 15.0,
            'heures_contractuelles': 35,
            'jours_travail': []
        }
        
        is_valid, message = validate_json_data(valid_planning, PLANNING_SCHEMA)
        assert is_valid is True
        assert message == "Données valides"
    
    def test_validate_field_types(self):
        """Test de validation des types de champs"""
        # Type incorrect
        invalid_data = {
            'email': 123,  # Devrait être string
            'password': 'TestPassword123'
        }
        
        is_valid, message = validate_json_data(invalid_data, USER_LOGIN_SCHEMA)
        assert is_valid is False
        assert 'type' in message
        assert 'email' in message
    
    def test_validate_field_lengths(self):
        """Test de validation des longueurs de champs"""
        # Trop long
        invalid_data = {
            'email': 'a' * 260 + '@example.com',
            'password': 'TestPassword123'
        }
        
        is_valid, message = validate_json_data(invalid_data, USER_REGISTRATION_SCHEMA)
        assert is_valid is False
        assert 'dépasser' in message
        assert 'email' in message
        
        # Trop court
        invalid_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'A',  # Trop court
            'prenom': 'User'
        }
        
        is_valid, message = validate_json_data(invalid_data, USER_REGISTRATION_SCHEMA)
        assert is_valid is False
        assert 'au moins' in message
        assert 'nom' in message