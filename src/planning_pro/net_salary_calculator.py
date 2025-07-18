"""
Calculateur de salaire net approximatif
"""

from typing import Dict, Any


class NetSalaryCalculator:
    """Calculateur de salaire net approximatif pour la France"""

    def __init__(self):
        # Taux de cotisations salariales approximatifs (2024)
        self.cotisations_salarie = {
            "securite_sociale": 0.023,  # CSG déductible
            "csg_crds": 0.0925,  # CSG/CRDS
            "assurance_chomage": 0.024,  # Assurance chômage
            "retraite_complementaire": 0.0387,  # AGIRC-ARRCO
            "retraite_securite_sociale": 0.1105,  # Retraite sécurité sociale
        }

        # Taux total approximatif
        self.taux_total_cotisations = sum(self.cotisations_salarie.values())

        # Seuils pour l'impôt sur le revenu (barème 2024, célibataire)
        self.tranches_impot = [
            (10777, 0.0),  # Jusqu'à 10 777€ : 0%
            (27478, 0.11),  # De 10 778€ à 27 478€ : 11%
            (78570, 0.30),  # De 27 479€ à 78 570€ : 30%
            (168994, 0.41),  # De 78 571€ à 168 994€ : 41%
            (float("inf"), 0.45),  # Au-delà : 45%
        ]

    def calculer_salaire_net(self, salaire_brut_mensuel: float) -> Dict[str, Any]:
        """
        Calcule le salaire net approximatif à partir du salaire brut mensuel

        Args:
            salaire_brut_mensuel: Salaire brut mensuel en euros

        Returns:
            Dict contenant les détails du calcul
        """
        # Calcul du salaire net après cotisations sociales
        cotisations_sociales = salaire_brut_mensuel * self.taux_total_cotisations
        salaire_net_avant_impot = salaire_brut_mensuel - cotisations_sociales

        # Calcul de l'impôt sur le revenu (estimation annuelle)
        salaire_annuel_net = salaire_net_avant_impot * 12
        impot_annuel = self._calculer_impot_annuel(salaire_annuel_net)
        impot_mensuel = impot_annuel / 12

        # Salaire net final
        salaire_net_final = salaire_net_avant_impot - impot_mensuel

        return {
            "salaire_brut": salaire_brut_mensuel,
            "cotisations_sociales": cotisations_sociales,
            "salaire_net_avant_impot": salaire_net_avant_impot,
            "impot_mensuel": impot_mensuel,
            "salaire_net_final": salaire_net_final,
            "taux_cotisations": self.taux_total_cotisations * 100,
            "taux_impot_effectif": (
                (impot_mensuel / salaire_brut_mensuel * 100)
                if salaire_brut_mensuel > 0
                else 0
            ),
        }

    def _calculer_impot_annuel(self, salaire_annuel_net: float) -> float:
        """Calcule l'impôt sur le revenu annuel selon le barème progressif"""
        if salaire_annuel_net <= 0:
            return 0

        # Abattement forfaitaire de 10% pour frais professionnels (minimum 448€, maximum 12 829€)
        abattement = min(max(salaire_annuel_net * 0.10, 448), 12829)
        revenu_imposable = max(0, salaire_annuel_net - abattement)

        impot = 0
        revenu_restant = revenu_imposable
        tranche_precedente = 0

        for seuil, taux in self.tranches_impot:
            if revenu_restant <= 0:
                break

            tranche_imposable = min(revenu_restant, seuil - tranche_precedente)
            impot += tranche_imposable * taux
            revenu_restant -= tranche_imposable
            tranche_precedente = seuil

        return max(0, impot)

    def get_estimation_disclaimer(self) -> str:
        """Retourne le texte d'avertissement sur l'estimation"""
        return (
            "⚠️ Estimation approximative basée sur les taux 2024 pour un salarié célibataire sans enfant. "
            "Les cotisations réelles peuvent varier selon votre situation personnelle, votre entreprise, "
            "et votre régime de retraite complémentaire. Cette estimation ne remplace pas un calcul officiel."
        )


# Instance globale
net_salary_calculator = NetSalaryCalculator()
