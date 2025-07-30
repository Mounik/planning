"""
Générateur de PDF pour les feuilles d'heures
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus.tableofcontents import SimpleIndex
from reportlab.lib.enums import TA_CENTER
from datetime import datetime, timedelta
import io
from typing import Dict, Any, List, Tuple


def format_date_french(date_str: str) -> str:
    """Formate une date en français à partir d'une string ISO (YYYY-MM-DD)"""
    jours = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    mois = [
        "",
        "janvier",
        "février",
        "mars",
        "avril",
        "mai",
        "juin",
        "juillet",
        "août",
        "septembre",
        "octobre",
        "novembre",
        "décembre",
    ]

    # Parser la date ISO sans problème de timezone
    parts = date_str.split('-')
    annee = int(parts[0])
    mois_num = int(parts[1])
    jour_num = int(parts[2])

    # Créer l'objet date correctement
    date = datetime(annee, mois_num, jour_num)

    jour_semaine = jours[date.weekday()]
    mois_nom = mois[mois_num]

    return f"{jour_semaine} {jour_num} {mois_nom} {annee}"


def calculer_heures_par_semaine(jours_travailles: List[Dict[str, Any]]) -> List[Tuple[str, float]]:
    """Calcule les heures travaillées par semaine"""
    semaines = {}

    for jour in jours_travailles:
        # Parser la date
        parts = jour["date"].split('-')
        date_obj = datetime(int(parts[0]), int(parts[1]), int(parts[2]))

        # Trouver le début de la semaine (lundi)
        debut_semaine = date_obj - timedelta(days=date_obj.weekday())
        fin_semaine = debut_semaine + timedelta(days=6)

        # Clé de la semaine
        cle_semaine = debut_semaine.strftime("%Y-%m-%d")

        # Initialiser la semaine si pas encore présente
        if cle_semaine not in semaines:
            semaines[cle_semaine] = {
                'debut': debut_semaine,
                'fin': fin_semaine,
                'heures': 0
            }

        # Ajouter les heures de ce jour
        semaines[cle_semaine]['heures'] += jour.get('heures', 0)

    # Convertir en liste triée par date
    result = []
    for cle_semaine in sorted(semaines.keys()):
        semaine = semaines[cle_semaine]

        # Formater les dates avec gestion du changement de mois/année
        if semaine['debut'].month == semaine['fin'].month:
            # Même mois
            debut_str = semaine['debut'].strftime("%d")
            fin_str = semaine['fin'].strftime("%d/%m")
            label = f"Semaine du {debut_str} au {fin_str}"
        else:
            # Mois différents
            debut_str = semaine['debut'].strftime("%d/%m")
            fin_str = semaine['fin'].strftime("%d/%m")
            label = f"Semaine du {debut_str} au {fin_str}"

        # Ajouter l'année si on change d'année
        if semaine['debut'].year != semaine['fin'].year:
            debut_str = semaine['debut'].strftime("%d/%m/%Y")
            fin_str = semaine['fin'].strftime("%d/%m/%Y")
            label = f"Semaine du {debut_str} au {fin_str}"

        result.append((label, semaine['heures']))

    return result


class PDFGenerator:
    """Générateur de PDF pour les feuilles d'heures"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Configure les styles personnalisés"""
        # Style pour le titre principal
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.black,
            )
        )

        # Style pour les sous-titres
        self.styles.add(
            ParagraphStyle(
                name="CustomSubtitle",
                parent=self.styles["Heading2"],
                fontSize=12,
                spaceAfter=12,
                textColor=colors.black,
            )
        )

        # Style pour le texte normal
        self.styles.add(
            ParagraphStyle(
                name="CustomNormal",
                parent=self.styles["Normal"],
                fontSize=10,
                spaceAfter=6,
            )
        )

    def _valider_donnees_feuille(self, feuille_data: Dict[str, Any]) -> None:
        """Valide les données de la feuille d'heures"""
        champs_requis = ['mois', 'annee', 'taux_horaire', 'heures_contractuelles',
                        'total_heures', 'jours_travailles', 'calcul_salaire', 'salaire_net']

        for champ in champs_requis:
            if champ not in feuille_data:
                raise ValueError(f"Champ manquant dans les données: {champ}")

        if not isinstance(feuille_data['jours_travailles'], list):
            raise ValueError("Les jours travaillés doivent être une liste")

        if len(feuille_data['jours_travailles']) == 0:
            raise ValueError("Aucun jour travaillé trouvé")

    def generer_pdf_feuille(self, feuille_data: Dict[str, Any]) -> io.BytesIO:
        """Génère un PDF pour une feuille d'heures avec gestion d'erreurs et pagination"""

        try:
            # Valider les données d'entrée
            self._valider_donnees_feuille(feuille_data)

            # Créer un buffer en mémoire
            buffer = io.BytesIO()

            # Créer le document PDF avec gestion avancée de la pagination
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=20 * mm,
                leftMargin=20 * mm,
                topMargin=20 * mm,
                bottomMargin=25 * mm,  # Plus d'espace en bas pour éviter les coupures
                allowSplitting=1,      # Permet la division des éléments entre pages
                showBoundary=0         # Ne pas afficher les bordures de debug
            )

            # Construire le contenu
            story = []

            # Titre principal
            mois_noms = [
                "",
                "Janvier",
                "Février",
                "Mars",
                "Avril",
                "Mai",
                "Juin",
                "Juillet",
                "Août",
                "Septembre",
                "Octobre",
                "Novembre",
                "Décembre",
            ]

            titre = f"FEUILLE D'HEURES - {mois_noms[feuille_data['mois']]} {feuille_data['annee']}"
            story.append(Paragraph(titre, self.styles["CustomTitle"]))
            story.append(Spacer(1, 20))

            # Informations du contrat
            story.append(
                Paragraph("INFORMATIONS DU CONTRAT", self.styles["CustomSubtitle"])
            )

            infos_contrat = [
                ["Taux horaire:", f"{feuille_data['taux_horaire']}€/h"],
                [
                    "Heures contractuelles:",
                    f"{feuille_data['heures_contractuelles']}h/semaine",
                ],
                ["Total heures travaillées:", f"{round(feuille_data['total_heures'], 4)}h"],
            ]

            table_infos = Table(infos_contrat, colWidths=[80 * mm, 50 * mm])
            table_infos.setStyle(
                TableStyle(
                    [
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )

            story.append(table_infos)
            story.append(Spacer(1, 20))

            # Détail des jours travaillés avec pagination
            story.append(
                Paragraph("DÉTAIL DES JOURS TRAVAILLÉS", self.styles["CustomSubtitle"])
            )

            # Diviser les jours en groupes pour éviter les tableaux trop longs
            jours_par_page = 15  # Maximum de jours par page
            jours_travailles = feuille_data["jours_travailles"]

            for i in range(0, len(jours_travailles), jours_par_page):
                # Construire les données du tableau pour ce groupe
                data_jours = [["Date", "Créneaux", "Heures"]]

                groupe_jours = jours_travailles[i:i + jours_par_page]

                for jour in groupe_jours:
                    date_formatee = format_date_french(jour["date"])

                    creneaux_text = ""
                    if jour["creneaux"]:
                        creneaux_text = "\n".join(
                            [
                                f"{creneau['heure_debut']} - {creneau['heure_fin']}"
                                for creneau in jour["creneaux"]
                            ]
                        )

                    data_jours.append([date_formatee, creneaux_text, f"{round(jour['heures'], 4)}h"])

                table_jours = Table(data_jours, colWidths=[60 * mm, 80 * mm, 30 * mm])
                table_jours.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("GRID", (0, 0), (-1, -1), 1, colors.black),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    )
                )

                story.append(table_jours)

                # Ajouter une nouvelle page si ce n'est pas le dernier groupe
                if i + jours_par_page < len(jours_travailles):
                    story.append(PageBreak())
                    story.append(
                        Paragraph("DÉTAIL DES JOURS TRAVAILLÉS (suite)", self.styles["CustomSubtitle"])
                    )
                else:
                    story.append(Spacer(1, 20))

            # Récapitulatif hebdomadaire
            story.append(Paragraph("RÉCAPITULATIF HEBDOMADAIRE", self.styles["CustomSubtitle"]))

            # Calculer les heures par semaine
            semaines_heures = calculer_heures_par_semaine(feuille_data["jours_travailles"])

            # Créer le tableau des semaines
            data_semaines = [["Période", "Heures travaillées"]]
            for semaine_label, heures in semaines_heures:
                data_semaines.append([semaine_label, f"{round(heures, 4)}h"])

            table_semaines = Table(data_semaines, colWidths=[100 * mm, 40 * mm])
            table_semaines.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )

            story.append(table_semaines)
            story.append(Spacer(1, 20))

            # Récapitulatif salarial
            story.append(Paragraph("RÉCAPITULATIF SALARIAL", self.styles["CustomSubtitle"]))

            calcul = feuille_data["calcul_salaire"]

            # Calculer le total des heures
            total_heures = (
                calcul['heures_normales'] +
                calcul['heures_complementaires'] +
                calcul['heures_complementaires_majorees'] +
                calcul.get('total_heures_supplementaires', 0)
            )

            # Tableau des heures
            data_heures = [
                ["Type d'heures", "Nombre d'heures", "Salaire"],
                [
                    "Heures normales",
                    f"{round(calcul['heures_normales'], 4)}h",
                    f"{calcul['salaire_normal']:.2f}€",
                ],
                [
                    "Heures complémentaires",
                    f"{round(calcul['heures_complementaires'], 4)}h",
                    f"{calcul['salaire_complementaire']:.2f}€",
                ],
                [
                    "Heures complémentaires majorées",
                    f"{round(calcul['heures_complementaires_majorees'], 4)}h",
                    f"{calcul['salaire_complementaire_majore']:.2f}€",
                ],
                [
                    "Heures supplémentaires",
                    f"{round(calcul.get('total_heures_supplementaires', 0), 4)}h",
                    f"{calcul['salaire_supplementaire']:.2f}€",
                ],
                # Ligne de séparation et total
                ["", "", ""],
                [
                    "TOTAL HEURES",
                    f"{round(total_heures, 4)}h",
                    f"{calcul['salaire_brut_total']:.2f}€",
                ],
            ]

            table_heures = Table(data_heures, colWidths=[80 * mm, 40 * mm, 40 * mm])
            table_heures.setStyle(
                TableStyle(
                    [
                        # En-tête
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

                        # Corps du tableau
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -2), 1, colors.black),

                        # Ligne de séparation (avant-dernière ligne)
                        ("LINEBELOW", (0, -3), (-1, -3), 2, colors.black),
                        ("GRID", (0, -2), (-1, -2), 0, colors.white),  # Pas de grille pour la ligne vide

                        # Ligne de total (dernière ligne)
                        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, -1), (-1, -1), 11),
                        ("GRID", (0, -1), (-1, -1), 1, colors.black),
                    ]
                )
            )

            story.append(table_heures)
            story.append(Spacer(1, 10))

            # Total brut
            total_text = f"<b>TOTAL BRUT: {calcul['salaire_brut_total']:.2f}€</b>"
            story.append(Paragraph(total_text, self.styles["CustomSubtitle"]))

            # Calcul du salaire net
            salaire_net = feuille_data["salaire_net"]

            story.append(Spacer(1, 15))
            story.append(
                Paragraph("ESTIMATION DU SALAIRE NET", self.styles["CustomSubtitle"])
            )

            # Tableau des déductions
            data_deductions = [
                ["Déductions", "Montant"],
                ["Cotisations sociales", f"-{salaire_net['cotisations_sociales']:.2f}€"],
                ["Impôt sur le revenu", f"-{salaire_net['impot_mensuel']:.2f}€"],
            ]

            table_deductions = Table(data_deductions, colWidths=[80 * mm, 40 * mm])
            table_deductions.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            story.append(table_deductions)
            story.append(Spacer(1, 10))

            # Total net
            total_net_text = (
                f"<b>TOTAL NET ESTIMÉ: {salaire_net['salaire_net_final']:.2f}€</b>"
            )
            story.append(Paragraph(total_net_text, self.styles["CustomSubtitle"]))

            # Avertissement
            disclaimer_text = "⚠️ Estimation approximative basée sur les taux 2024 - Consultez votre service paie pour les montants exacts"
            story.append(Paragraph(disclaimer_text, self.styles["CustomNormal"]))

            story.append(Spacer(1, 30))

            # Pied de page
            date_generation = datetime.now().strftime("%d/%m/%Y à %H:%M")
            pied_page = f"Document généré le {date_generation} par le Gestionnaire d'Heures"
            story.append(Paragraph(pied_page, self.styles["CustomNormal"]))

            # Construire le PDF avec gestion d'erreurs
            try:
                doc.build(story)
            except Exception as e:
                raise Exception(f"Erreur lors de la construction du PDF: {str(e)}")

            # Retourner le buffer
            buffer.seek(0)
            return buffer

        except Exception as e:
            # Log l'erreur et relancer avec un message plus informatif
            error_msg = f"Erreur lors de la génération du PDF: {str(e)}"
            print(f"[PDF_GENERATOR] {error_msg}")
            raise Exception(error_msg)


# Instance globale
pdf_generator = PDFGenerator()