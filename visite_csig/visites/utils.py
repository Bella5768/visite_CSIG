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


def _get_images_dir():
    """Retourne le dossier images en cherchant dans STATICFILES_DIRS puis STATIC_ROOT"""
    import os
    # D'abord chercher dans les dossiers de fichiers statiques (dev)
    for static_dir in settings.STATICFILES_DIRS:
        images_path = os.path.join(str(static_dir), 'images')
        if os.path.isdir(images_path):
            return images_path
    # Sinon dans STATIC_ROOT (production)
    if settings.STATIC_ROOT:
        images_path = os.path.join(str(settings.STATIC_ROOT), 'images')
        if os.path.isdir(images_path):
            return images_path
    return None


def generer_preuve_pdf(rendez_vous):
    """Génère un PDF de preuve de rendez-vous"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # En-tête
    p.setFont("Helvetica-Bold", 18)
    p.drawCentredString(width/2, height - 2*cm, "PREUVE DE RENDEZ-VOUS")
    
    p.setFont("Helvetica", 11)
    p.drawCentredString(width/2, height - 2.8*cm, "Cabinet du Ministre — MENA-ETFP")
    p.drawCentredString(width/2, height - 3.4*cm, "République de Guinée")
    
    # Ligne séparatrice
    p.setStrokeColorRGB(0.11, 0.31, 0.85)
    p.setLineWidth(2)
    p.line(2*cm, height - 4*cm, width - 2*cm, height - 4*cm)
    
    # Détails du rendez-vous
    y = height - 5.5*cm
    p.setFont("Helvetica-Bold", 13)
    p.drawString(2.5*cm, y, "Détails du rendez-vous")
    
    y -= 1*cm
    p.setFont("Helvetica", 11)
    details = [
        ("Sujet", rendez_vous.sujet),
        ("Date", rendez_vous.date_rendez_vous.strftime('%d/%m/%Y')),
        ("Heure", f"{rendez_vous.heure_debut.strftime('%H:%M')} - {rendez_vous.heure_fin.strftime('%H:%M') if rendez_vous.heure_fin else ''}"),
        ("Motif", rendez_vous.motif.libelle if rendez_vous.motif else '-'),
        ("Statut", "Confirmé"),
    ]
    
    for label, value in details:
        p.setFont("Helvetica-Bold", 10)
        p.drawString(3*cm, y, f"{label}:")
        p.setFont("Helvetica", 10)
        p.drawString(7*cm, y, str(value))
        y -= 0.7*cm
    
    # Informations du visiteur
    y -= 1*cm
    p.setFont("Helvetica-Bold", 13)
    p.drawString(2.5*cm, y, "Informations du demandeur")
    
    y -= 1*cm
    visiteur_details = [
        ("Nom", f"{rendez_vous.visiteur.prenoms} {rendez_vous.visiteur.nom}"),
        ("Téléphone", rendez_vous.visiteur.telephone or '-'),
        ("Email", rendez_vous.visiteur.email or '-'),
    ]
    
    if rendez_vous.correspondant:
        visiteur_details.append(("Correspondant", f"{rendez_vous.correspondant.prenoms} {rendez_vous.correspondant.nom}"))
    
    for label, value in visiteur_details:
        p.setFont("Helvetica-Bold", 10)
        p.drawString(3*cm, y, f"{label}:")
        p.setFont("Helvetica", 10)
        p.drawString(7*cm, y, str(value))
        y -= 0.7*cm
    
    # Note en bas
    y -= 1.5*cm
    p.setFont("Helvetica-Bold", 10)
    p.drawString(2.5*cm, y, "Veuillez présenter ce document et une pièce d'identité à l'accueil.")
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, 2*cm, "Ministère de l'Éducation Nationale, de l'Alphabétisation,")
    p.drawCentredString(width/2, 1.5*cm, "de l'Enseignement Technique et de la Formation Professionnelle")
    p.drawCentredString(width/2, 1*cm, "Document généré automatiquement — Ne pas modifier")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


def envoyer_email_confirmation_rendez_vous(rendez_vous, request):
    """
    Envoie un email de confirmation au demandeur du rendez-vous
    avec les logos attachés en inline (CID) et le PDF de preuve en pièce jointe.
    """
    if not rendez_vous.visiteur.email:
        print(f"[EMAIL] Pas d'email pour le visiteur {rendez_vous.visiteur}")
        return False
    
    import os
    from email.mime.image import MIMEImage
    from django.core.mail import EmailMultiAlternatives
    from django.core import signing
    from django.urls import reverse

    sujet = f"Confirmation de votre rendez-vous - {rendez_vous.sujet}"

    preuve_token = signing.dumps({'rdv_id': rendez_vous.pk}, salt='rendez_vous_public_preuve')
    preuve_url = request.build_absolute_uri(
        reverse('rendez_vous_public_preuve', kwargs={'token': preuve_token})
    )

    context = {
        'rendez_vous': rendez_vous,
        'visiteur': rendez_vous.visiteur,
        'motif': rendez_vous.motif,
        'correspondant': rendez_vous.correspondant,
        'site_url': request.build_absolute_uri('/'),
        'preuve_url': preuve_url,
    }
    
    html_message = render_to_string('rendez_vous/email_confirmation.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        email = EmailMultiAlternatives(
            subject=sujet,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[rendez_vous.visiteur.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.mixed_subtype = 'related'

        # Attacher les logos en inline
        images_dir = _get_images_dir()
        if images_dir:
            logo_files = [
                ('logo_mena', 'mena-etfp.png', 'image/png'),
                ('logo_branding', 'branding.webp', 'image/webp'),
                ('logo_simandou', 'simandou.jpeg', 'image/jpeg'),
            ]
            for cid, filename, mimetype in logo_files:
                filepath = os.path.join(images_dir, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        maintype, subtype = mimetype.split('/')
                        img = MIMEImage(f.read(), _subtype=subtype)
                        img.add_header('Content-ID', f'<{cid}>')
                        img.add_header('Content-Disposition', 'inline', filename=filename)
                        email.attach(img)
                else:
                    print(f"[EMAIL] Logo non trouvé: {filepath}")
        else:
            print(f"[EMAIL] Dossier images non trouvé")

        # Générer et attacher le PDF de preuve
        try:
            pdf_buffer = generer_preuve_pdf(rendez_vous)
            nom_pdf = f"preuve_rdv_{rendez_vous.visiteur.nom}_{rendez_vous.date_rendez_vous.strftime('%Y%m%d')}.pdf"
            email.attach(nom_pdf, pdf_buffer.getvalue(), 'application/pdf')
            print(f"[EMAIL] PDF de preuve attaché: {nom_pdf}")
        except Exception as e:
            print(f"[EMAIL] Erreur génération PDF: {e}")

        email.send(fail_silently=False)
        print(f"[EMAIL] ✅ Email de confirmation envoyé à: {rendez_vous.visiteur.email}")
        return True
    except Exception as e:
        print(f"[EMAIL] ❌ Erreur lors de l'envoi: {e}")
        import traceback
        traceback.print_exc()
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


def notifier_visiteur_modification_rendez_vous(rendez_vous, request, changes=None):
    """
    Notifie le visiteur par email lorsqu'un rendez-vous est modifié.
    """
    if not rendez_vous.visiteur.email:
        return False

    sujet = f"Modification de votre rendez-vous - {rendez_vous.sujet}"

    context = {
        'rendez_vous': rendez_vous,
        'visiteur': rendez_vous.visiteur,
        'motif': rendez_vous.motif,
        'correspondant': rendez_vous.correspondant,
        'site_url': request.build_absolute_uri('/'),
        'changes': changes or [],
    }

    html_message = render_to_string('rendez_vous/email_modification.html', context)
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
        print(f"Erreur lors de l'envoi de l'email de modification: {e}")
        return False
