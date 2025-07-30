# 🗓️ Gestionnaire d'Heures - Planning Pro

Application web Flask pour la gestion des plannings de travail et le calcul des heures supplémentaires selon la législation française.

## ✨ Fonctionnalités

### 👤 Gestion des utilisateurs
- Inscription et connexion sécurisée
- Gestion des mots de passe avec bcrypt
- Réinitialisation de mot de passe par email
- Authentification avec Flask-Login

### 📅 Gestion des plannings
- Création de plannings mensuels avec interface calendrier
- Gestion des créneaux horaires flexibles
- Support multi-créneaux par jour
- Modification et suppression des plannings
- Interface intuitive avec sélection de dates

### 💰 Calcul des salaires
- **Système avancé** de calcul des heures supplémentaires et complémentaires
- Support des différents types de contrats :
  - 20h/semaine
  - 25h/semaine
  - 30h/semaine
  - 35h/semaine (temps plein)
  - 39h/semaine

### 📊 Heures supplémentaires et complémentaires
- **Heures complémentaires** (contrats partiels) :
  - Complémentaires normales : +10% de majoration
  - Complémentaires majorées : +25% de majoration
- **Heures supplémentaires** (au-delà de 35h) :
  - 36h-39h : +10% de majoration
  - 39h-43h : +20% de majoration
  - 43h et plus : +50% de majoration

### 📈 Feuilles d'heures
- Conversion automatique des plannings en feuilles d'heures
- Calcul détaillé des salaires par catégorie d'heures
- Affichage des totaux et répartition des heures
- Export et visualisation des données

## 🏗️ Architecture technique

### Backend
- **Framework** : Flask avec Python 3.8+
- **Base de données** : SQLite avec gestion des relations
- **Gestionnaire BDD** : Module database.py personnalisé
- **Sécurité** : bcrypt pour les mots de passe, Flask-Login pour l'authentification

### Frontend
- **Templates** : Jinja2 avec Bootstrap 5
- **JavaScript** : Vanilla JS avec API REST
- **Interface** : Responsive design avec FontAwesome

### Structure des données
```
📁 data/
├── planning.db          # Base de données SQLite
├── access.log          # Logs d'accès
├── error.log           # Logs d'erreurs
└── security.log        # Logs de sécurité

📁 src/planning_pro/
├── app.py                    # Application Flask principale
├── models.py                 # Modèles de données SQLite
├── database.py               # Gestionnaire de base de données
├── salary_calculator.py      # Calculateur de salaires avancé
├── net_salary_calculator.py  # Calculateur de salaire net
├── pdf_generator.py          # Générateur de PDF
├── security.py               # Utilitaires de sécurité
└── config.py                 # Configuration

📁 templates/           # Templates HTML Jinja2
```

## 🚀 Installation et démarrage

### Prérequis
- Python 3.8+
- uv (gestionnaire de paquets Python)

### Installation
```bash
# Cloner le projet
git clone <repository-url>
cd claude_planning

# Installer les dépendances
uv sync --dev

# Configuration sécurisée
cp .env.example .env
# Éditer .env avec vos paramètres (SECRET_KEY obligatoire)

# Démarrer l'application
uv run python run_prod.py
```

### Configuration
1. **Obligatoire** : Configurer `SECRET_KEY` dans `.env`
2. **Recommandé** : Configurer l'email dans `.env` pour la récupération de mot de passe
3. **Production** : Activer HTTPS avec `FORCE_HTTPS=true`
4. Créer un compte utilisateur via l'interface web
5. Commencer à créer des plannings !

### Déploiement production
```bash
# Générer une clé secrète
uv run python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env

# Configurer la production
echo "SESSION_COOKIE_SECURE=true" >> .env
echo "FORCE_HTTPS=true" >> .env
echo "CSRF_SSL_STRICT=true" >> .env

# Démarrer avec Gunicorn
uv run python run_prod.py
```

## 📖 Utilisation

### 1. Créer un planning
1. Sélectionner le mois et l'année
2. Choisir le type de contrat (20h, 25h, 30h, 35h, 39h)
3. Saisir le taux horaire
4. Générer le calendrier et remplir les créneaux de travail
5. Sauvegarder le planning

### 2. Consulter les feuilles d'heures
1. Convertir un planning en feuille d'heures
2. Visualiser le détail des heures par catégorie
3. Consulter le calcul de salaire détaillé

### 3. Gestion des heures
L'application calcule automatiquement :
- Les heures normales selon le contrat
- Les heures complémentaires (contrats partiels)
- Les heures supplémentaires (au-delà de 35h)
- Les majorations correspondantes

## 🔧 Développement

### Commandes utiles
```bash
# Formatage du code
uv run black src/

# Vérification du style
uv run flake8 src/

# Vérification des types
uv run mypy src/planning_pro

# Tests complets
uv run pytest tests/

# Tests avec couverture
uv run pytest tests/ --cov

# Tests par catégorie
uv run pytest tests/ -m unit          # Tests unitaires
uv run pytest tests/ -m integration   # Tests d'intégration
uv run pytest tests/ -m security      # Tests de sécurité
uv run pytest tests/ -m api           # Tests API

# Audit de sécurité
uv run safety check
uv run bandit -r src/planning_pro
```

### Structure du projet
```
planning/
├── src/planning_pro/                # Code source principal
│   ├── app.py                      # Routes Flask et API
│   ├── models.py                   # Modèles SQLite
│   ├── database.py                 # Gestionnaire BDD
│   ├── salary_calculator.py        # Calculs de salaires
│   ├── net_salary_calculator.py    # Calculs de salaire net
│   ├── pdf_generator.py            # Génération de PDF
│   ├── security.py                 # Utilitaires de sécurité
│   └── config.py                   # Configuration
├── templates/                       # Templates HTML
├── tests/                          # Suite de tests complète
│   ├── __init__.py
│   ├── conftest.py                 # Configuration pytest
│   ├── test_models.py              # Tests unitaires modèles
│   ├── test_api.py                 # Tests endpoints API
│   ├── test_security.py            # Tests module sécurité
│   ├── test_salary_calculator.py   # Tests calculateurs
│   └── test_integration.py         # Tests d'intégration
├── .github/workflows/              # GitHub Actions CI/CD
│   └── ci.yml                      # Pipeline automatisé
├── data/                           # Base de données et logs
├── main.py                         # Point d'entrée développement
├── run_prod.py                     # Point d'entrée production
├── pytest.ini                     # Configuration pytest
└── pyproject.toml                  # Configuration uv + outils
```

## 📡 API REST

### Endpoints principaux
- `GET/POST /api/planning` - Gestion des plannings
- `GET/PUT/DELETE /api/planning/<id>` - Planning spécifique
- `POST /api/planning/<id>/convert` - Conversion en feuille d'heures
- `GET /api/feuille-heures` - Liste des feuilles d'heures
- `GET/DELETE /api/feuille-heures/<id>` - Feuille d'heures spécifique
- `GET /api/contracts` - Types de contrats disponibles

### Format des données API
Les données sont stockées en SQLite et échangées via API REST au format JSON :

**Exemple de planning :**
```json
{
  "mois": 1,
  "annee": 2025,
  "taux_horaire": 15.50,
  "heures_contractuelles": 35,
  "jours_travail": [
    {
      "date": "2025-01-15",
      "creneaux": [
        {"heure_debut": "09:00", "heure_fin": "12:00"},
        {"heure_debut": "13:00", "heure_fin": "17:00"}
      ]
    }
  ]
}
```

## 🧪 Tests et Qualité

### Suite de tests complète

L'application dispose d'une suite de tests exhaustive couvrant :

#### Tests unitaires
- **Modèles** : User, Planning, CreneauTravail, JourTravaille
- **Calculateurs** : Salaire brut, net, tous types de contrats
- **Sécurité** : Validation, sanitisation, schémas JSON

#### Tests d'intégration
- **Workflows utilisateur** : Inscription → Connexion → Planning → Feuille heures
- **CRUD Planning** : Création, lecture, mise à jour, suppression
- **Calculs salaire** : Cohérence entre plannings et feuilles d'heures

#### Tests API
- **Authentification** : Inscription, connexion, déconnexion
- **Endpoints Planning** : Tous les endpoints avec validation
- **Gestion erreurs** : Codes d'erreur, validation des données

#### Tests de sécurité
- **Validation données** : Emails, mots de passe, horaires, dates
- **Sanitisation** : Protection XSS, injection
- **Schémas JSON** : Validation stricte des API

### Configuration qualité

```bash
# Couverture de tests minimale : 80%
pytest --cov --cov-fail-under=80

# Vérifications automatiques
black --check src/           # Formatage
flake8 src/                 # Style de code
mypy src/planning_pro       # Types
safety check                # Vulnérabilités
bandit -r src/planning_pro  # Sécurité
```

### CI/CD avec GitHub Actions

Pipeline automatisé qui vérifie :
- **Tests** : Python 3.8-3.11, pytest avec coverage
- **Qualité** : Black, flake8, mypy
- **Sécurité** : Safety, Bandit
- **Intégration** : Démarrage application
- **Performance** : Tests de charge basiques
- **Artifacts** : Build et rapports

## 🔐 Sécurité

L'application est prête pour la production avec des mesures de sécurité complètes :

### Authentification et autorisation
- **Mots de passe** : Hashage bcrypt avec salt
- **Sessions** : Flask-Login avec cookies sécurisés
- **Tokens** : Système de réinitialisation de mot de passe avec expiration

### Protection des données
- **Validation** : Sanitisation et validation stricte des entrées
- **CSRF** : Protection contre les attaques Cross-Site Request Forgery
- **Headers** : Headers de sécurité (CSP, HSTS, X-Frame-Options)
- **Rate limiting** : Limitation des requêtes par IP

### Logging et monitoring
- **Logs de sécurité** : Traçage des événements critiques
- **Gestion d'erreurs** : Codes d'erreur avec IDs pour le support
- **Audit trail** : Historique des actions utilisateur

### Configuration sécurisée
- **Variables d'environnement** : Configuration sensible externalisée
- **Mode production** : DEBUG=false par défaut
- **Déploiement** : Configuration Gunicorn pour la production

## 🗄️ Base de données

### Schéma SQLite
- **users** : Gestion des utilisateurs
- **plannings** : Plannings mensuels
- **jours_travail** : Jours de travail d'un planning
- **creneaux_travail** : Créneaux horaires des jours
- **feuilles_heures** : Feuilles d'heures générées
- **jours_travailles** : Jours travaillés d'une feuille
- **creneaux_feuille** : Créneaux des feuilles d'heures

### Architecture SQLite
L'application utilise SQLite pour :
- Performances optimisées
- Intégrité des données garantie
- Requêtes complexes facilité
- Montée en charge possible

## 🎯 Conformité légale

Le calcul des heures supplémentaires suit la législation française :
- Heures complémentaires pour les contrats partiels
- Seuils de majoration conformes au Code du travail
- Distinction entre heures normales, complémentaires et supplémentaires

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de :
1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📞 Support

Pour toute question ou problème :
- Créer une issue sur GitHub
- Consulter la documentation dans `/docs`
- Vérifier les logs de l'application

---

*Développé avec ❤️ pour simplifier la gestion des plannings de travail*