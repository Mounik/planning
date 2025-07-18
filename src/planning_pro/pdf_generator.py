"""
Générateur de PDF pour les feuilles d'heures
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io
from typing import Dict, Any


def format_date_french(date: datetime) -> str:
    """Formate une date en français"""
    jours = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']
    mois = ['', 'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
            'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
    
    jour_semaine = jours[date.weekday()]
    jour = date.day
    mois_nom = mois[date.month]
    annee = date.year
    
    return f"{jour_semaine} {jour} {mois_nom} {annee}"


class PDFGenerator:
    """Générateur de PDF pour les feuilles d'heures"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configure les styles personnalisés"""
        # Style pour le titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black
        ))
        
        # Style pour les sous-titres
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.black
        ))
        
        # Style pour le texte normal
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generer_pdf_feuille(self, feuille_data: Dict[str, Any]) -> io.BytesIO:
        """Génère un PDF pour une feuille d'heures"""
        
        # Créer un buffer en mémoire
        buffer = io.BytesIO()
        
        # Créer le document PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Construire le contenu
        story = []
        
        # Titre principal
        mois_noms = ['', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        
        titre = f"FEUILLE D'HEURES - {mois_noms[feuille_data['mois']]} {feuille_data['annee']}"
        story.append(Paragraph(titre, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Informations du contrat
        story.append(Paragraph("INFORMATIONS DU CONTRAT", self.styles['CustomSubtitle']))
        
        infos_contrat = [
            ['Taux horaire:', f"{feuille_data['taux_horaire']}€/h"],
            ['Heures contractuelles:', f"{feuille_data['heures_contractuelles']}h/semaine"],
            ['Total heures travaillées:', f"{feuille_data['total_heures']}h"],
        ]
        
        table_infos = Table(infos_contrat, colWidths=[80*mm, 50*mm])
        table_infos.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(table_infos)
        story.append(Spacer(1, 20))
        
        # Détail des jours travaillés
        story.append(Paragraph("DÉTAIL DES JOURS TRAVAILLÉS", self.styles['CustomSubtitle']))
        
        # Construire les données du tableau
        data_jours = [['Date', 'Créneaux', 'Heures']]
        
        for jour in feuille_data['jours_travailles']:
            date = datetime.strptime(jour['date'], '%Y-%m-%d')
            date_formatee = format_date_french(date)
            
            creneaux_text = ''
            if jour['creneaux']:
                creneaux_text = '\n'.join([
                    f"{creneau['heure_debut']} - {creneau['heure_fin']}"
                    for creneau in jour['creneaux']
                ])
            
            data_jours.append([
                date_formatee,
                creneaux_text,
                f"{jour['heures']}h"
            ])
        
        table_jours = Table(data_jours, colWidths=[60*mm, 80*mm, 30*mm])
        table_jours.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table_jours)
        story.append(Spacer(1, 20))
        
        # Récapitulatif salarial
        story.append(Paragraph("RÉCAPITULATIF SALARIAL", self.styles['CustomSubtitle']))
        
        calcul = feuille_data['calcul_salaire']
        
        # Tableau des heures
        data_heures = [
            ['Type d\'heures', 'Nombre d\'heures', 'Salaire'],
            ['Heures normales', f"{calcul['heures_normales']}h", f"{calcul['salaire_normal']:.2f}€"],
            ['Heures complémentaires', f"{calcul['heures_complementaires']}h", f"{calcul['salaire_complementaire']:.2f}€"],
            ['Heures complémentaires majorées', f"{calcul['heures_complementaires_majorees']}h", f"{calcul['salaire_complementaire_majore']:.2f}€"],
            ['Heures supplémentaires', f"{calcul.get('total_heures_supplementaires', 0)}h", f"{calcul['salaire_supplementaire']:.2f}€"],
        ]
        
        table_heures = Table(data_heures, colWidths=[80*mm, 40*mm, 40*mm])
        table_heures.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(table_heures)
        story.append(Spacer(1, 10))
        
        # Total brut
        total_text = f"<b>TOTAL BRUT: {calcul['salaire_brut_total']:.2f}€</b>"
        story.append(Paragraph(total_text, self.styles['CustomSubtitle']))
        
        # Calcul du salaire net
        salaire_net = feuille_data['salaire_net']
        
        story.append(Spacer(1, 15))
        story.append(Paragraph("ESTIMATION DU SALAIRE NET", self.styles['CustomSubtitle']))
        
        # Tableau des déductions
        data_deductions = [
            ['Déductions', 'Montant'],
            ['Cotisations sociales', f"-{salaire_net['cotisations_sociales']:.2f}€"],
            ['Impôt sur le revenu', f"-{salaire_net['impot_mensuel']:.2f}€"],
        ]
        
        table_deductions = Table(data_deductions, colWidths=[80*mm, 40*mm])
        table_deductions.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(table_deductions)
        story.append(Spacer(1, 10))
        
        # Total net
        total_net_text = f"<b>TOTAL NET ESTIMÉ: {salaire_net['salaire_net_final']:.2f}€</b>"
        story.append(Paragraph(total_net_text, self.styles['CustomSubtitle']))
        
        # Avertissement
        disclaimer_text = "⚠️ Estimation approximative basée sur les taux 2024 - Consultez votre service paie pour les montants exacts"
        story.append(Paragraph(disclaimer_text, self.styles['CustomNormal']))
        
        story.append(Spacer(1, 30))
        
        # Pied de page
        date_generation = datetime.now().strftime('%d/%m/%Y à %H:%M')
        pied_page = f"Document généré le {date_generation} par le Gestionnaire d'Heures"
        story.append(Paragraph(pied_page, self.styles['CustomNormal']))
        
        # Construire le PDF
        doc.build(story)
        
        # Retourner le buffer
        buffer.seek(0)
        return buffer


# Instance globale
pdf_generator = PDFGenerator()