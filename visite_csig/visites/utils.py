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
    """Génère un PDF de preuve de rendez-vous avec un design institutionnel."""
    import os
    import json
    from reportlab.lib.colors import HexColor, Color
    from reportlab.lib.utils import ImageReader

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Palette
    PRIMARY = HexColor('#104480')      # Bleu institutionnel
    ACCENT = HexColor('#fbbf24')       # Or accent
    SUCCESS = HexColor('#16a34a')
    TEXT_DARK = HexColor('#1e293b')
    TEXT_MUTED = HexColor('#64748b')
    BG_LIGHT = HexColor('#f8fafc')
    BORDER = HexColor('#e2e8f0')

    # ============== BANDEAU HEADER ==============
    header_h = 4.2 * cm
    p.setFillColor(PRIMARY)
    p.rect(0, height - header_h, width, header_h, stroke=0, fill=1)

    # Bande accent dorée sous le header
    p.setFillColor(ACCENT)
    p.rect(0, height - header_h - 0.15 * cm, width, 0.15 * cm, stroke=0, fill=1)

    # Logo MENA-ETFP à gauche
    images_dir = _get_images_dir()
    if images_dir:
        logo_path = os.path.join(images_dir, 'mena-etfp-transparent.png')
        if not os.path.exists(logo_path):
            logo_path = os.path.join(images_dir, 'mena-etfp.png')
        if os.path.exists(logo_path):
            try:
                p.drawImage(
                    ImageReader(logo_path),
                    1.5 * cm, height - header_h + 0.6 * cm,
                    width=3 * cm, height=3 * cm,
                    preserveAspectRatio=True, mask='auto',
                )
            except Exception:
                pass

    # Texte header (centré, à droite du logo)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(5.2 * cm, height - 1.5 * cm, "RÉPUBLIQUE DE GUINÉE")
    p.setFont("Helvetica", 9)
    p.drawString(5.2 * cm, height - 2.0 * cm, "Travail — Justice — Solidarité")

    p.setFont("Helvetica-Bold", 9.5)
    p.drawString(5.2 * cm, height - 2.7 * cm, "Ministère de l'Éducation Nationale,")
    p.drawString(5.2 * cm, height - 3.15 * cm, "de l'Alphabétisation, de l'Enseignement Technique")
    p.drawString(5.2 * cm, height - 3.6 * cm, "et de la Formation Professionnelle")

    # ============== TITRE PRINCIPAL ==============
    title_y = height - header_h - 1.3 * cm
    p.setFillColor(PRIMARY)
    p.setFont("Helvetica-Bold", 22)
    p.drawCentredString(width / 2, title_y, "PREUVE DE RENDEZ-VOUS")

    p.setFillColor(TEXT_MUTED)
    p.setFont("Helvetica-Oblique", 10)
    p.drawCentredString(width / 2, title_y - 0.6 * cm, "Cabinet du Ministre")

    # Référence du document
    ref_y = title_y - 1.5 * cm
    p.setFillColor(TEXT_DARK)
    p.setFont("Helvetica-Bold", 9)
    ref = f"Référence : RDV-{rendez_vous.pk:06d}"
    p.drawString(2 * cm, ref_y, ref)
    from django.utils import timezone as _tz
    date_emission = _tz.now().strftime('%d/%m/%Y à %H:%M')
    p.setFont("Helvetica", 9)
    p.setFillColor(TEXT_MUTED)
    p.drawRightString(width - 2 * cm, ref_y, f"Émis le {date_emission}")

    # Badge statut "CONFIRMÉ"
    badge_x = width / 2 - 2.2 * cm
    badge_y = ref_y - 1.2 * cm
    p.setFillColor(SUCCESS)
    p.roundRect(badge_x, badge_y, 4.4 * cm, 0.85 * cm, 0.42 * cm, stroke=0, fill=1)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(width / 2, badge_y + 0.27 * cm, "✓  CONFIRMÉ")

    # ============== CARTE DÉTAILS RDV ==============
    card_top = badge_y - 0.8 * cm
    card_h = 5.8 * cm
    card_y = card_top - card_h
    card_x = 2 * cm
    card_w = width - 4 * cm

    p.setFillColor(BG_LIGHT)
    p.setStrokeColor(BORDER)
    p.setLineWidth(0.6)
    p.roundRect(card_x, card_y, card_w, card_h, 0.25 * cm, stroke=1, fill=1)

    # Bande titre de la carte
    p.setFillColor(PRIMARY)
    p.roundRect(card_x, card_top - 0.9 * cm, card_w, 0.9 * cm, 0.25 * cm, stroke=0, fill=1)
    p.rect(card_x, card_top - 0.9 * cm, card_w, 0.45 * cm, stroke=0, fill=1)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(card_x + 0.5 * cm, card_top - 0.6 * cm, "DÉTAILS DU RENDEZ-VOUS")

    # Contenu de la carte
    def _draw_kv(x, y, label, value, label_w=4.5):
        p.setFillColor(TEXT_MUTED)
        p.setFont("Helvetica", 9)
        p.drawString(x, y, label.upper())
        p.setFillColor(TEXT_DARK)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(x, y - 0.55 * cm, str(value))

    col1_x = card_x + 0.7 * cm
    col2_x = card_x + card_w / 2 + 0.3 * cm
    row1_y = card_top - 1.7 * cm
    row2_y = row1_y - 1.6 * cm
    row3_y = row2_y - 1.6 * cm

    heure_str = f"{rendez_vous.heure_debut.strftime('%H:%M')} - {rendez_vous.heure_fin.strftime('%H:%M')}" \
        if rendez_vous.heure_fin else rendez_vous.heure_debut.strftime('%H:%M')

    _draw_kv(col1_x, row1_y, "Sujet", rendez_vous.sujet or '-')
    _draw_kv(col2_x, row1_y, "Motif", rendez_vous.motif.libelle if rendez_vous.motif else '-')

    _draw_kv(col1_x, row2_y, "Date", rendez_vous.date_rendez_vous.strftime('%A %d %B %Y').capitalize()
             if hasattr(rendez_vous.date_rendez_vous, 'strftime') else str(rendez_vous.date_rendez_vous))
    _draw_kv(col2_x, row2_y, "Heure", heure_str)

    if rendez_vous.correspondant:
        corr = f"{rendez_vous.correspondant.prenoms} {rendez_vous.correspondant.nom}"
        _draw_kv(col1_x, row3_y, "Correspondant", corr)

    # ============== CARTE DEMANDEUR ==============
    card2_top = card_y - 0.6 * cm
    card2_h = 4.2 * cm
    card2_y = card2_top - card2_h

    p.setFillColor(BG_LIGHT)
    p.setStrokeColor(BORDER)
    p.roundRect(card_x, card2_y, card_w, card2_h, 0.25 * cm, stroke=1, fill=1)

    p.setFillColor(PRIMARY)
    p.roundRect(card_x, card2_top - 0.9 * cm, card_w, 0.9 * cm, 0.25 * cm, stroke=0, fill=1)
    p.rect(card_x, card2_top - 0.9 * cm, card_w, 0.45 * cm, stroke=0, fill=1)
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(card_x + 0.5 * cm, card2_top - 0.6 * cm, "INFORMATIONS DU DEMANDEUR")

    v = rendez_vous.visiteur
    nom_complet = f"{v.prenoms} {v.nom}"
    r1 = card2_top - 1.7 * cm
    r2 = r1 - 1.5 * cm

    _draw_kv(col1_x, r1, "Nom complet", nom_complet)
    _draw_kv(col2_x, r1, "Téléphone", v.telephone or '-')
    _draw_kv(col1_x, r2, "Email", v.email or '-')
    if getattr(v, 'numero_identite', None):
        _draw_kv(col2_x, r2, "Pièce d'identité", v.numero_identite)

    # ============== QR CODE ==============
    qr_data = json.dumps({
        'type': 'preuve_rdv',
        'rdv_id': rendez_vous.pk,
        'nom': v.nom,
        'date': str(rendez_vous.date_rendez_vous),
    }, ensure_ascii=False)

    qr = qrcode.QRCode(version=1, box_size=4, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#104480", back_color="white")
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    qr_size = 3.2 * cm
    qr_x = width - 2 * cm - qr_size
    qr_y = card2_y - qr_size - 1.2 * cm

    # Cadre autour du QR
    p.setStrokeColor(BORDER)
    p.setFillColorRGB(1, 1, 1)
    p.roundRect(qr_x - 0.2 * cm, qr_y - 0.2 * cm, qr_size + 0.4 * cm, qr_size + 0.4 * cm,
                0.15 * cm, stroke=1, fill=1)
    p.drawImage(ImageReader(qr_buf), qr_x, qr_y, width=qr_size, height=qr_size)

    p.setFillColor(TEXT_MUTED)
    p.setFont("Helvetica", 7.5)
    p.drawCentredString(qr_x + qr_size / 2, qr_y - 0.5 * cm, "Scannez pour vérifier")

    # Encadré "Instructions" à gauche du QR
    inst_x = 2 * cm
    inst_y = qr_y + qr_size + 0.4 * cm
    inst_w = qr_x - inst_x - 0.6 * cm
    inst_h = qr_size + 0.4 * cm

    p.setFillColor(HexColor('#fef3c7'))
    p.setStrokeColor(ACCENT)
    p.setLineWidth(0.8)
    p.roundRect(inst_x, inst_y - inst_h, inst_w, inst_h, 0.2 * cm, stroke=1, fill=1)

    p.setFillColor(HexColor('#92400e'))
    p.setFont("Helvetica-Bold", 9.5)
    p.drawString(inst_x + 0.4 * cm, inst_y - 0.6 * cm, "⚠  INSTRUCTIONS IMPORTANTES")

    instructions = [
        "• Présentez ce document à l'accueil le jour du rendez-vous.",
        "• Munissez-vous d'une pièce d'identité valide.",
        "• Arrivez 10 minutes avant l'heure prévue.",
        "• Ce document est strictement personnel.",
    ]
    p.setFillColor(HexColor('#78350f'))
    p.setFont("Helvetica", 8.5)
    yi = inst_y - 1.15 * cm
    for line in instructions:
        p.drawString(inst_x + 0.4 * cm, yi, line)
        yi -= 0.5 * cm

    # ============== FOOTER ==============
    footer_h = 1.6 * cm
    p.setFillColor(PRIMARY)
    p.rect(0, 0, width, footer_h, stroke=0, fill=1)
    p.setFillColor(ACCENT)
    p.rect(0, footer_h, width, 0.1 * cm, stroke=0, fill=1)

    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 8.5)
    p.drawCentredString(width / 2, footer_h - 0.5 * cm,
                        "Cabinet du Ministre — MENA-ETFP — République de Guinée")
    p.setFont("Helvetica-Oblique", 7.5)
    p.drawCentredString(width / 2, footer_h - 0.95 * cm,
                        "Document généré automatiquement — Toute modification rend ce document nul.")
    p.setFont("Helvetica", 7)
    p.drawCentredString(width / 2, footer_h - 1.3 * cm,
                        f"Document n° RDV-{rendez_vous.pk:06d}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer


def envoyer_email_emailjs(template_params, service_id=None, template_id=None):
    """
    Envoie un email via l'API REST EmailJS (https://www.emailjs.com/).

    template_params: dict des variables du template EmailJS
    (ex: to_email, to_name, sujet, date, heure, motif, preuve_url...).

    Retourne True si l'envoi a réussi, False sinon.
    """
    import json
    import urllib.request
    import urllib.error

    if not getattr(settings, 'USE_EMAILJS', False):
        print("[EMAILJS] EmailJS non configuré (identifiants manquants)")
        return False

    payload = {
        'service_id': service_id or settings.EMAILJS_SERVICE_ID,
        'template_id': template_id or settings.EMAILJS_TEMPLATE_ID,
        'user_id': settings.EMAILJS_PUBLIC_KEY,
        'template_params': template_params,
    }
    # La clé privée est requise pour les appels API côté serveur
    # (activer "Allow EmailJS API for non-browser applications" dans
    # Account > Security du dashboard EmailJS).
    if getattr(settings, 'EMAILJS_PRIVATE_KEY', ''):
        payload['accessToken'] = settings.EMAILJS_PRIVATE_KEY

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.emailjs.com/api/v1.0/email/send',
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode('utf-8', errors='replace')
            print(f"[EMAILJS] Réponse: {resp.status} {body}")
            return resp.status == 200
    except urllib.error.HTTPError as e:
        print(f"[EMAILJS] ❌ Erreur HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}")
        return False
    except Exception as e:
        print(f"[EMAILJS] ❌ Erreur: {e}")
        return False


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
    destinataire = rendez_vous.visiteur.email

    print(f"[EMAIL] Préparation de l'envoi à: {destinataire}")
    print(f"[EMAIL] Sujet: {sujet}")

    preuve_token = signing.dumps({'rdv_id': rendez_vous.pk}, salt='rendez_vous_public_preuve')
    preuve_url = request.build_absolute_uri(
        reverse('rendez_vous_public_preuve', kwargs={'token': preuve_token})
    )

    # --- Envoi via EmailJS (prioritaire si configuré) ---------------------
    if getattr(settings, 'USE_EMAILJS', False):
        heure_str = rendez_vous.heure_debut.strftime('%H:%M')
        if rendez_vous.heure_fin:
            heure_str += f" - {rendez_vous.heure_fin.strftime('%H:%M')}"
        template_params = {
            'to_email': destinataire,
            'to_name': f"{rendez_vous.visiteur.prenoms} {rendez_vous.visiteur.nom}",
            'sujet': rendez_vous.sujet,
            'motif': rendez_vous.motif.libelle if rendez_vous.motif else '-',
            'date_rdv': rendez_vous.date_rendez_vous.strftime('%d/%m/%Y'),
            'heure_rdv': heure_str,
            'correspondant': str(rendez_vous.correspondant) if rendez_vous.correspondant else '-',
            'preuve_url': preuve_url,
            'reference': f"RDV-{rendez_vous.pk:06d}",
        }
        if envoyer_email_emailjs(template_params):
            print(f"[EMAILJS] ✅ Email de confirmation envoyé à: {destinataire}")
            return True
        print("[EMAILJS] ⚠️ Échec EmailJS, tentative via SMTP...")

    # --- Envoi via SMTP (fallback) ----------------------------------------
    print(f"[EMAIL] Configuration SMTP: {settings.EMAIL_HOST}:{settings.EMAIL_PORT} (TLS={settings.EMAIL_USE_TLS})")

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
            to=[destinataire],
        )
        email.attach_alternative(html_message, "text/html")
        email.mixed_subtype = 'related'

        # Options SMTP supplémentaires pour contourner les restrictions
        email.extra_headers = {
            'X-Priority': '1',
            'X-MSMail-Priority': 'High',
        }

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

        print(f"[EMAIL] Envoi en cours...")
        email.send(fail_silently=False)
        print(f"[EMAIL] ✅ Email de confirmation envoyé avec succès à: {destinataire}")
        return True
    except Exception as e:
        print(f"[EMAIL] ❌ Erreur lors de l'envoi à {destinataire}: {e}")
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
