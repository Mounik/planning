#!/usr/bin/env python3
"""
Script de debug pour examiner les dates dans la base de données
"""

import sqlite3
import sys
import os

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from planning_pro.database import db_manager

def debug_dates():
    """Examine les dates dans la base de données"""
    
    print("=== DEBUG DES DATES ===")
    
    # Vérifier les plannings
    print("\n1. PLANNINGS:")
    plannings = db_manager.execute_query("SELECT id, mois, annee FROM plannings ORDER BY annee DESC, mois DESC LIMIT 5")
    for planning in plannings:
        print(f"  Planning {planning['id']}: {planning['mois']}/{planning['annee']}")
        
        # Jours de travail du planning
        jours = db_manager.execute_query("SELECT date FROM jours_travail WHERE planning_id = ? ORDER BY date LIMIT 10", (planning['id'],))
        for jour in jours:
            print(f"    - Date: {jour['date']}")
    
    # Vérifier les feuilles d'heures
    print("\n2. FEUILLES D'HEURES:")
    feuilles = db_manager.execute_query("SELECT id, mois, annee FROM feuilles_heures ORDER BY annee DESC, mois DESC LIMIT 5")
    for feuille in feuilles:
        print(f"  Feuille {feuille['id']}: {feuille['mois']}/{feuille['annee']}")
        
        # Jours travaillés de la feuille
        jours = db_manager.execute_query("SELECT date FROM jours_travailles WHERE feuille_heures_id = ? ORDER BY date LIMIT 10", (feuille['id'],))
        for jour in jours:
            print(f"    - Date: {jour['date']}")
            
            # Test de parsing de la date
            try:
                parts = jour['date'].split('-')
                if len(parts) == 3:
                    annee, mois, jour_num = int(parts[0]), int(parts[1]), int(parts[2])
                    print(f"      Parsé: {jour_num}/{mois}/{annee}")
                    
                    # Test avec datetime
                    from datetime import datetime
                    date_obj = datetime(annee, mois, jour_num)
                    print(f"      Jour semaine: {date_obj.strftime('%A %d %B %Y')}")
                else:
                    print(f"      Erreur: format date invalide")
            except Exception as e:
                print(f"      Erreur parsing: {e}")

if __name__ == "__main__":
    debug_dates()