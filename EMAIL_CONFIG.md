# Configuration Email pour la Récupération de Mot de Passe

## ✅ Fonctionnement actuel

La récupération de mot de passe fonctionne en **mode développement** :
- Si la configuration email n'est pas complète, le lien de réinitialisation s'affiche dans la console
- Vous pouvez copier ce lien et l'utiliser directement dans votre navigateur

## 🔧 Configuration Production (Optionnelle)

Pour envoyer de vrais emails en production, configurez ces variables d'environnement :

### Pour Gmail :

```bash
export MAIL_USERNAME="votre-email@gmail.com"
export MAIL_PASSWORD="votre-mot-de-passe-application"
export MAIL_DEFAULT_SENDER="votre-email@gmail.com"
```

### Étapes pour Gmail :

1. **Activez l'authentification à deux facteurs** sur votre compte Google
2. **Générez un mot de passe d'application** :
   - Allez dans les paramètres de votre compte Google
   - Sécurité → Authentification à deux facteurs → Mots de passe des applications
   - Générez un nouveau mot de passe pour "Mail"
3. **Utilisez ce mot de passe d'application** (pas votre mot de passe normal)

### Pour d'autres fournisseurs :

```bash
export MAIL_SERVER="smtp.votre-fournisseur.com"
export MAIL_PORT="587"
export MAIL_USE_TLS="true"
export MAIL_USERNAME="votre-email@domaine.com"
export MAIL_PASSWORD="votre-mot-de-passe"
export MAIL_DEFAULT_SENDER="votre-email@domaine.com"
```

## 🧪 Test de Configuration

Utilisez le script de test pour vérifier votre configuration :

```bash
uv run python test_email.py
```

## 📝 Comment utiliser en développement

1. **Créez un utilisateur** via la page d'inscription
2. **Allez sur "Mot de passe oublié"** et entrez votre email
3. **Consultez la console** du serveur Flask pour voir le lien de réinitialisation
4. **Copiez le lien** et ouvrez-le dans votre navigateur
5. **Définissez un nouveau mot de passe**

## 🔍 Dépannage

### Si le lien ne fonctionne pas :
- Vérifiez que le token n'a pas expiré (1 heure)
- Assurez-vous d'utiliser le bon domaine (localhost:5000)
- Consultez les logs du serveur pour les erreurs

### Si l'email ne s'envoie pas :
- Vérifiez les variables d'environnement
- Testez avec `python test_email.py`
- Consultez les logs du serveur pour les erreurs détaillées