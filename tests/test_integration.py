"""
Tests d'intégration pour l'application Planning Pro
"""
import pytest
import json
from datetime import datetime
from src.planning_pro.models import User, Planning
from src.planning_pro.database import DatabaseManager


@pytest.mark.integration
class TestUserWorkflow:
    """Tests du workflow utilisateur complet"""
    
    def test_complete_user_workflow(self, client):
        """Test du workflow complet : inscription -> connexion -> création planning -> feuille heures"""
        # Données utilisateur
        user_data = {
            'email': 'integration@test.com',
            'password': 'TestPassword123',
            'nom': 'Integration',
            'prenom': 'Test'
        }
        
        # 1. Inscription
        response = client.post('/register', json=user_data)
        assert response.status_code == 201
        
        # 2. Connexion
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        response = client.post('/login', json=login_data)
        assert response.status_code == 200
        
        # 3. Création d'un planning
        planning_data = {
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
        
        response = client.post('/api/planning', json=planning_data)
        assert response.status_code == 201
        
        create_data = json.loads(response.data)
        planning_id = create_data['planning_id']
        
        # 4. Vérification du planning créé
        response = client.get(f'/api/planning/{planning_id}')
        assert response.status_code == 200
        
        planning = json.loads(response.data)
        assert planning['mois'] == 1
        assert planning['annee'] == 2025
        assert planning['taux_horaire'] == 15.0
        assert len(planning['jours_travail']) == 2
        
        # 5. Conversion en feuille d'heures
        response = client.post(f'/api/planning/{planning_id}/convert')
        assert response.status_code == 201
        
        convert_data = json.loads(response.data)
        feuille_id = convert_data['feuille_id']
        
        # 6. Vérification de la feuille d'heures
        response = client.get(f'/api/feuille-heures/{feuille_id}')
        assert response.status_code == 200
        
        feuille = json.loads(response.data)
        assert 'calcul_salaire' in feuille
        assert feuille['calcul_salaire']['salaire_brut'] > 0
        
        # 7. Déconnexion
        response = client.post('/logout')
        assert response.status_code == 200


@pytest.mark.integration
class TestPlanningWorkflow:
    """Tests du workflow de planning complet"""
    
    def test_planning_crud_operations(self, client, authenticated_user):
        """Test des opérations CRUD sur les plannings"""
        # Données de base
        base_planning = {
            'mois': 2,
            'annee': 2025,
            'taux_horaire': 16.0,
            'heures_contractuelles': 30,
            'jours_travail': [
                {
                    'date': '2025-02-10',
                    'creneaux': [
                        {'heure_debut': '10:00', 'heure_fin': '14:00'}
                    ]
                }
            ]
        }
        
        # CREATE - Créer un planning
        response = client.post('/api/planning', json=base_planning)
        assert response.status_code == 201
        
        create_data = json.loads(response.data)
        planning_id = create_data['planning_id']
        
        # READ - Lire le planning
        response = client.get(f'/api/planning/{planning_id}')
        assert response.status_code == 200
        
        planning = json.loads(response.data)
        assert planning['mois'] == 2
        assert planning['taux_horaire'] == 16.0
        
        # UPDATE - Modifier le planning
        updated_planning = base_planning.copy()
        updated_planning['taux_horaire'] = 18.0
        updated_planning['jours_travail'].append({
            'date': '2025-02-11',
            'creneaux': [
                {'heure_debut': '09:00', 'heure_fin': '13:00'}
            ]
        })
        
        response = client.put(f'/api/planning/{planning_id}', json=updated_planning)
        assert response.status_code == 200
        
        # Vérifier la modification
        response = client.get(f'/api/planning/{planning_id}')
        updated_data = json.loads(response.data)
        assert updated_data['taux_horaire'] == 18.0
        assert len(updated_data['jours_travail']) == 2
        
        # DELETE - Supprimer le planning
        response = client.delete(f'/api/planning/{planning_id}')
        assert response.status_code == 200
        
        # Vérifier la suppression
        response = client.get(f'/api/planning/{planning_id}')
        assert response.status_code == 404


@pytest.mark.integration
class TestSalaryCalculationWorkflow:
    """Tests du workflow de calcul de salaire"""
    
    def test_salary_calculation_different_contracts(self, client, authenticated_user):
        """Test du calcul de salaire pour différents types de contrats"""
        test_cases = [
            # (heures_contractuelles, heures_travaillees, expected_min_brut)
            (20, 25, 20 * 15.0),  # Temps partiel avec heures comp
            (25, 35, 25 * 15.0),  # Temps partiel avec heures comp et sup
            (35, 35, 35 * 15.0),  # Temps plein normal
            (35, 40, 35 * 15.0),  # Temps plein avec heures sup
            (39, 45, 39 * 15.0),  # 39h avec heures sup
        ]
        
        for heures_contractuelles, heures_travaillees, expected_min_brut in test_cases:
            # Créer un planning avec des heures spécifiques
            planning_data = {
                'mois': 3,
                'annee': 2025,
                'taux_horaire': 15.0,
                'heures_contractuelles': heures_contractuelles,
                'jours_travail': []
            }
            
            # Générer des jours de travail pour atteindre les heures souhaitées
            heures_par_jour = heures_travaillees // 5
            heures_restantes = heures_travaillees % 5
            
            for i in range(5):
                heures_jour = heures_par_jour + (1 if i < heures_restantes else 0)
                if heures_jour > 0:
                    planning_data['jours_travail'].append({
                        'date': f'2025-03-{i+10:02d}',
                        'creneaux': [
                            {'heure_debut': '09:00', 'heure_fin': f'{9+heures_jour:02d}:00'}
                        ]
                    })
            
            # Créer le planning
            response = client.post('/api/planning', json=planning_data)
            assert response.status_code == 201
            
            create_data = json.loads(response.data)
            planning_id = create_data['planning_id']
            
            # Convertir en feuille d'heures
            response = client.post(f'/api/planning/{planning_id}/convert')
            assert response.status_code == 201
            
            convert_data = json.loads(response.data)
            feuille_id = convert_data['feuille_id']
            
            # Vérifier le calcul
            response = client.get(f'/api/feuille-heures/{feuille_id}')
            assert response.status_code == 200
            
            feuille = json.loads(response.data)
            calcul = feuille['calcul_salaire']
            
            # Vérifications de base
            assert calcul['salaire_brut'] >= expected_min_brut
            assert calcul['salaire_net'] > 0
            assert calcul['salaire_net'] < calcul['salaire_brut']
            
            # Nettoyer
            client.delete(f'/api/planning/{planning_id}')
            client.delete(f'/api/feuille-heures/{feuille_id}')


@pytest.mark.integration
class TestErrorHandlingWorkflow:
    """Tests de gestion d'erreurs dans les workflows"""
    
    def test_planning_validation_errors(self, client, authenticated_user):
        """Test des erreurs de validation dans les plannings"""
        invalid_plannings = [
            # Mois invalide
            {
                'mois': 13,
                'annee': 2025,
                'taux_horaire': 15.0,
                'heures_contractuelles': 35,
                'jours_travail': []
            },
            # Taux horaire négatif
            {
                'mois': 1,
                'annee': 2025,
                'taux_horaire': -5.0,
                'heures_contractuelles': 35,
                'jours_travail': []
            },
            # Créneau avec heure de fin avant début
            {
                'mois': 1,
                'annee': 2025,
                'taux_horaire': 15.0,
                'heures_contractuelles': 35,
                'jours_travail': [
                    {
                        'date': '2025-01-15',
                        'creneaux': [
                            {'heure_debut': '17:00', 'heure_fin': '09:00'}
                        ]
                    }
                ]
            }
        ]
        
        for invalid_planning in invalid_plannings:
            response = client.post('/api/planning', json=invalid_planning)
            assert response.status_code == 400
            
            error_data = json.loads(response.data)
            assert error_data['success'] is False
            assert 'error' in error_data
    
    def test_authentication_required_workflow(self, client):
        """Test que l'authentification est requise"""
        # Tenter d'accéder aux endpoints sans authentification
        protected_endpoints = [
            ('GET', '/api/planning'),
            ('POST', '/api/planning'),
            ('GET', '/api/feuille-heures'),
            ('GET', '/api/planning/1'),
            ('PUT', '/api/planning/1'),
            ('DELETE', '/api/planning/1'),
        ]
        
        for method, endpoint in protected_endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                response = client.post(endpoint, json={})
            elif method == 'PUT':
                response = client.put(endpoint, json={})
            elif method == 'DELETE':
                response = client.delete(endpoint)
            
            assert response.status_code == 401


@pytest.mark.integration
class TestDataConsistency:
    """Tests de cohérence des données"""
    
    def test_planning_feuille_consistency(self, client, authenticated_user):
        """Test de cohérence entre planning et feuille d'heures"""
        # Créer un planning avec des données précises
        planning_data = {
            'mois': 4,
            'annee': 2025,
            'taux_horaire': 20.0,
            'heures_contractuelles': 35,
            'jours_travail': [
                {
                    'date': '2025-04-01',
                    'creneaux': [
                        {'heure_debut': '09:00', 'heure_fin': '12:00'},  # 3h
                        {'heure_debut': '13:00', 'heure_fin': '17:00'}   # 4h
                    ]
                },
                {
                    'date': '2025-04-02',
                    'creneaux': [
                        {'heure_debut': '10:00', 'heure_fin': '18:00'}   # 8h
                    ]
                }
            ]
        }
        
        # Créer le planning
        response = client.post('/api/planning', json=planning_data)
        assert response.status_code == 201
        
        create_data = json.loads(response.data)
        planning_id = create_data['planning_id']
        
        # Récupérer le planning
        response = client.get(f'/api/planning/{planning_id}')
        planning = json.loads(response.data)
        
        # Convertir en feuille d'heures
        response = client.post(f'/api/planning/{planning_id}/convert')
        assert response.status_code == 201
        
        convert_data = json.loads(response.data)
        feuille_id = convert_data['feuille_id']
        
        # Récupérer la feuille d'heures
        response = client.get(f'/api/feuille-heures/{feuille_id}')
        feuille = json.loads(response.data)
        
        # Vérifier la cohérence
        assert feuille['mois'] == planning['mois']
        assert feuille['annee'] == planning['annee']
        assert feuille['taux_horaire'] == planning['taux_horaire']
        assert feuille['heures_contractuelles'] == planning['heures_contractuelles']
        assert len(feuille['jours_travailles']) == len(planning['jours_travail'])
        
        # Vérifier les heures totales
        total_heures_planning = sum(
            sum(
                (datetime.strptime(creneau['heure_fin'], '%H:%M') - 
                 datetime.strptime(creneau['heure_debut'], '%H:%M')).total_seconds() / 3600
                for creneau in jour['creneaux']
            )
            for jour in planning['jours_travail']
        )
        
        total_heures_feuille = sum(
            sum(
                (datetime.strptime(creneau['heure_fin'], '%H:%M') - 
                 datetime.strptime(creneau['heure_debut'], '%H:%M')).total_seconds() / 3600
                for creneau in jour['creneaux']
            )
            for jour in feuille['jours_travailles']
        )
        
        assert abs(total_heures_planning - total_heures_feuille) < 0.01