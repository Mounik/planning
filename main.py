#!/usr/bin/env python3
from src.planning_pro.app import app

def main():
    """Lance l'application Flask"""
    print("🚀 Démarrage du Gestionnaire d'Heures...")
    print("📍 Application disponible sur: http://localhost:5000")
    print("⏹️  Appuyez sur Ctrl+C pour arrêter")

    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
