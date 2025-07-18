#!/usr/bin/env python3

"""
Test de génération PDF
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from planning_pro.pdf_generator import pdf_generator

def test_pdf_generation():
    """Test de génération PDF"""
    
    # Données de test
    feuille_data = {
        'id': 1,
        'mois': 7,
        'annee': 2025,
        'taux_horaire': 11.88,
        'heures_contractuelles': 30,
        'total_heures': 40,
        'jours_travailles': [
            {
                'date': '2025-07-01',
                'heures': 8,
                'creneaux': [
                    {'heure_debut': '11:00', 'heure_fin': '14:00'},
                    {'heure_debut': '19:00', 'heure_fin': '23:00'},
                    {'heure_debut': '09:00', 'heure_fin': '10:00'}
                ]
            },
            {
                'date': '2025-07-02',
                'heures': 8,
                'creneaux': [
                    {'heure_debut': '11:00', 'heure_fin': '14:00'},
                    {'heure_debut': '19:00', 'heure_fin': '23:00'},
                    {'heure_debut': '09:00', 'heure_fin': '10:00'}
                ]
            }
        ],
        'calcul_salaire': {
            'heures_normales': 30,
            'heures_complementaires': 3,
            'heures_complementaires_majorees': 2,
            'total_heures_supplementaires': 5,
            'salaire_normal': 356.40,
            'salaire_complementaire': 39.20,
            'salaire_complementaire_majore': 29.70,
            'salaire_supplementaire': 66.53,
            'salaire_brut_total': 491.83
        }
    }
    
    try:
        # Générer le PDF
        pdf_buffer = pdf_generator.generer_pdf_feuille(feuille_data)
        
        # Sauvegarder le PDF de test
        with open('test_feuille_heures.pdf', 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print("✓ PDF généré avec succès: test_feuille_heures.pdf")
        print(f"  Taille: {len(pdf_buffer.getvalue())} bytes")
        
        # Nettoyer
        os.remove('test_feuille_heures.pdf')
        print("✓ Fichier de test nettoyé")
        
    except Exception as e:
        print(f"✗ Erreur lors de la génération PDF: {e}")

if __name__ == "__main__":
    test_pdf_generation()