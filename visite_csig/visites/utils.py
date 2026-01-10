import qrcode
import io
import base64
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def generate_qrcode_base64(data):
    """Génère un QR code et retourne en base64"""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()


def generate_badge_pdf(visiteur, visite=None):
    """Génère un badge visiteur en PDF"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=(9*cm, 6*cm))
    
    # En-tête
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(4.5*cm, 5.2*cm, "BADGE VISITEUR")
    
    # Nom du visiteur
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(4.5*cm, 4.2*cm, f"{visiteur.prenoms} {visiteur.nom}")
    
    # Infos visite
    if visite:
        p.setFont("Helvetica", 10)
        p.drawCentredString(4.5*cm, 3.5*cm, f"Motif: {visite.motif.libelle}")
        p.drawCentredString(4.5*cm, 3*cm, f"Date: {visite.date_visite}")
        p.drawCentredString(4.5*cm, 2.5*cm, f"Entrée: {visite.heure_entree.strftime('%H:%M')}")
    
    # QR Code (petit)
    import json
    qr_data = json.dumps({'type': 'visiteur_csig', 'id': visiteur.id, 'nom': visiteur.nom, 'prenoms': visiteur.prenoms})
    qr = qrcode.QRCode(version=1, box_size=3, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    from reportlab.lib.utils import ImageReader
    p.drawImage(ImageReader(qr_buffer), 3*cm, 0.3*cm, width=3*cm, height=3*cm)
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer
