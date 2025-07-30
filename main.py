#!/usr/bin/env python3
import os
from src.planning_pro.app import app

def main():
    """Lance l'application Flask"""
    debug_mode = os.environ.get('DEBUG', 'false').lower() == 'true'
    port = int(os.environ.get('PORT', '8080'))

    if debug_mode:
        print("⚠️  WARNING: Debug mode is enabled!")
        print("🚀 Démarrage du Gestionnaire d'Heures (DEBUG)...")
        print(f"📍 Application disponible sur: http://localhost:{port}")
        print("⏹️  Appuyez sur Ctrl+C pour arrêter")
        app.run(debug=True, host='127.0.0.1', port=port)
    else:
        print("🚀 Démarrage du Gestionnaire d'Heures (PRODUCTION)...")
        print(f"📍 Application disponible sur: http://127.0.0.1:{port}")
        print("⚠️  Use a production WSGI server (gunicorn) for production deployment")
        print("⏹️  Appuyez sur Ctrl+C pour arrêter")
        app.run(debug=False, host='127.0.0.1', port=port)

if __name__ == "__main__":
    main()
