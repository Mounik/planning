#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration email
"""

import os
from flask import Flask
from flask_mail import Mail, Message
from src.planning_pro.config import Config

# Configuration de test
app = Flask(__name__)
app.config.from_object(Config)

# Afficher la configuration
print("=== Configuration Email ===")
print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
print(f"MAIL_PASSWORD: {'***' if app.config.get('MAIL_PASSWORD') else 'None'}")
print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")

# Vérifier si la configuration est complète
missing_configs = []
if not app.config.get('MAIL_USERNAME'):
    missing_configs.append('MAIL_USERNAME')
if not app.config.get('MAIL_PASSWORD'):
    missing_configs.append('MAIL_PASSWORD')
if not app.config.get('MAIL_DEFAULT_SENDER'):
    missing_configs.append('MAIL_DEFAULT_SENDER')

if missing_configs:
    print(f"\n❌ Configuration manquante: {', '.join(missing_configs)}")
    print("\nPour configurer l'email, définissez ces variables d'environnement :")
    print("export MAIL_USERNAME='votre-email@gmail.com'")
    print("export MAIL_PASSWORD='votre-mot-de-passe-application'")
    print("export MAIL_DEFAULT_SENDER='votre-email@gmail.com'")
    print("\nNote: Pour Gmail, utilisez un mot de passe d'application, pas votre mot de passe normal.")
else:
    print("\n✅ Configuration email complète")

    # Test d'envoi
    with app.app_context():
        mail = Mail(app)

        try:
            msg = Message(
                "Test de configuration email",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[app.config['MAIL_USERNAME']]
            )
            msg.body = "Ceci est un test de configuration email pour l'application Planning Pro."

            mail.send(msg)
            print("✅ Email de test envoyé avec succès !")

        except Exception as e:
            print(f"❌ Erreur lors de l'envoi: {e}")
            print("\nVérifiez que :")
            print("1. Votre email et mot de passe sont corrects")
            print("2. L'authentification à deux facteurs est activée pour Gmail")
            print("3. Vous utilisez un mot de passe d'application (pas votre mot de passe normal)")