from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
import os
import logging
import traceback
from datetime import datetime
from .models import Planning, FeuilleDHeures, User
from .database import db_manager
from .config import Config
from .security import (
    validator,
    log_security_event,
    rate_limit,
)

# Chemin vers le répertoire racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)
app.config.from_object(Config)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("data/security.log"), logging.StreamHandler()],
)

# Configuration de la sécurité
csrf = CSRFProtect(app)

# Configuration des headers de sécurité avec Talisman
if app.config.get("SECURITY_HEADERS", True):
    csp = {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        "font-src": "'self' https://cdnjs.cloudflare.com",
        "img-src": "'self' data:",
        "connect-src": "'self'",
    }

    Talisman(
        app,
        force_https=app.config.get("FORCE_HTTPS", False),
        strict_transport_security=True,
        content_security_policy=csp,
        session_cookie_secure=app.config.get("SESSION_COOKIE_SECURE", False),
    )

# Configuration Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # type: ignore[assignment]
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

# Configuration Flask-Mail
mail = Mail(app)


@app.errorhandler(400)
def handle_bad_request(error):
    """Gestion des erreurs 400 - Bad Request"""
    log_security_event(
        "HTTP_400", f"Bad request: {error.description}", ip_address=request.remote_addr
    )
    if request.is_json:
        return jsonify({"error": "Requête invalide", "details": error.description}), 400
    flash("Requête invalide", "error")
    return (
        render_template("error.html", error_code=400, error_message="Requête invalide"),
        400,
    )


@app.errorhandler(401)
def handle_unauthorized(error):
    """Gestion des erreurs 401 - Unauthorized"""
    log_security_event(
        "HTTP_401", "Unauthorized access attempt", ip_address=request.remote_addr
    )
    if request.is_json:
        return jsonify({"error": "Accès non autorisé"}), 401
    flash("Accès non autorisé", "error")
    return redirect(url_for("login"))


@app.errorhandler(403)
def handle_forbidden(error):
    """Gestion des erreurs 403 - Forbidden"""
    log_security_event(
        "HTTP_403", "Forbidden access attempt", ip_address=request.remote_addr
    )
    if request.is_json:
        return jsonify({"error": "Accès interdit"}), 403
    flash("Accès interdit", "error")
    return (
        render_template("error.html", error_code=403, error_message="Accès interdit"),
        403,
    )


@app.errorhandler(404)
def handle_not_found(error):
    """Gestion des erreurs 404 - Not Found"""
    if request.is_json:
        return jsonify({"error": "Ressource non trouvée"}), 404
    flash("Page non trouvée", "error")
    return (
        render_template("error.html", error_code=404, error_message="Page non trouvée"),
        404,
    )


@app.errorhandler(500)
def handle_internal_error(error):
    """Gestion des erreurs 500 - Internal Server Error"""
    error_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_security_event(
        "HTTP_500",
        f"Internal server error [ID: {error_id}] - {str(error)}",
        ip_address=request.remote_addr,
    )

    # Log détaillé pour le débogage
    if current_app.debug:
        current_app.logger.error(
            f"Internal error [{error_id}]: {traceback.format_exc()}"
        )

    if request.is_json:
        return (
            jsonify({"error": "Erreur interne du serveur", "error_id": error_id}),
            500,
        )

    flash(f"Erreur interne du serveur (ID: {error_id})", "error")
    return (
        render_template(
            "error.html", error_code=500, error_message="Erreur interne du serveur"
        ),
        500,
    )


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Gestion des erreurs non gérées"""
    error_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_security_event(
        "UNEXPECTED_ERROR",
        f"Unexpected error [ID: {error_id}] - {str(error)}",
        ip_address=request.remote_addr,
    )

    # Log détaillé pour le débogage
    current_app.logger.error(f"Unexpected error [{error_id}]: {traceback.format_exc()}")

    if request.is_json:
        return jsonify({"error": "Erreur inattendue", "error_id": error_id}), 500

    flash(f"Erreur inattendue (ID: {error_id})", "error")
    return (
        render_template(
            "error.html", error_code=500, error_message="Erreur inattendue"
        ),
        500,
    )


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get_by_id(int(user_id))
    except (ValueError, TypeError):
        return None


# Routes d'authentification
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email and password:
            user = User.get_by_email(email)
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get("next")
                return redirect(next_page) if next_page else redirect(url_for("index"))
            else:
                flash("Email ou mot de passe incorrect", "error")
        else:
            flash("Email et mot de passe requis", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
@rate_limit(max_requests=10, window_seconds=3600)  # Max 10 inscriptions par heure
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        nom = request.form.get("nom", "").strip()
        prenom = request.form.get("prenom", "").strip()

        # Validation des données
        if not all([email, password, nom, prenom]):
            log_security_event(
                "REGISTRATION_FAILED",
                "Missing required fields",
                ip_address=request.remote_addr,
            )
            flash("Tous les champs sont requis", "error")
            return render_template("register.html")

        # Validation de l'email
        if not validator.validate_email(email):
            log_security_event(
                "REGISTRATION_FAILED",
                f"Invalid email format: {email}",
                ip_address=request.remote_addr,
            )
            flash("Format d'email invalide", "error")
            return render_template("register.html")

        # Validation du mot de passe
        is_valid_password, password_message = validator.validate_password(password)
        if not is_valid_password:
            log_security_event(
                "REGISTRATION_FAILED",
                f"Weak password for {email}",
                ip_address=request.remote_addr,
            )
            flash(password_message, "error")
            return render_template("register.html")

        # Validation du nom et prénom
        if not validator.validate_name(nom) or not validator.validate_name(prenom):
            log_security_event(
                "REGISTRATION_FAILED",
                f"Invalid name format for {email}",
                ip_address=request.remote_addr,
            )
            flash(
                "Nom et prénom invalides (2-50 caractères, lettres uniquement)", "error"
            )
            return render_template("register.html")

        # Vérifier si l'utilisateur existe déjà
        if User.get_by_email(email):
            log_security_event(
                "REGISTRATION_FAILED",
                f"Account already exists: {email}",
                ip_address=request.remote_addr,
            )
            flash("Un compte avec cet email existe déjà", "error")
            return render_template("register.html")

        try:
            # Sanitiser les données
            email = validator.sanitize_string(email.lower())
            nom = validator.sanitize_string(nom)
            prenom = validator.sanitize_string(prenom)

            # Créer le nouvel utilisateur
            user = User(email=email, password=password, nom=nom, prenom=prenom)
            user.save()

            log_security_event(
                "REGISTRATION_SUCCESS",
                f"New account created: {email}",
                ip_address=request.remote_addr,
            )
            flash(
                "Compte créé avec succès ! Vous pouvez maintenant vous connecter.",
                "success",
            )
            return redirect(url_for("login"))
        except Exception as e:
            log_security_event(
                "REGISTRATION_ERROR",
                f"Account creation failed for {email}: {str(e)}",
                ip_address=request.remote_addr,
            )
            flash("Erreur lors de la création du compte", "error")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Vous avez été déconnecté", "info")
    return redirect(url_for("login"))


# Routes de récupération de mot de passe
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        if not email:
            flash("Veuillez entrer votre adresse email", "error")
            return render_template("forgot_password.html")

        user = User.get_by_email(email)
        if user:
            token = user.generate_reset_token()

            # Générer l'URL de réinitialisation
            reset_url = url_for("reset_password", token=token, _external=True)

            # Vérifier la configuration email
            if not app.config.get("MAIL_DEFAULT_SENDER"):
                # Mode développement : afficher le lien directement
                print(f"\n=== MODE DÉVELOPPEMENT - EMAIL NON CONFIGURÉ ===")
                print(f"Lien de réinitialisation pour {user.email}:")
                print(f"{reset_url}")
                print("=" * 50)

                flash(
                    f"Mode développement: Lien de réinitialisation affiché dans la console",
                    "info",
                )
                flash(
                    "Configuration email manquante. Consultez test_email.py pour la configuration.",
                    "warning",
                )
                return redirect(url_for("login"))

            # Envoyer l'email de réinitialisation
            try:
                msg = Message(
                    "Réinitialisation de votre mot de passe",
                    sender=app.config["MAIL_DEFAULT_SENDER"],
                    recipients=[email],
                )

                msg.body = f"""
Bonjour {user.prenom},

Vous avez demandé la réinitialisation de votre mot de passe.

Cliquez sur le lien suivant pour réinitialiser votre mot de passe :
{reset_url}

Ce lien expirera dans 1 heure.

Si vous n'avez pas demandé cette réinitialisation, ignorez simplement cet email.

Cordialement,
L'équipe Planning Pro
"""

                mail.send(msg)
                flash(
                    "Un email de réinitialisation a été envoyé à votre adresse email",
                    "success",
                )
                return redirect(url_for("login"))

            except Exception as e:
                # En cas d'erreur, afficher le lien en mode développement
                print(f"\n=== ERREUR EMAIL - AFFICHAGE DU LIEN ===")
                print(f"Erreur: {e}")
                print(f"Lien de réinitialisation pour {user.email}:")
                print(f"{reset_url}")
                print("=" * 50)

                flash(
                    f"Erreur email, mais lien affiché dans la console",
                    "warning",
                )
                return redirect(url_for("login"))
        else:
            # Pour des raisons de sécurité, on affiche le même message même si l'email n'existe pas
            flash(
                "Un email de réinitialisation a été envoyé à votre adresse email",
                "success",
            )
            return redirect(url_for("login"))

    return render_template("forgot_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.get_by_reset_token(token)
    if not user:
        flash("Le lien de réinitialisation est invalide ou a expiré", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not password or not confirm_password:
            flash("Veuillez remplir tous les champs", "error")
            return render_template("reset_password.html", token=token)

        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas", "error")
            return render_template("reset_password.html", token=token)

        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères", "error")
            return render_template("reset_password.html", token=token)

        # Réinitialiser le mot de passe
        if user.reset_password(password, token):
            flash("Votre mot de passe a été réinitialisé avec succès", "success")
            return redirect(url_for("login"))
        else:
            flash("Erreur lors de la réinitialisation du mot de passe", "error")

    return render_template("reset_password.html", token=token)


# Routes principales (protégées)
@app.route("/")
@login_required
def index():
    # Récupérer les plannings récents pour l'utilisateur connecté
    plannings = Planning.get_by_user(current_user.id)
    feuilles = FeuilleDHeures.get_by_user(current_user.id)

    # Statistiques rapides
    total_plannings = len(plannings)
    total_feuilles = len(feuilles)

    return render_template(
        "index.html",
        plannings=plannings[:5],  # 5 plannings récents
        feuilles=feuilles[:5],  # 5 feuilles récentes
        total_plannings=total_plannings,
        total_feuilles=total_feuilles,
    )


@app.route("/planning", methods=["GET", "POST"])
@login_required
def planning():
    if request.method == "POST":
        # Traitement du formulaire de création/modification de planning
        planning_id = request.form.get("planning_id")

        if planning_id:
            # Modification
            try:
                planning_obj = Planning.get_by_id(int(planning_id))
                if not planning_obj or planning_obj.user_id != current_user.id:
                    flash("Planning non trouvé", "error")
                    return redirect(url_for("planning"))
            except (ValueError, TypeError):
                flash("ID de planning invalide", "error")
                return redirect(url_for("planning"))
        else:
            # Création
            planning_obj = None

        # Récupérer les données du formulaire
        mois_str = request.form.get("mois")
        annee_str = request.form.get("annee")
        taux_horaire_str = request.form.get("taux_horaire")
        heures_contractuelles_str = request.form.get("heures_contractuelles", "35.0")

        if not all([mois_str, annee_str, taux_horaire_str]):
            flash("Tous les champs sont requis", "error")
            return redirect(url_for("planning"))

        try:
            mois = int(mois_str) if mois_str else 0
            annee = int(annee_str) if annee_str else 0
            taux_horaire = float(taux_horaire_str) if taux_horaire_str else 0.0
            heures_contractuelles = (
                float(heures_contractuelles_str) if heures_contractuelles_str else 35.0
            )
        except ValueError:
            flash("Valeurs numériques invalides", "error")
            return redirect(url_for("planning"))

        # Construire la liste des jours de travail
        jours_travail = []
        for key in request.form:
            if key.startswith("date_"):
                date_str = request.form[key]
                if date_str:
                    creneaux = []
                    # Chercher les créneaux pour cette date
                    for creneau_key in request.form:
                        if creneau_key.startswith(f"creneau_{date_str}_"):
                            parts = creneau_key.split("_")
                            if len(parts) >= 4:
                                heure_type = parts[3]  # 'debut' ou 'fin'
                                creneau_idx = parts[2]

                                if heure_type == "debut":
                                    heure_debut = request.form[creneau_key]
                                    heure_fin_key = (
                                        f"creneau_{date_str}_{creneau_idx}_fin"
                                    )
                                    heure_fin = request.form.get(heure_fin_key)

                                    if heure_debut and heure_fin:
                                        creneaux.append(
                                            {
                                                "heure_debut": heure_debut,
                                                "heure_fin": heure_fin,
                                            }
                                        )

                    if creneaux:
                        jours_travail.append({"date": date_str, "creneaux": creneaux})

        if planning_obj:
            # Mise à jour
            planning_obj.mois = mois
            planning_obj.annee = annee
            planning_obj.jours_travail = jours_travail
            planning_obj.taux_horaire = taux_horaire
            planning_obj.heures_contractuelles = heures_contractuelles
            planning_obj.save()
            flash("Planning mis à jour avec succès !", "success")
        else:
            # Création
            planning_obj = Planning(
                mois=mois,
                annee=annee,
                jours_travail=jours_travail,
                taux_horaire=taux_horaire,
                user_id=current_user.id,
                heures_contractuelles=heures_contractuelles,
            )
            planning_obj.save()
            flash("Planning créé avec succès !", "success")

        return redirect(url_for("planning"))

    # GET: Afficher la liste des plannings
    plannings = Planning.get_by_user(current_user.id)

    # Planning à éditer si spécifié
    edit_planning = None
    edit_id = request.args.get("edit")
    if edit_id:
        try:
            edit_planning = Planning.get_by_id(int(edit_id))
            if not edit_planning or edit_planning.user_id != current_user.id:
                edit_planning = None
        except (ValueError, TypeError):
            edit_planning = None

    return render_template(
        "planning.html", plannings=plannings, edit_planning=edit_planning
    )


@app.route("/planning/<int:planning_id>/delete", methods=["POST"])
@login_required
def delete_planning(planning_id):
    planning_obj = Planning.get_by_id(planning_id)
    if not planning_obj or planning_obj.user_id != current_user.id:
        flash("Planning non trouvé", "error")
        return redirect(url_for("planning"))

    # Supprimer le planning de la base de données
    db_manager.execute_delete("DELETE FROM plannings WHERE id = ?", (planning_id,))

    flash("Planning supprimé avec succès", "success")
    return redirect(url_for("planning"))


@app.route("/planning/<int:planning_id>/convert", methods=["POST"])
@login_required
def convert_planning(planning_id):
    planning_obj = Planning.get_by_id(planning_id)
    if not planning_obj or planning_obj.user_id != current_user.id:
        flash("Planning non trouvé", "error")
        return redirect(url_for("planning"))

    # Convertir le planning en feuille d'heures
    feuille = planning_obj.to_feuille_heures()

    # Vérifier si c'était une mise à jour ou une création
    feuille_existante = FeuilleDHeures.get_by_mois_annee_user(
        planning_obj.mois, planning_obj.annee, current_user.id
    )

    if feuille_existante and feuille_existante.id != feuille.id:
        flash("Feuille d'heures mise à jour avec succès !", "success")
    else:
        flash("Feuille d'heures créée avec succès !", "success")

    return redirect(url_for("feuille_heures"))


@app.route("/feuille-heures")
@login_required
def feuille_heures():
    feuilles = FeuilleDHeures.get_by_user(current_user.id)

    # Détail d'une feuille si spécifié
    detail_feuille = None
    detail_id = request.args.get("detail")
    if detail_id:
        try:
            detail_feuille = FeuilleDHeures.get_by_id(int(detail_id))
            if not detail_feuille or detail_feuille.user_id != current_user.id:
                detail_feuille = None
        except (ValueError, TypeError):
            detail_feuille = None

    return render_template(
        "feuille_heures.html", feuilles=feuilles, detail_feuille=detail_feuille
    )


@app.route("/feuille-heures/<int:feuille_id>/delete", methods=["POST"])
@login_required
def delete_feuille_heures(feuille_id):
    feuille = FeuilleDHeures.get_by_id(feuille_id)
    if not feuille or feuille.user_id != current_user.id:
        flash("Feuille d'heures non trouvée", "error")
        return redirect(url_for("feuille_heures"))

    # Supprimer la feuille d'heures de la base de données
    db_manager.execute_delete("DELETE FROM feuilles_heures WHERE id = ?", (feuille_id,))

    flash("Feuille d'heures supprimée avec succès", "success")
    return redirect(url_for("feuille_heures"))


# API endpoints pour l'interface JavaScript
@app.route("/api/planning", methods=["GET", "POST"])
@login_required
@rate_limit(max_requests=100, window_seconds=3600)
def api_planning():

    if request.method == "GET":
        # Récupérer tous les plannings de l'utilisateur
        plannings = Planning.get_by_user(current_user.id)
        return jsonify([p.to_dict() for p in plannings])

    elif request.method == "POST":
        # Créer un nouveau planning
        try:
            data = request.get_json()
            if not data:
                log_security_event(
                    "API_PLANNING_FAILED", "Missing JSON data", current_user.id
                )
                return jsonify({"error": "Données JSON manquantes"}), 400

            # Validation des données
            is_valid, error_message = validator.validate_planning_data(data)
            if not is_valid:
                log_security_event(
                    "API_PLANNING_FAILED",
                    f"Invalid data: {error_message}",
                    current_user.id,
                )
                return jsonify({"error": error_message}), 400

            planning = Planning(
                mois=int(data["mois"]),
                annee=int(data["annee"]),
                jours_travail=data["jours_travail"],
                taux_horaire=float(data["taux_horaire"]),
                user_id=current_user.id,
                heures_contractuelles=float(data.get("heures_contractuelles", 35.0)),
            )
            planning.save()

            log_security_event(
                "API_PLANNING_SUCCESS",
                f"Planning created for {data['mois']}/{data['annee']}",
                current_user.id,
            )
            return jsonify({"success": True, "data": planning.to_dict()}), 201
        except Exception as e:
            log_security_event(
                "API_PLANNING_ERROR",
                f"Planning creation failed: {str(e)}",
                current_user.id,
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Erreur lors de la création du planning",
                    }
                ),
                500,
            )


@app.route("/api/planning/<int:planning_id>", methods=["GET", "PUT", "DELETE"])
@login_required
@rate_limit(max_requests=200, window_seconds=3600)
def api_planning_detail(planning_id):

    planning = Planning.get_by_id(planning_id)
    if not planning or planning.user_id != current_user.id:
        log_security_event(
            "API_PLANNING_UNAUTHORIZED",
            f"Unauthorized access to planning {planning_id}",
            current_user.id,
        )
        return jsonify({"error": "Planning non trouvé"}), 404

    if request.method == "GET":
        return jsonify(planning.to_dict())

    elif request.method == "PUT":
        try:
            data = request.get_json()
            if not data:
                log_security_event(
                    "API_PLANNING_FAILED",
                    "Missing JSON data for update",
                    current_user.id,
                )
                return jsonify({"error": "Données JSON manquantes"}), 400

            # Validation des données
            is_valid, error_message = validator.validate_planning_data(data)
            if not is_valid:
                log_security_event(
                    "API_PLANNING_FAILED",
                    f"Invalid update data: {error_message}",
                    current_user.id,
                )
                return jsonify({"error": error_message}), 400

            planning.mois = int(data["mois"])
            planning.annee = int(data["annee"])
            planning.jours_travail = data["jours_travail"]
            planning.taux_horaire = float(data["taux_horaire"])
            planning.heures_contractuelles = float(
                data.get("heures_contractuelles", 35.0)
            )
            planning.save()

            log_security_event(
                "API_PLANNING_SUCCESS",
                f"Planning {planning_id} updated",
                current_user.id,
            )
            return jsonify({"success": True, "data": planning.to_dict()})
        except Exception as e:
            log_security_event(
                "API_PLANNING_ERROR",
                f"Planning update failed: {str(e)}",
                current_user.id,
            )
            return (
                jsonify({"success": False, "error": "Erreur lors de la mise à jour"}),
                500,
            )

    elif request.method == "DELETE":
        try:
            db_manager.execute_delete(
                "DELETE FROM plannings WHERE id = ?", (planning_id,)
            )
            log_security_event(
                "API_PLANNING_SUCCESS",
                f"Planning {planning_id} deleted",
                current_user.id,
            )
            return jsonify(
                {"success": True, "message": "Planning supprimé avec succès"}
            )
        except Exception as e:
            log_security_event(
                "API_PLANNING_ERROR",
                f"Planning deletion failed: {str(e)}",
                current_user.id,
            )
            return (
                jsonify({"success": False, "error": "Erreur lors de la suppression"}),
                500,
            )


@app.route("/api/planning/<int:planning_id>/convert", methods=["POST"])
@login_required
@rate_limit(max_requests=50, window_seconds=3600)
def api_planning_convert(planning_id):

    planning = Planning.get_by_id(planning_id)
    if not planning or planning.user_id != current_user.id:
        log_security_event(
            "API_CONVERT_UNAUTHORIZED",
            f"Unauthorized access to planning {planning_id}",
            current_user.id,
        )
        return jsonify({"error": "Planning non trouvé"}), 404

    try:
        feuille = planning.to_feuille_heures()
        log_security_event(
            "API_CONVERT_SUCCESS",
            f"Planning {planning_id} converted to feuille",
            current_user.id,
        )
        return jsonify({"success": True, "data": feuille.to_dict()})
    except Exception as e:
        log_security_event(
            "API_CONVERT_ERROR",
            f"Planning conversion failed: {str(e)}",
            current_user.id,
        )
        return jsonify({"success": False, "error": "Erreur lors de la conversion"}), 500


@app.route("/api/feuille-heures", methods=["GET"])
@login_required
@rate_limit(max_requests=200, window_seconds=3600)
def api_feuille_heures():

    feuilles = FeuilleDHeures.get_by_user(current_user.id)
    return jsonify([f.to_dict() for f in feuilles])


@app.route("/api/contracts", methods=["GET"])
@login_required
@rate_limit(max_requests=100, window_seconds=3600)
def api_contracts():
    """Retourne la liste des contrats de travail disponibles"""
    from .salary_calculator import salary_calculator

    contracts = salary_calculator.get_available_contracts()
    return jsonify(contracts)


@app.route("/api/feuille-heures/<int:feuille_id>", methods=["GET", "DELETE"])
@login_required
@rate_limit(max_requests=200, window_seconds=3600)
def api_feuille_heures_detail(feuille_id):

    feuille = FeuilleDHeures.get_by_id(feuille_id)
    if not feuille or feuille.user_id != current_user.id:
        log_security_event(
            "API_FEUILLE_UNAUTHORIZED",
            f"Unauthorized access to feuille {feuille_id}",
            current_user.id,
        )
        return jsonify({"error": "Feuille d'heures non trouvée"}), 404

    if request.method == "GET":
        return jsonify(feuille.to_dict())

    elif request.method == "DELETE":
        try:
            db_manager.execute_delete(
                "DELETE FROM feuilles_heures WHERE id = ?", (feuille_id,)
            )
            log_security_event(
                "API_FEUILLE_SUCCESS", f"Feuille {feuille_id} deleted", current_user.id
            )
            return jsonify(
                {"success": True, "message": "Feuille d'heures supprimée avec succès"}
            )
        except Exception as e:
            log_security_event(
                "API_FEUILLE_ERROR",
                f"Feuille deletion failed: {str(e)}",
                current_user.id,
            )
            return (
                jsonify({"success": False, "error": "Erreur lors de la suppression"}),
                500,
            )


if __name__ == "__main__":
    app.run(debug=True)
