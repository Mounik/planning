# Planning Pro 📅

Une application web Flask pour la gestion des plannings et feuilles d'heures, avec calcul automatique des salaires et heures supplémentaires.

## 🎯 Fonctionnalités

- **Authentification complète** : Inscription, connexion, récupération de mot de passe
- **Gestion des plannings** : Création, modification, suppression de plannings mensuels
- **Créneaux horaires flexibles** : Plusieurs créneaux par jour, gestion des horaires de nuit
- **Conversion automatique** : Transformation des plannings en feuilles d'heures
- **Calcul des salaires** : Heures normales, supplémentaires avec majoration (25%)
- **Interface responsive** : Design moderne avec Bootstrap 5

## 🚀 Installation

### Prérequis
- Python 3.12+
- uv (gestionnaire de paquets Python)

### Installation des dépendances
```bash
# Cloner le projet
git clone <votre-repo>
cd claude_planning

# Installer les dépendances
uv sync --dev
```

## 🏃 Démarrage rapide

### 1. Lancer l'application
```bash
uv run python main.py
```

### 2. Accéder à l'interface
Ouvrez votre navigateur à : http://localhost:5000

### 3. Créer un compte
- Cliquez sur "Créer un compte"
- Remplissez le formulaire d'inscription
- Connectez-vous avec vos identifiants

## 📊 Utilisation

### Créer un planning
1. Allez dans **Planning** → **Nouveau planning**
2. Définissez le mois, l'année et le taux horaire
3. Ajoutez vos créneaux de travail pour chaque jour
4. Sauvegardez votre planning

### Générer une feuille d'heures
1. Depuis la liste des plannings, cliquez sur **Convertir**
2. Consultez votre feuille d'heures avec les calculs automatiques
3. Visualisez le détail des heures normales et supplémentaires

### Récupération de mot de passe
1. Cliquez sur **"Mot de passe oublié ?"** depuis la page de connexion
2. Entrez votre email
3. **En mode développement** : Consultez la console du serveur pour le lien de réinitialisation
4. **En production** : Vérifiez votre boîte email

## ⚙️ Configuration

### Variables d'environnement (optionnelles)

#### Configuration email (production)
```bash
export MAIL_USERNAME="votre-email@gmail.com"
export MAIL_PASSWORD="votre-mot-de-passe-application"
export MAIL_DEFAULT_SENDER="votre-email@gmail.com"
```

#### Configuration sécurité
```bash
export SECRET_KEY="votre-clé-secrète-super-longue"
```

### Test de configuration email
```bash
uv run python test_email.py
```

## 🏗️ Architecture

```
claude_planning/
├── src/planning_pro/           # Code principal
│   ├── app.py                 # Application Flask
│   ├── models.py              # Modèles de données
│   └── config.py              # Configuration
├── templates/                 # Templates HTML
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── forgot_password.html
│   ├── reset_password.html
│   ├── index.html
│   ├── planning.html
│   └── feuille_heures.html
├── data/                      # Stockage JSON
│   ├── users.json
│   ├── plannings.json
│   └── feuilles_heures.json
├── main.py                    # Point d'entrée
├── test_email.py              # Test configuration email
└── EMAIL_CONFIG.md            # Documentation email
```

## 🔧 Développement

### Commandes utiles
```bash
# Démarrer l'application
uv run python main.py

# Formater le code
uv run black src/

# Vérifier le style
uv run flake8 src/

# Vérifier les types
uv run mypy src/planning_pro
```

### Modèles de données

#### User
- Authentification avec bcrypt
- Tokens de réinitialisation avec expiration
- Intégration Flask-Login

#### Planning
- Gestion des créneaux horaires par jour
- Conversion automatique en feuille d'heures
- Isolation par utilisateur

#### FeuilleDHeures
- Calcul automatique des heures supplémentaires
- Estimation du salaire brut
- Majoration configurable (25% par défaut)

## 📋 Fonctionnalités détaillées

### Gestion des heures
- **Heures normales** : Calculées selon les heures contractuelles (35h/semaine par défaut)
- **Heures supplémentaires** : Au-delà des heures normales mensuelles
- **Majoration** : 25% sur les heures supplémentaires
- **Créneaux de nuit** : Gestion des horaires qui s'étalent sur deux jours

### Sécurité
- Mots de passe hashés avec bcrypt
- Tokens de réinitialisation sécurisés avec expiration
- Sessions utilisateur avec Flask-Login
- Isolation des données par utilisateur

### Interface utilisateur
- Design responsive avec Bootstrap 5
- Messages flash pour les notifications
- Formulaires intuitifs avec validation
- Navigation claire et ergonomique

## 🐛 Dépannage

### Problèmes courants

#### L'application ne démarre pas
- Vérifiez que Python 3.12+ est installé
- Assurez-vous que `uv` est installé et configuré
- Exécutez `uv sync --dev` pour installer les dépendances

#### Récupération de mot de passe ne fonctionne pas
- En mode développement, consultez la console du serveur
- Pour la production, configurez les variables d'environnement email
- Utilisez `python test_email.py` pour tester la configuration

#### Données perdues
- Les données sont stockées dans le dossier `data/`
- Sauvegardez régulièrement les fichiers JSON
- En cas de corruption, supprimez les fichiers pour repartir à zéro

## 📚 Documentation technique

### Configuration des heures supplémentaires
```python
# Dans config.py
TAUX_MAJORATION_HEURES_SUP = 1.25  # 25% de majoration
```

### Calcul des heures normales mensuelles
```python
heures_normales_mois = heures_semaine * 52 / 12
```

### Stockage des données
- Format JSON pour simplicité
- Classe `DataStore` pour l'abstraction
- Sauvegarde automatique à chaque modification

## 🤝 Contribution

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité
3. Committez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour toute question ou problème :
1. Consultez la documentation dans `EMAIL_CONFIG.md`
2. Vérifiez les logs du serveur Flask
3. Utilisez les scripts de test fournis
4. Ouvrez une issue sur GitHub

---

**Développé avec ❤️ et Flask**