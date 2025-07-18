"""
Tests pour les endpoints API
"""
import pytest
import json
from src.planning_pro.models import User, Planning


class TestAuthAPI:
    """Tests pour les endpoints d'authentification"""
    
    def test_register_success(self, client):
        """Test d'inscription réussie"""
        user_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        response = client.post('/register', json=user_data)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user_id' in data
    
    def test_register_duplicate_email(self, client, test_user):
        """Test d'inscription avec email déjà existant"""
        # Première inscription
        client.post('/register', json=test_user)
        
        # Deuxième inscription avec le même email
        response = client.post('/register', json=test_user)
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'déjà utilisé' in data['error']
    
    def test_register_invalid_email(self, client):
        """Test d'inscription avec email invalide"""
        user_data = {
            'email': 'invalid-email',
            'password': 'TestPassword123',
            'nom': 'Test',
            'prenom': 'User'
        }
        
        response = client.post('/register', json=user_data)
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'email' in data['error'].lower()
    
    def test_register_weak_password(self, client):
        """Test d'inscription avec mot de passe faible"""
        user_data = {
            'email': 'test@example.com',
            'password': '123',  # Mot de passe trop faible
            'nom': 'Test',
            'prenom': 'User'
        }
        
        response = client.post('/register', json=user_data)
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'mot de passe' in data['error'].lower()
    
    def test_login_success(self, client, test_user):
        """Test de connexion réussie"""
        # Inscription
        client.post('/register', json=test_user)
        
        # Connexion
        login_data = {
            'email': test_user['email'],
            'password': test_user['password']
        }
        
        response = client.post('/login', json=login_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user_id' in data
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test de connexion avec identifiants invalides"""
        # Inscription
        client.post('/register', json=test_user)
        
        # Tentative de connexion avec mauvais mot de passe
        login_data = {
            'email': test_user['email'],
            'password': 'WrongPassword'
        }
        
        response = client.post('/login', json=login_data)
        assert response.status_code == 401
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'identifiants' in data['error'].lower()
    
    def test_logout(self, client, authenticated_user):
        """Test de déconnexion"""
        response = client.post('/logout')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True


class TestPlanningAPI:
    """Tests pour les endpoints de planning"""
    
    def test_create_planning_success(self, client, authenticated_user, sample_planning):
        """Test de création de planning réussie"""
        response = client.post('/api/planning', json=sample_planning)
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'planning_id' in data
    
    def test_create_planning_unauthorized(self, client, sample_planning):
        """Test de création de planning sans authentification"""
        response = client.post('/api/planning', json=sample_planning)
        assert response.status_code == 401
    
    def test_create_planning_invalid_data(self, client, authenticated_user):
        """Test de création de planning avec données invalides"""
        invalid_planning = {
            'mois': 13,  # Mois invalide
            'annee': 2025,
            'taux_horaire': -5,  # Taux négatif
            'heures_contractuelles': 0,
            'jours_travail': []
        }
        
        response = client.post('/api/planning', json=invalid_planning)
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_get_plannings(self, client, authenticated_user, sample_planning):
        """Test de récupération des plannings"""
        # Créer un planning
        client.post('/api/planning', json=sample_planning)
        
        # Récupérer les plannings
        response = client.get('/api/planning')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['mois'] == sample_planning['mois']
    
    def test_get_planning_by_id(self, client, authenticated_user, sample_planning):
        """Test de récupération d'un planning par ID"""
        # Créer un planning
        create_response = client.post('/api/planning', json=sample_planning)
        create_data = json.loads(create_response.data)
        planning_id = create_data['planning_id']
        
        # Récupérer le planning
        response = client.get(f'/api/planning/{planning_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['id'] == planning_id
        assert data['mois'] == sample_planning['mois']
    
    def test_get_planning_not_found(self, client, authenticated_user):
        """Test de récupération d'un planning inexistant"""
        response = client.get('/api/planning/999')
        assert response.status_code == 404
    
    def test_update_planning(self, client, authenticated_user, sample_planning):
        """Test de mise à jour d'un planning"""
        # Créer un planning
        create_response = client.post('/api/planning', json=sample_planning)
        create_data = json.loads(create_response.data)
        planning_id = create_data['planning_id']
        
        # Mettre à jour le planning
        updated_data = sample_planning.copy()
        updated_data['taux_horaire'] = 20.0
        
        response = client.put(f'/api/planning/{planning_id}', json=updated_data)
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_delete_planning(self, client, authenticated_user, sample_planning):
        """Test de suppression d'un planning"""
        # Créer un planning
        create_response = client.post('/api/planning', json=sample_planning)
        create_data = json.loads(create_response.data)
        planning_id = create_data['planning_id']
        
        # Supprimer le planning
        response = client.delete(f'/api/planning/{planning_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Vérifier que le planning n'existe plus
        get_response = client.get(f'/api/planning/{planning_id}')
        assert get_response.status_code == 404
    
    def test_convert_planning_to_feuille(self, client, authenticated_user, sample_planning):
        """Test de conversion d'un planning en feuille d'heures"""
        # Créer un planning
        create_response = client.post('/api/planning', json=sample_planning)
        create_data = json.loads(create_response.data)
        planning_id = create_data['planning_id']
        
        # Convertir en feuille d'heures
        response = client.post(f'/api/planning/{planning_id}/convert')
        assert response.status_code == 201
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'feuille_id' in data


class TestFeuilleHeuresAPI:
    """Tests pour les endpoints de feuille d'heures"""
    
    def test_get_feuilles_heures(self, client, authenticated_user, sample_planning):
        """Test de récupération des feuilles d'heures"""
        # Créer un planning et le convertir
        create_response = client.post('/api/planning', json=sample_planning)
        create_data = json.loads(create_response.data)
        planning_id = create_data['planning_id']
        
        client.post(f'/api/planning/{planning_id}/convert')
        
        # Récupérer les feuilles d'heures
        response = client.get('/api/feuille-heures')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1
    
    def test_get_feuille_heures_by_id(self, client, authenticated_user, sample_planning):
        """Test de récupération d'une feuille d'heures par ID"""
        # Créer un planning et le convertir
        create_response = client.post('/api/planning', json=sample_planning)
        create_data = json.loads(create_response.data)
        planning_id = create_data['planning_id']
        
        convert_response = client.post(f'/api/planning/{planning_id}/convert')
        convert_data = json.loads(convert_response.data)
        feuille_id = convert_data['feuille_id']
        
        # Récupérer la feuille d'heures
        response = client.get(f'/api/feuille-heures/{feuille_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['id'] == feuille_id
        assert 'calcul_salaire' in data
    
    def test_delete_feuille_heures(self, client, authenticated_user, sample_planning):
        """Test de suppression d'une feuille d'heures"""
        # Créer un planning et le convertir
        create_response = client.post('/api/planning', json=sample_planning)
        create_data = json.loads(create_response.data)
        planning_id = create_data['planning_id']
        
        convert_response = client.post(f'/api/planning/{planning_id}/convert')
        convert_data = json.loads(convert_response.data)
        feuille_id = convert_data['feuille_id']
        
        # Supprimer la feuille d'heures
        response = client.delete(f'/api/feuille-heures/{feuille_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Vérifier que la feuille n'existe plus
        get_response = client.get(f'/api/feuille-heures/{feuille_id}')
        assert get_response.status_code == 404


class TestContractsAPI:
    """Tests pour les endpoints de contrats"""
    
    def test_get_contracts(self, client, authenticated_user):
        """Test de récupération des types de contrats"""
        response = client.get('/api/contracts')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Vérifier qu'on a au moins le contrat 35h
        contract_35h = next((c for c in data if c['heures'] == 35), None)
        assert contract_35h is not None
        assert contract_35h['nom'] == 'Temps plein (35h)'


class TestErrorHandling:
    """Tests pour la gestion d'erreurs"""
    
    def test_404_not_found(self, client):
        """Test d'endpoint inexistant"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test de méthode non autorisée"""
        response = client.patch('/api/contracts')
        assert response.status_code == 405
    
    def test_invalid_json(self, client, authenticated_user):
        """Test avec JSON invalide"""
        response = client.post('/api/planning', 
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400