# Sécurité - Planning Pro 🔒

## 🛡️ Mesures de sécurité implémentées

### Authentification
- **Hachage des mots de passe** : bcrypt avec salt automatique
- **Tokens de réinitialisation** : Génération sécurisée avec expiration (1 heure)
- **Sessions utilisateur** : Gestion sécurisée avec Flask-Login
- **Validation des formulaires** : Vérification côté serveur

### Protection des données
- **Isolation utilisateur** : Chaque utilisateur ne peut accéder qu'à ses propres données
- **Validation des entrées** : Module `security.py` avec validation stricte
- **Sanitisation** : Échappement HTML et validation des formats
- **Stockage sécurisé** : Base SQLite avec requêtes préparées
- **Logs de sécurité** : Traçage des événements dans `data/security.log`

### Configuration sécurisée
- **Variables d'environnement** : Secrets stockés hors du code
- **Clé secrète** : Configuration obligatoire pour la production
- **HTTPS recommandé** : Pour la production

## 🔐 Configuration des secrets

### Fichier .env (recommandé)
```bash
# Copiez .env.example vers .env
cp .env.example .env

# Éditez .env avec vos vraies valeurs
nano .env
```

### Variables d'environnement critiques
```bash
# OBLIGATOIRE pour la production
SECRET_KEY=your-super-secret-key-minimum-32-characters

# Pour la récupération de mot de passe
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

## 🚨 Bonnes pratiques

### Développement
- ✅ Utilisez `.env` pour les secrets locaux
- ✅ Ne committez jamais `.env` dans Git
- ✅ Utilisez des valeurs de test uniquement
- ✅ Régénérez les secrets régulièrement

### Production
- ✅ Générez une `SECRET_KEY` unique et complexe
- ✅ Utilisez HTTPS obligatoirement
- ✅ Configurez un serveur SMTP sécurisé
- ✅ Sauvegardez les données régulièrement
- ✅ Surveillez les logs d'accès

## 🔑 Génération de clés sécurisées

### SECRET_KEY
```python
import secrets
secret_key = secrets.token_hex(32)
print(f"SECRET_KEY={secret_key}")
```

### Mot de passe d'application Gmail
1. Activez l'authentification à deux facteurs
2. Générez un mot de passe d'application
3. Utilisez ce mot de passe (pas votre mot de passe normal)

## 🛠️ Vérification de sécurité

### Script de vérification
```bash
# Vérifier la configuration
python -c "from src.planning_pro.config import Config; print('✅ Configuration OK' if Config.SECRET_KEY != 'dev-secret-key-change-in-production' else '❌ Changez SECRET_KEY')"
```

### Checklist de sécurité
- [ ] `SECRET_KEY` différente de la valeur par défaut
- [ ] `.env` dans `.gitignore`
- [ ] Mots de passe forts pour les comptes de test
- [ ] Configuration email sécurisée
- [ ] Sauvegarde de `data/planning.db`
- [ ] Logs surveillés en production (`data/*.log`)
- [ ] Module `security.py` activé pour la validation
- [ ] Requêtes SQLite sécurisées (requêtes préparées)
- [ ] Tests de sécurité passent (`uv run pytest tests/test_security.py`)
- [ ] Audit de sécurité propre (`uv run safety check`)
- [ ] Scan Bandit sans problème (`uv run bandit -r src/planning_pro`)

## 🚫 Ce qu'il ne faut PAS faire

### ❌ À éviter absolument
- Committer des secrets dans Git
- Utiliser la `SECRET_KEY` par défaut en production
- Partager des fichiers `.env`
- Utiliser des mots de passe faibles
- Exposer les données utilisateur
- Ignorer les erreurs de sécurité

### ❌ Fichiers à ne jamais committer
- `.env`
- `data/planning.db` (contient les données utilisateur)
- `data/*.log` (logs sensibles)
- `credentials.json`
- `config.secret.py`

## 🔍 Surveillance et monitoring

### Logs à surveiller
- **Security logs** : `data/security.log` - Événements de sécurité
- **Access logs** : `data/access.log` - Accès aux ressources
- **Error logs** : `data/error.log` - Erreurs applicatives
- Tentatives de connexion échouées
- Accès aux données sensibles
- Erreurs de configuration
- Requêtes suspectes

### Tests de sécurité automatisés
- **Validation d'entrées** : Tests des validateurs email, mot de passe, horaires
- **Sanitisation** : Tests d'échappement HTML et protection XSS
- **Schémas JSON** : Validation stricte des données API
- **Authentification** : Tests des mécanismes de connexion/déconnexion
- **Autorisation** : Vérification de l'isolation des données utilisateur

### Alertes recommandées
- Multiples tentatives de connexion
- Accès depuis des IP suspectes
- Erreurs répétées
- Utilisation anormale

## 📞 Signalement de vulnérabilités

Si vous découvrez une vulnérabilité de sécurité :

1. **NE PAS** créer d'issue publique
2. Contactez directement l'équipe de développement
3. Fournissez un rapport détaillé
4. Attendez une réponse avant divulgation

## 🔄 Mise à jour de sécurité

### Fréquence recommandée
- Vérifiez les dépendances : mensuelle
- Mettez à jour les secrets : trimestrielle
- Auditez les accès : semestrielle
- Sauvegardez `data/planning.db` : hebdomadaire
- Archivez les logs : mensuelle

### Commandes utiles
```bash
# Vérifier les vulnérabilités
uv run safety check

# Scan de sécurité du code
uv run bandit -r src/planning_pro

# Tests de sécurité
uv run pytest tests/test_security.py -v

# Audit complet
uv run safety check && uv run bandit -r src/planning_pro && uv run pytest tests/test_security.py

# Mettre à jour les dépendances
uv sync --upgrade

# Nettoyer les logs
rm -f data/*.log
```

---

**La sécurité est l'affaire de tous ! 🛡️**