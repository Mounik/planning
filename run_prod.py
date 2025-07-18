#!/usr/bin/env python3
"""
Script de démarrage pour la production avec Gunicorn
"""
import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Vérifie que les dépendances sont installées"""
    try:
        import gunicorn
        print("✅ Gunicorn installé")
    except ImportError:
        print("❌ Gunicorn n'est pas installé. Exécutez: uv add gunicorn")
        sys.exit(1)

def setup_environment():
    """Configure l'environnement de production"""
    # Variables d'environnement par défaut pour la production
    production_env = {
        'DEBUG': 'false',
        'FLASK_ENV': 'production',
        'SECURITY_HEADERS': 'true',
        'SESSION_COOKIE_SECURE': 'false',  # Mettre à true avec HTTPS
        'FORCE_HTTPS': 'false',  # Mettre à true en production avec HTTPS
        'CSRF_SSL_STRICT': 'false',  # Mettre à true avec HTTPS
    }

    # Appliquer les variables d'environnement
    for key, value in production_env.items():
        if key not in os.environ:
            os.environ[key] = value

    # Vérifier SECRET_KEY
    if not os.environ.get('SECRET_KEY'):
        print("⚠️  WARNING: SECRET_KEY n'est pas défini!")
        print("   Générez une clé secrète avec: python -c 'import secrets; print(secrets.token_urlsafe(32))'")
        print("   Puis ajoutez-la à votre fichier .env: SECRET_KEY=votre_cle_secrete")

def create_directories():
    """Crée les répertoires nécessaires"""
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)

    # Créer les fichiers de log
    (data_dir / 'access.log').touch()
    (data_dir / 'error.log').touch()
    (data_dir / 'security.log').touch()

    print("✅ Répertoires et fichiers de log créés")

def run_gunicorn():
    """Lance Gunicorn avec la configuration de production"""
    cmd = [
        'gunicorn',
        '--config', 'gunicorn_config.py',
        'src.planning_pro.app:app'
    ]

    print("🚀 Démarrage de l'application en mode production...")
    print("📍 Application disponible sur: http://127.0.0.1:5000")
    print("📋 Logs disponibles dans le répertoire 'data/'")
    print("⏹️  Appuyez sur Ctrl+C pour arrêter")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de l'application...")

def main():
    """Fonction principale"""
    print("🔧 Configuration de l'environnement de production...")

    check_dependencies()
    setup_environment()
    create_directories()

    print("\n" + "="*50)
    print("🚀 DÉMARRAGE EN MODE PRODUCTION")
    print("="*50)

    run_gunicorn()

if __name__ == "__main__":
    main()