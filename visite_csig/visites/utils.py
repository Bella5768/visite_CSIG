import qrcode
import io
import base64
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


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


def envoyer_email_confirmation_rendez_vous(rendez_vous, request):
    """
    Envoie un email de confirmation au demandeur du rendez-vous
    """
    if not rendez_vous.visiteur.email:
        return False
    
    sujet = f"Confirmation de votre rendez-vous - {rendez_vous.sujet}"
    
    context = {
        'rendez_vous': rendez_vous,
        'visiteur': rendez_vous.visiteur,
        'motif': rendez_vous.motif,
        'correspondant': rendez_vous.correspondant,
        'site_url': request.build_absolute_uri('/'),
    }
    
    html_message = render_to_string('rendez_vous/email_confirmation.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            sujet,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [rendez_vous.visiteur.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email de confirmation: {e}")
        return False


def notifier_correspondant_rendez_vous(rendez_vous, request):
    """
    Notifie le correspondant par email lorsqu'un rendez-vous est confirmé
    """
    if not rendez_vous.correspondant or not rendez_vous.correspondant.email:
        return False
    
    sujet = f" Nouveau rendez-vous confirmé - {rendez_vous.sujet}"
    
    context = {
        'rendez_vous': rendez_vous,
        'visiteur': rendez_vous.visiteur,
        'motif': rendez_vous.motif,
        'correspondant': rendez_vous.correspondant,
        'site_url': request.build_absolute_uri('/'),
    }
    
    html_message = render_to_string('rendez_vous/email_notification_correspondant.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            sujet,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [rendez_vous.correspondant.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email au correspondant: {e}")
        return False
