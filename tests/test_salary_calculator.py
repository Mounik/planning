"""
Tests pour les calculateurs de salaire
"""
import pytest
from src.planning_pro.salary_calculator import SalaryCalculator
from src.planning_pro.net_salary_calculator import NetSalaryCalculator


class TestSalaryCalculator:
    """Tests pour le calculateur de salaire brut"""
    
    def test_init(self):
        """Test d'initialisation du calculateur"""
        calc = SalaryCalculator(
            heures_travaillees=40,
            heures_contractuelles=35,
            taux_horaire=15.0
        )
        
        assert calc.heures_travaillees == 40
        assert calc.heures_contractuelles == 35
        assert calc.taux_horaire == 15.0
    
    def test_calculate_temps_plein_normal(self):
        """Test calcul temps plein sans heures supplémentaires"""
        calc = SalaryCalculator(
            heures_travaillees=35,
            heures_contractuelles=35,
            taux_horaire=15.0
        )
        
        result = calc.calculate()
        
        assert result['heures_normales'] == 35
        assert result['heures_complementaires_normales'] == 0
        assert result['heures_complementaires_majorees'] == 0
        assert result['heures_supplementaires_25'] == 0
        assert result['heures_supplementaires_50'] == 0
        assert result['salaire_brut'] == 35 * 15.0
    
    def test_calculate_temps_plein_avec_heures_sup(self):
        """Test calcul temps plein avec heures supplémentaires"""
        calc = SalaryCalculator(
            heures_travaillees=43,
            heures_contractuelles=35,
            taux_horaire=15.0
        )
        
        result = calc.calculate()
        
        assert result['heures_normales'] == 35
        assert result['heures_supplementaires_25'] == 4  # 36-39h
        assert result['heures_supplementaires_50'] == 4  # 40-43h
        
        # Calcul attendu:
        # 35h normales: 35 * 15 = 525€
        # 4h sup 25%: 4 * 15 * 1.25 = 75€
        # 4h sup 50%: 4 * 15 * 1.50 = 90€
        # Total: 525 + 75 + 90 = 690€
        expected_brut = 35 * 15.0 + 4 * 15.0 * 1.25 + 4 * 15.0 * 1.50
        assert result['salaire_brut'] == expected_brut
    
    def test_calculate_temps_partiel_20h_normal(self):
        """Test calcul temps partiel 20h sans heures complémentaires"""
        calc = SalaryCalculator(
            heures_travaillees=20,
            heures_contractuelles=20,
            taux_horaire=15.0
        )
        
        result = calc.calculate()
        
        assert result['heures_normales'] == 20
        assert result['heures_complementaires_normales'] == 0
        assert result['heures_complementaires_majorees'] == 0
        assert result['heures_supplementaires_25'] == 0
        assert result['heures_supplementaires_50'] == 0
        assert result['salaire_brut'] == 20 * 15.0
    
    def test_calculate_temps_partiel_20h_avec_comp(self):
        """Test calcul temps partiel 20h avec heures complémentaires"""
        calc = SalaryCalculator(
            heures_travaillees=32,
            heures_contractuelles=20,
            taux_horaire=15.0
        )
        
        result = calc.calculate()
        
        assert result['heures_normales'] == 20
        assert result['heures_complementaires_normales'] == 2  # 20h + 10% = 22h
        assert result['heures_complementaires_majorees'] == 10  # 22h -> 32h
        assert result['heures_supplementaires_25'] == 0
        assert result['heures_supplementaires_50'] == 0
        
        # Calcul attendu:
        # 20h normales: 20 * 15 = 300€
        # 2h comp normales: 2 * 15 * 1.10 = 33€
        # 10h comp majorées: 10 * 15 * 1.25 = 187.5€
        # Total: 300 + 33 + 187.5 = 520.5€
        expected_brut = 20 * 15.0 + 2 * 15.0 * 1.10 + 10 * 15.0 * 1.25
        assert result['salaire_brut'] == expected_brut
    
    def test_calculate_temps_partiel_25h_avec_sup(self):
        """Test calcul temps partiel 25h avec heures supplémentaires"""
        calc = SalaryCalculator(
            heures_travaillees=40,
            heures_contractuelles=25,
            taux_horaire=15.0
        )
        
        result = calc.calculate()
        
        assert result['heures_normales'] == 25
        assert result['heures_complementaires_normales'] == 2.5  # 25h + 10% = 27.5h
        assert result['heures_complementaires_majorees'] == 7.5  # 27.5h -> 35h
        assert result['heures_supplementaires_25'] == 4  # 36-39h
        assert result['heures_supplementaires_50'] == 1  # 40h
        
        # Calcul attendu:
        # 25h normales: 25 * 15 = 375€
        # 2.5h comp normales: 2.5 * 15 * 1.10 = 41.25€
        # 7.5h comp majorées: 7.5 * 15 * 1.25 = 140.625€
        # 4h sup 25%: 4 * 15 * 1.25 = 75€
        # 1h sup 50%: 1 * 15 * 1.50 = 22.5€
        # Total: 375 + 41.25 + 140.625 + 75 + 22.5 = 654.375€
        expected_brut = (25 * 15.0 + 2.5 * 15.0 * 1.10 + 7.5 * 15.0 * 1.25 + 
                        4 * 15.0 * 1.25 + 1 * 15.0 * 1.50)
        assert result['salaire_brut'] == expected_brut
    
    def test_calculate_temps_partiel_30h_seuils(self):
        """Test calcul temps partiel 30h aux seuils"""
        calc = SalaryCalculator(
            heures_travaillees=35,
            heures_contractuelles=30,
            taux_horaire=15.0
        )
        
        result = calc.calculate()
        
        assert result['heures_normales'] == 30
        assert result['heures_complementaires_normales'] == 3  # 30h + 10% = 33h
        assert result['heures_complementaires_majorees'] == 2  # 33h -> 35h
        assert result['heures_supplementaires_25'] == 0
        assert result['heures_supplementaires_50'] == 0
    
    def test_calculate_39h_avec_sup(self):
        """Test calcul 39h avec heures supplémentaires"""
        calc = SalaryCalculator(
            heures_travaillees=45,
            heures_contractuelles=39,
            taux_horaire=15.0
        )
        
        result = calc.calculate()
        
        assert result['heures_normales'] == 39
        assert result['heures_complementaires_normales'] == 0
        assert result['heures_complementaires_majorees'] == 0
        assert result['heures_supplementaires_25'] == 4  # 40-43h
        assert result['heures_supplementaires_50'] == 2  # 44-45h
        
        # Calcul attendu:
        # 39h normales: 39 * 15 = 585€
        # 4h sup 25%: 4 * 15 * 1.25 = 75€
        # 2h sup 50%: 2 * 15 * 1.50 = 45€
        # Total: 585 + 75 + 45 = 705€
        expected_brut = 39 * 15.0 + 4 * 15.0 * 1.25 + 2 * 15.0 * 1.50
        assert result['salaire_brut'] == expected_brut
    
    def test_get_contract_type(self):
        """Test détection du type de contrat"""
        tests = [
            (20, "20h/semaine"),
            (25, "25h/semaine"),
            (30, "30h/semaine"),
            (35, "35h/semaine (temps plein)"),
            (39, "39h/semaine"),
            (40, "Autre (40h/semaine)")
        ]
        
        for heures, expected_type in tests:
            calc = SalaryCalculator(
                heures_travaillees=heures,
                heures_contractuelles=heures,
                taux_horaire=15.0
            )
            assert calc.get_contract_type() == expected_type
    
    def test_edge_cases(self):
        """Test des cas limites"""
        # Heures travaillées = 0
        calc = SalaryCalculator(
            heures_travaillees=0,
            heures_contractuelles=35,
            taux_horaire=15.0
        )
        result = calc.calculate()
        assert result['salaire_brut'] == 0
        
        # Heures travaillées < heures contractuelles
        calc = SalaryCalculator(
            heures_travaillees=30,
            heures_contractuelles=35,
            taux_horaire=15.0
        )
        result = calc.calculate()
        assert result['heures_normales'] == 30
        assert result['salaire_brut'] == 30 * 15.0


class TestNetSalaryCalculator:
    """Tests pour le calculateur de salaire net"""
    
    def test_init(self):
        """Test d'initialisation du calculateur net"""
        calc = NetSalaryCalculator(1000.0)
        assert calc.salaire_brut == 1000.0
    
    def test_calculate_basic(self):
        """Test calcul salaire net basique"""
        calc = NetSalaryCalculator(1000.0)
        result = calc.calculate()
        
        assert 'salaire_net' in result
        assert 'cotisations_salariales' in result
        assert 'taux_cotisations' in result
        
        # Le salaire net doit être inférieur au brut
        assert result['salaire_net'] < 1000.0
        assert result['salaire_net'] > 0
        
        # Les cotisations doivent être positives
        assert result['cotisations_salariales'] > 0
        
        # Le taux de cotisations doit être raisonnable (environ 22-25%)
        assert 0.20 <= result['taux_cotisations'] <= 0.30
    
    def test_calculate_zero_brut(self):
        """Test calcul avec salaire brut zéro"""
        calc = NetSalaryCalculator(0.0)
        result = calc.calculate()
        
        assert result['salaire_net'] == 0.0
        assert result['cotisations_salariales'] == 0.0
        assert result['taux_cotisations'] == 0.0
    
    def test_calculate_high_salary(self):
        """Test calcul avec salaire élevé"""
        calc = NetSalaryCalculator(10000.0)
        result = calc.calculate()
        
        # Le salaire net doit être cohérent
        assert result['salaire_net'] > 0
        assert result['salaire_net'] < 10000.0
        
        # Les cotisations doivent être proportionnelles
        assert result['cotisations_salariales'] > 0
        assert result['taux_cotisations'] > 0
    
    def test_calculate_consistency(self):
        """Test cohérence des calculs"""
        calc = NetSalaryCalculator(1500.0)
        result = calc.calculate()
        
        # Vérifier que brut = net + cotisations
        expected_brut = result['salaire_net'] + result['cotisations_salariales']
        assert abs(expected_brut - 1500.0) < 0.01  # Tolérance pour les arrondis
        
        # Vérifier que le taux est cohérent
        expected_taux = result['cotisations_salariales'] / 1500.0
        assert abs(expected_taux - result['taux_cotisations']) < 0.001
    
    def test_different_salaries(self):
        """Test avec différents niveaux de salaires"""
        salaires = [500, 1000, 1500, 2000, 3000, 5000]
        
        for salaire_brut in salaires:
            calc = NetSalaryCalculator(salaire_brut)
            result = calc.calculate()
            
            # Vérifications de base
            assert result['salaire_net'] > 0
            assert result['salaire_net'] < salaire_brut
            assert result['cotisations_salariales'] > 0
            assert 0.20 <= result['taux_cotisations'] <= 0.30
    
    def test_progressive_taxation(self):
        """Test que le taux augmente avec le salaire (progressivité)"""
        calc_low = NetSalaryCalculator(1000.0)
        result_low = calc_low.calculate()
        
        calc_high = NetSalaryCalculator(5000.0)
        result_high = calc_high.calculate()
        
        # Le taux devrait être plus élevé pour les salaires élevés
        # (ou au moins égal en cas de taux fixe)
        assert result_high['taux_cotisations'] >= result_low['taux_cotisations']


class TestSalaryCalculatorIntegration:
    """Tests d'intégration entre les calculateurs"""
    
    def test_complete_salary_calculation(self):
        """Test calcul complet brut -> net"""
        # Calculer le salaire brut
        brut_calc = SalaryCalculator(
            heures_travaillees=40,
            heures_contractuelles=35,
            taux_horaire=15.0
        )
        brut_result = brut_calc.calculate()
        
        # Calculer le salaire net
        net_calc = NetSalaryCalculator(brut_result['salaire_brut'])
        net_result = net_calc.calculate()
        
        # Vérifications
        assert brut_result['salaire_brut'] > 0
        assert net_result['salaire_net'] > 0
        assert net_result['salaire_net'] < brut_result['salaire_brut']
        assert net_result['cotisations_salariales'] > 0
    
    def test_different_contract_types_integration(self):
        """Test intégration avec différents types de contrats"""
        contracts = [
            (20, 25),  # Temps partiel avec heures comp
            (25, 35),  # Temps partiel avec heures sup
            (35, 35),  # Temps plein normal
            (35, 40),  # Temps plein avec heures sup
            (39, 45)   # 39h avec heures sup
        ]
        
        for heures_contractuelles, heures_travaillees in contracts:
            # Calcul brut
            brut_calc = SalaryCalculator(
                heures_travaillees=heures_travaillees,
                heures_contractuelles=heures_contractuelles,
                taux_horaire=15.0
            )
            brut_result = brut_calc.calculate()
            
            # Calcul net
            net_calc = NetSalaryCalculator(brut_result['salaire_brut'])
            net_result = net_calc.calculate()
            
            # Vérifications de base
            assert brut_result['salaire_brut'] > 0
            assert net_result['salaire_net'] > 0
            assert net_result['salaire_net'] < brut_result['salaire_brut']