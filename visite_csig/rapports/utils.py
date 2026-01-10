import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def export_rapport_pdf(visites, date, stats):
    """Exporte le rapport journalier en PDF"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1*cm, bottomMargin=1*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # Titre
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=18)
    elements.append(Paragraph(f"Rapport des visites - {date}", title_style))
    elements.append(Spacer(1, 0.5*cm))
    
    # Statistiques
    stats_data = [
        ['Total', 'En cours', 'Terminées', 'Annulées'],
        [str(stats['total']), str(stats['en_cours']), str(stats['terminees']), str(stats['annulees'])]
    ]
    stats_table = Table(stats_data, colWidths=[4*cm]*4)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 1*cm))
    
    # Tableau des visites
    data = [['Visiteur', 'Motif', 'Correspondant', 'Entrée', 'Sortie', 'Durée', 'Statut']]
    for v in visites:
        data.append([
            f"{v.visiteur.prenoms} {v.visiteur.nom}",
            v.motif.libelle,
            str(v.correspondant) if v.correspondant else '-',
            v.heure_entree.strftime('%H:%M'),
            v.heure_sortie.strftime('%H:%M') if v.heure_sortie else '-',
            v.get_duree(),
            v.get_statut_display()
        ])
    
    if len(data) > 1:
        table = Table(data, colWidths=[5*cm, 4*cm, 4*cm, 2*cm, 2*cm, 2*cm, 2.5*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("Aucune visite pour cette date.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
