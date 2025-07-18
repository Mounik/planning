"""
Calculateur de salaire avec gestion des heures supplémentaires et complémentaires
selon le type de contrat de travail
"""

from typing import Dict, List, Optional, Any
import json

# Configuration des seuils de majoration par type de contrat
SALARY_CONFIG = [
    {
        "contrat": "20h",
        "heures_contractuelles": 20,
        "heures_complementaires": [
            {"de": 20, "a": 22, "type": "complémentaires", "majoration": 10},
            {
                "de": 22,
                "a": 35,
                "type": "complémentaires majorées",
                "majoration": 25,
            },
        ],
        "heures_supplementaires": [
            {"de": 35, "a": 39, "majoration": 10},
            {"de": 39, "a": 43, "majoration": 20},
            {"de": 43, "a": None, "majoration": 50},
        ],
    },
    {
        "contrat": "25h",
        "heures_contractuelles": 25,
        "heures_complementaires": [
            {"de": 25, "a": 27.5, "type": "complémentaires", "majoration": 10},
            {
                "de": 27.5,
                "a": 35,
                "type": "complémentaires majorées",
                "majoration": 25,
            },
        ],
        "heures_supplementaires": [
            {"de": 35, "a": 39, "majoration": 10},
            {"de": 39, "a": 43, "majoration": 20},
            {"de": 43, "a": None, "majoration": 50},
        ],
    },
    {
        "contrat": "30h",
        "heures_contractuelles": 30,
        "heures_complementaires": [
            {"de": 30, "a": 33, "type": "complémentaires", "majoration": 10},
            {"de": 33, "a": 35, "type": "complémentaires majorées", "majoration": 25},
        ],
        "heures_supplementaires": [
            {"de": 35, "a": 39, "majoration": 10},
            {"de": 39, "a": 43, "majoration": 20},
            {"de": 43, "a": None, "majoration": 50},
        ],
    },
    {
        "contrat": "35h",
        "heures_contractuelles": 35,
        "heures_complementaires": [],
        "heures_supplementaires": [
            {"de": 35, "a": 39, "majoration": 10},
            {"de": 39, "a": 43, "majoration": 20},
            {"de": 43, "a": None, "majoration": 50},
        ],
    },
    {
        "contrat": "39h",
        "heures_contractuelles": 39,
        "heures_complementaires": [],
        "heures_supplementaires": [
            {"de": 39, "a": 43, "majoration": 20},
            {"de": 43, "a": None, "majoration": 50},
        ],
    },
]


class SalaryCalculator:
    """Calculateur de salaire avec gestion des heures supplémentaires et complémentaires"""

    def __init__(self):
        self.config = SALARY_CONFIG

    def get_contract_config(self, heures_contractuelles: float) -> Optional[Dict]:
        """Récupère la configuration pour un nombre d'heures contractuelles donné"""
        for config in self.config:
            if config["heures_contractuelles"] == heures_contractuelles:
                return config
        return None

    def calculate_salary(
        self, total_heures: float, heures_contractuelles: float, taux_horaire: float
    ) -> Dict[str, Any]:
        """
        Calcule le salaire en fonction du total d'heures travaillées et du type de contrat

        Args:
            total_heures: Nombre total d'heures travaillées
            heures_contractuelles: Nombre d'heures contractuelles
            taux_horaire: Taux horaire de base

        Returns:
            Dict contenant le détail du calcul de salaire
        """
        config = self.get_contract_config(heures_contractuelles)
        if not config:
            # Configuration par défaut si le contrat n'est pas trouvé
            return self._calculate_default_salary(
                total_heures, heures_contractuelles, taux_horaire
            )

        # Initialiser les résultats
        result = {
            "contrat": config["contrat"],
            "heures_contractuelles": heures_contractuelles,
            "total_heures": total_heures,
            "taux_horaire": taux_horaire,
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
        }

        heures_restantes = total_heures

        # 1. Heures normales (contractuelles)
        heures_normales = min(heures_restantes, heures_contractuelles)
        result["heures_normales"] = heures_normales
        result["salaire_normal"] = heures_normales * taux_horaire
        heures_restantes -= heures_normales

        if heures_restantes <= 0:
            result["salaire_brut_total"] = result["salaire_normal"]
            return result

        # 2. Heures complémentaires (pour les contrats < 35h)
        if config["heures_complementaires"]:
            for comp in config["heures_complementaires"]:
                if heures_restantes <= 0:
                    break

                debut = comp["de"]
                fin = comp["a"]
                majoration = comp["majoration"]

                # Calculer les heures dans cette tranche
                heures_tranche_debut = max(0, debut - heures_contractuelles)
                heures_tranche_fin = (
                    fin - heures_contractuelles if fin else float("inf")
                )

                if total_heures > debut:
                    heures_dans_tranche = min(
                        heures_restantes,
                        min(total_heures, fin if fin else total_heures)
                        - max(
                            debut,
                            heures_contractuelles
                            + result["heures_normales"]
                            - heures_contractuelles,
                        ),
                    )

                    if heures_dans_tranche > 0:
                        taux_majore = taux_horaire * (1 + majoration / 100)

                        if comp["type"] == "complémentaires":
                            result["heures_complementaires"] += heures_dans_tranche
                            result["salaire_complementaire"] += (
                                heures_dans_tranche * taux_majore
                            )
                        else:  # complémentaires majorées
                            result[
                                "heures_complementaires_majorees"
                            ] += heures_dans_tranche
                            result["salaire_complementaire_majore"] += (
                                heures_dans_tranche * taux_majore
                            )

                        heures_restantes -= heures_dans_tranche

        # 3. Heures supplémentaires (au-delà des heures contractuelles pour >= 35h, ou au-delà de 35h pour < 35h)
        seuil_heures_sup = max(35, heures_contractuelles)
        if heures_restantes > 0 and total_heures > seuil_heures_sup:
            heures_sup_base = max(0, total_heures - seuil_heures_sup)
            heures_sup_restantes = heures_sup_base

            for sup in config["heures_supplementaires"]:
                if heures_sup_restantes <= 0:
                    break

                debut = sup["de"]
                fin = sup["a"]
                majoration = sup["majoration"]

                if total_heures > debut:
                    heures_dans_tranche = min(
                        heures_sup_restantes,
                        (fin if fin else total_heures) - max(debut, seuil_heures_sup),
                    )

                    if heures_dans_tranche > 0:
                        taux_majore = taux_horaire * (1 + majoration / 100)
                        salaire_tranche = heures_dans_tranche * taux_majore

                        result["heures_supplementaires"].append(
                            {
                                "de": debut,
                                "a": fin,
                                "heures": heures_dans_tranche,
                                "majoration": majoration,
                                "taux_majore": taux_majore,
                                "salaire": salaire_tranche,
                            }
                        )

                        result["salaire_supplementaire"] += salaire_tranche
                        heures_sup_restantes -= heures_dans_tranche

        # Calcul du salaire brut total
        result["salaire_brut_total"] = (
            result["salaire_normal"]
            + result["salaire_complementaire"]
            + result["salaire_complementaire_majore"]
            + result["salaire_supplementaire"]
        )

        # Détail des heures supplémentaires pour affichage
        result["detail_supplementaires"] = result["heures_supplementaires"]
        result["total_heures_supplementaires"] = sum(
            h["heures"] for h in result["heures_supplementaires"]
        )

        return result

    def _calculate_default_salary(
        self, total_heures: float, heures_contractuelles: float, taux_horaire: float
    ) -> Dict[str, Any]:
        """Calcul par défaut si le contrat n'est pas dans la configuration"""
        heures_normales = min(total_heures, heures_contractuelles)
        heures_sup = max(0, total_heures - heures_contractuelles)

        salaire_normal = heures_normales * taux_horaire
        salaire_sup = heures_sup * taux_horaire * 1.25  # 25% de majoration par défaut

        return {
            "contrat": f"{heures_contractuelles}h",
            "heures_contractuelles": heures_contractuelles,
            "total_heures": total_heures,
            "taux_horaire": taux_horaire,
            "heures_normales": heures_normales,
            "heures_complementaires": 0,
            "heures_complementaires_majorees": 0,
            "heures_supplementaires": (
                [{"heures": heures_sup, "majoration": 25}] if heures_sup > 0 else []
            ),
            "salaire_normal": salaire_normal,
            "salaire_complementaire": 0,
            "salaire_complementaire_majore": 0,
            "salaire_supplementaire": salaire_sup,
            "salaire_brut_total": salaire_normal + salaire_sup,
            "detail_supplementaires": [],
            "total_heures_supplementaires": heures_sup,
        }

    def get_available_contracts(self) -> List[Dict[str, Any]]:
        """Retourne la liste des contrats disponibles"""
        return [
            {
                "contrat": config["contrat"],
                "heures_contractuelles": config["heures_contractuelles"],
            }
            for config in self.config
        ]


# Instance globale du calculateur
salary_calculator = SalaryCalculator()
