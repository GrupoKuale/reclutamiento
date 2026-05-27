# -*- coding: utf-8 -*-
"""
Generador de Formato de Contratación – Gente Kuale S.A. de C.V.

Coordenadas calibradas desde formato_contratacion_base.pdf
usando pdfplumber con verificación visual iterativa.

Regla de texto:  escribir en rl_y + 1  (justo encima de la línea)
Regla de X:      escribir en cx - 2.5, rl_y_center - 3.5  (centrado en círculo 12.5pt)
"""
import base64
import io
import os
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

# ── Offset global ─────────────────────────────────────────────────────────────
OFF = 1   # pt encima de la línea


# ─────────────────────────────────────────────────────────────────────────────
def _make_overlay_p1(data, font_size=9):
    """
    Página 1.

    LÍNEAS (x0, rl_y medidos con pdfplumber):
      unidad_negocio     x=313   rl_y=679.3
      fecha_ingreso      x=203   rl_y=654.5
      nombre_completo    x=203   rl_y=635.5
      edad               x=203   rl_y=616.5
      fecha_nacimiento   x=203   rl_y=597.5
      lugar_nacimiento   x=203   rl_y=578.5
      tipo_sangre        x=203   rl_y=559.5
      nss                x=203   rl_y=540.7
      puesto             x=203   rl_y=521.7
      calle              x=203   rl_y=483.7
      tipo_vialidad      x=473   rl_y=483.7
      num_exterior       x=203   rl_y=464.8
      num_interior       x=203   rl_y=445.8
      colonia            x=203   rl_y=426.8
      municipio_estado   x=203   rl_y=407.8
      codigo_postal      x=203   rl_y=389.0
      entre_calles       x=203   rl_y=370.1
      referencias        x=203   rl_y=351.1
      frente_a           x=203   rl_y=332.1
      caracteristicas    x=203   rl_y=313.1
      tel_fijo           x=223   rl_y=256.5
      celular            x=406   rl_y=256.5
      correo             x=203   rl_y=237.7
      nombre_emergencia  x=100   rl_y=139.8
      tel_emergencia     x=318   rl_y=139.8
      parentesco_emerg   x=469   rl_y=139.8
      otro_vacante       x=340   rl_y= 97.4

    CÍRCULOS (cx, rl_y_center verificados con contexto de texto):
      mamá/papá Sí       cx=224.1  rl_y=223.2
      mamá/papá No       cx=262.9  rl_y=223.2
      enfermedad Sí      cx=224.1  rl_y=204.5
      enfermedad No      cx=224.1  rl_y=185.8
      Periódico          cx=360.2  rl_y=120.2
      Amistad            cx=444.0  rl_y=120.2
      Iniciativa propia  cx=556.7  rl_y=120.2
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        raise ImportError("Instala reportlab: pip install reportlab --break-system-packages")

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFillColorRGB(0, 0, 0)
    c.setFont('Helvetica', font_size)

    # ── Encabezado ────────────────────────────────────────────────────────────
    c.drawString(313, 679.3 + OFF, str(data.get('unidad_negocio') or ''))

    # ── Datos personales ──────────────────────────────────────────────────────
    c.drawString(203, 654.5 + OFF, str(data.get('fecha_ingreso')    or ''))
    c.drawString(203, 635.5 + OFF, str(data.get('nombre_completo')  or ''))
    c.drawString(203, 616.5 + OFF, str(data.get('edad')             or ''))
    c.drawString(203, 597.5 + OFF, str(data.get('fecha_nacimiento') or ''))
    c.drawString(203, 578.5 + OFF, str(data.get('lugar_nacimiento') or ''))
    c.drawString(203, 559.5 + OFF, str(data.get('tipo_sangre')      or ''))

    # ── NSS / Puesto ──────────────────────────────────────────────────────────
    c.drawString(203, 540.7 + OFF, str(data.get('nss')   or ''))
    c.drawString(203, 521.7 + OFF, str(data.get('puesto') or ''))

    # ── Domicilio ─────────────────────────────────────────────────────────────
    c.drawString(203, 483.7 + OFF, str(data.get('calle')           or ''))
    c.drawString(473, 483.7 + OFF, str(data.get('tipo_vialidad')   or ''))
    c.drawString(203, 464.8 + OFF, str(data.get('num_exterior')    or ''))
    c.drawString(203, 445.8 + OFF, str(data.get('num_interior')    or ''))
    c.drawString(203, 426.8 + OFF, str(data.get('colonia')         or ''))
    c.drawString(203, 407.8 + OFF, str(data.get('municipio_estado') or ''))
    c.drawString(203, 389.0 + OFF, str(data.get('codigo_postal')   or ''))
    c.drawString(203, 370.1 + OFF, str(data.get('entre_calles')    or ''))
    c.drawString(203, 351.1 + OFF, str(data.get('referencias')     or ''))
    c.drawString(203, 332.1 + OFF, str(data.get('frente_a')        or ''))
    c.drawString(203, 313.1 + OFF, str(data.get('caracteristicas') or ''))

    # ── Contacto ──────────────────────────────────────────────────────────────
    c.drawString(223, 256.5 + OFF, str(data.get('tel_fijo') or ''))
    c.drawString(406, 256.5 + OFF, str(data.get('celular')  or ''))
    c.drawString(203, 237.7 + OFF, str(data.get('correo')   or ''))

    # ── Contacto de emergencia ────────────────────────────────────────────────
    c.drawString(100, 139.8 + OFF, str(data.get('nombre_emergencia')     or ''))
    c.drawString(318, 139.8 + OFF, str(data.get('telefono_emergencia')   or ''))
    c.drawString(469, 139.8 + OFF, str(data.get('parentesco_emergencia') or ''))

    # ── Soy mamá / papá ───────────────────────────────────────────────────────
    # Sí: cx=224.1 rl_y=223.2 | No: cx=262.9 rl_y=223.2
    c.setFont('Helvetica-Bold', 8)
    if data.get('is_parent') == 'yes':
        c.drawString(224.1 - 2.5, 223.2 - 3.5, 'X')
    else:
        c.drawString(262.9 - 2.5, 223.2 - 3.5, 'X')

    # ── ¿Padeces de alguna enfermedad crónica? ────────────────────────────────
    # Sí: cx=224.1 rl_y=204.5 | No: cx=224.1 rl_y=185.8
    if data.get('has_chronic_disease') == 'yes':
        c.drawString(224.1 - 2.5, 204.5 - 3.5, 'X')
        c.setFont('Helvetica', font_size)
        if data.get('chronic_disease'):
            c.drawString(285, 199.7 + OFF, str(data['chronic_disease']))
    else:
        c.drawString(224.1 - 2.5, 185.8 - 3.5, 'X')

    # ── ¿Cómo te enteraste de la oferta laboral? ──────────────────────────────
    # Periódico: cx=360.2 | Amistad: cx=444.0 | Iniciativa: cx=556.7 | rl_y=120.2
    # Valores del campo about_vacancy (actualizado en modelo):
    # periodico=Periódico, friendship=Amistad, initiative=Iniciativa propia, other=Otro
    vacancy_coords = {
        'periodico':  (360.2, 120.2),   # Periódico
        'friendship': (444.0, 120.2),   # Amistad
        'initiative': (556.7, 120.2),   # Iniciativa propia
    }
    # Etiquetas legibles para escribir en línea Otro
    vacancy_labels = {
        'networking': 'Redes sociales',
        'other':      data.get('other_reason') or 'Otro',
    }
    vacancy = str(data.get('about_vacancy') or '').lower().strip()
    c.setFont('Helvetica-Bold', 8)
    if vacancy in vacancy_coords:
        vx, vy = vacancy_coords[vacancy]
        c.drawString(vx - 2.5, vy - 3.5, 'X')
    else:
        c.setFont('Helvetica', font_size)
        other_text = vacancy_labels.get(vacancy) or str(data.get('other_reason') or vacancy)
        if other_text:
            c.drawString(340, 97.4 + OFF, other_text)

    c.save()
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────────────────────
def _make_overlay_p2(data, font_size=9):
    """
    Página 2.

    LÍNEAS (x0, rl_y medidos con pdfplumber):
      no_cuenta          x=149   rl_y=576.2
      nombre_p2          x=149   rl_y=557.2
      curp               x=149   rl_y=538.2
      calle_p2           x=149   rl_y=519.2
      numero_p2          x=149   rl_y=500.2
      colonia_p2         x=149   rl_y=481.2
      cp_p2              x=149   rl_y=462.2
      tel_fijo_p2        x=149   rl_y=443.2
      celular_p2         x=149   rl_y=424.2
      fecha_nac_p2       x=202   rl_y=405.2
      sexo               x=149   rl_y=386.2
      puesto_p2          x=149   rl_y=367.2
      nombre_beneficiario x=181  rl_y=278.5
      parentesco         x=181   rl_y=259.5
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        raise ImportError("Instala reportlab: pip install reportlab --break-system-packages")

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont('Helvetica', font_size)
    c.setFillColorRGB(0, 0, 0)

    c.drawString(149, 576.2 + OFF, str(data.get('no_cuenta')           or ''))
    c.drawString(149, 557.2 + OFF, str(data.get('nombre_p2')           or ''))
    c.drawString(149, 538.2 + OFF, str(data.get('curp')                or ''))
    c.drawString(149, 519.2 + OFF, str(data.get('calle_p2')            or ''))
    c.drawString(149, 500.2 + OFF, str(data.get('numero_p2')           or ''))
    c.drawString(149, 481.2 + OFF, str(data.get('colonia_p2')          or ''))
    c.drawString(149, 462.2 + OFF, str(data.get('cp_p2')               or ''))
    c.drawString(149, 443.2 + OFF, str(data.get('tel_fijo_p2')         or ''))
    c.drawString(149, 424.2 + OFF, str(data.get('celular_p2')          or ''))
    c.drawString(202, 405.2 + OFF, str(data.get('fecha_nac_p2')        or ''))
    c.drawString(149, 386.2 + OFF, str(data.get('sexo')                or ''))
    c.drawString(149, 367.2 + OFF, str(data.get('puesto_p2')           or ''))
    c.drawString(181, 278.5 + OFF, str(data.get('nombre_beneficiario') or ''))
    c.drawString(181, 259.5 + OFF, str(data.get('parentesco')          or ''))

    c.save()
    buf.seek(0)
    return buf


# ─────────────────────────────────────────────────────────────────────────────
def _get_lugar_nacimiento(applicant):
    a = applicant
    ciudad = ''
    estado = ''
    if a.birthplace_select:
        try:
            ciudad = (a.birthplace_select.municipality
                      or a.birthplace_select.state
                      or a.birthplace_select.name)
        except Exception:
            ciudad = a.birthplace_select.name or ''
    if a.state_birth_Select:
        try:
            estado = a.state_birth_Select.state or a.state_birth_Select.name
        except Exception:
            estado = a.state_birth_Select.name or ''
    return ', '.join(filter(None, [ciudad, estado]))


# ─────────────────────────────────────────────────────────────────────────────
def generate_formato_contratacion(applicant, company_name=None, pdf_base_bytes=None):
    """Genera el PDF de formato de contratación. Retorna bytes del PDF."""
    try:
        from pypdf import PdfWriter, PdfReader
    except ImportError:
        raise ImportError("Instala pypdf: pip install pypdf --break-system-packages")

    if not pdf_base_bytes:
        module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pdf_base = os.path.join(
            module_path, 'static', 'src', 'pdf', 'formato_contratacion_base.pdf'
        )
        if not os.path.exists(pdf_base):
            raise FileNotFoundError("PDF base no encontrado en: %s" % pdf_base)
        with open(pdf_base, 'rb') as f:
            pdf_base_bytes = f.read()

    a = applicant

    # ── Nombre completo ───────────────────────────────────────────────────────
    full_name = ' '.join(filter(None, [
        a.partner_name or '',
        a.last_name    or '',
        a.last_name2   or '',
    ])).strip()

    # ── Fecha de nacimiento ───────────────────────────────────────────────────
    birthdate_str = ''
    if a.birthdate:
        try:
            birthdate_str = a.birthdate.strftime('%d/%m/%Y')
        except Exception:
            birthdate_str = str(a.birthdate)

    # ── Auxiliares ────────────────────────────────────────────────────────────
    lugar_nac = _get_lugar_nacimiento(a)

    gender_map = {'male': 'Masculino', 'female': 'Femenino', 'non_binary': 'No binario'}
    sexo = gender_map.get(a.gender, '')

    municipio_estado = ', '.join(filter(None, [a.municipality or '', a.state or '']))

    beneficiario  = a.beneficiaries_ids[:1]
    nombre_benef  = beneficiario.beneficiary_name if beneficiario else ''
    parentesco_b  = dict(
        beneficiario._fields['beneficiary_relationship'].selection
    ).get(beneficiario.beneficiary_relationship, '') if beneficiario else ''

    banco     = a.bank_account_ids[:1]
    no_cuenta = banco.account_number if banco else ''

    tipo_vialidad = ''
    if a.type_road:
        tipo_vialidad = dict(a._fields['type_road'].selection).get(a.type_road, '')

    calles_entre = ', '.join(filter(None, [
        a.between_streets or '',
        a.between_street2 or '',
    ]))

    blood_map = {
        'a_p': 'A+', 'a_n': 'A-', 'b_p': 'B+',  'b_n': 'B-',
        'ab_p': 'AB+', 'ab_n': 'AB-', 'o_p': 'O+', 'o_n': 'O-',
    }
    tipo_sangre = blood_map.get(a.blood_type or '', '')

    emergencia            = a.emergency_contacts[:1] if a.emergency_contacts else None
    nombre_emergencia     = emergencia.name         if emergencia else ''
    telefono_emergencia   = emergencia.phone_number if emergencia else ''
    parentesco_emergencia = dict(
        emergencia._fields['relationship'].selection
    ).get(emergencia.relationship, '') if emergencia else ''

    is_parent = 'yes' if a.children else 'no'

    # ── Página 1 ──────────────────────────────────────────────────────────────
    datos_p1 = {
        'unidad_negocio':    company_name or (a.company_id.name if a.company_id else ''),
        'fecha_ingreso':     datetime.today().strftime('%d/%m/%Y'),
        'nombre_completo':   full_name,
        'edad':              str(a.age) if a.age else '',
        'fecha_nacimiento':  birthdate_str,
        'lugar_nacimiento':  lugar_nac,
        'tipo_sangre':       tipo_sangre,
        'nss':               a.social_security_number or '',
        'puesto':            a.job_id.name if a.job_id else '',
        'calle':             a.current_address or '',
        'tipo_vialidad':     tipo_vialidad,
        'num_exterior':      a.exterior_number or '',
        'num_interior':      a.interior_number or '',
        'colonia':           a.colony or '',
        'municipio_estado':  municipio_estado,
        'codigo_postal':     a.postal_code or '',
        'entre_calles':      calles_entre,
        'referencias':       a.additional_ref or '',
        'frente_a':          '',
        'caracteristicas':   a.address_details or '',
        'tel_fijo':          a.desk_phone or '',
        'celular':           a.partner_mobile or a.partner_phone or '',
        'correo':            a.email_from or '',
        'is_parent':         is_parent,
        'has_chronic_disease': a.has_chronic_disease or 'no',
        'chronic_disease':   a.chronic_disease or '',
        'nombre_emergencia':     nombre_emergencia,
        'telefono_emergencia':   telefono_emergencia,
        'parentesco_emergencia': parentesco_emergencia,
        'about_vacancy':     a.about_vacancy or '',
        'other_reason':      a.other_reason or '',
    }

    # ── Página 2 ──────────────────────────────────────────────────────────────
    datos_p2 = {
        'no_cuenta':           no_cuenta,
        'nombre_p2':           full_name,
        'curp':                a.curp or '',
        'calle_p2':            a.current_address or '',
        'numero_p2':           a.exterior_number or '',
        'colonia_p2':          a.colony or '',
        'cp_p2':               a.postal_code or '',
        'tel_fijo_p2':         a.desk_phone or '',
        'celular_p2':          a.partner_mobile or a.partner_phone or '',
        'fecha_nac_p2':        birthdate_str,
        'sexo':                sexo,
        'puesto_p2':           a.job_id.name if a.job_id else '',
        'nombre_beneficiario': nombre_benef,
        'parentesco':          parentesco_b,
    }

    # ── Generar y fusionar ────────────────────────────────────────────────────
    overlay_p1 = _make_overlay_p1(datos_p1)
    overlay_p2 = _make_overlay_p2(datos_p2)

    reader_base = PdfReader(io.BytesIO(pdf_base_bytes))
    reader_ov1  = PdfReader(overlay_p1)
    reader_ov2  = PdfReader(overlay_p2)

    writer = PdfWriter()
    page1 = reader_base.pages[0]
    page1.merge_page(reader_ov1.pages[0])
    writer.add_page(page1)

    page2 = reader_base.pages[1]
    page2.merge_page(reader_ov2.pages[0])
    writer.add_page(page2)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)

    _logger.info('Formato contratacion generado para applicant %s', applicant.id)
    return output.read()


def generate_formato_b64(applicant, company_name=None):
    """Retorna el PDF como string base64."""
    pdf_bytes = generate_formato_contratacion(applicant, company_name)
    return base64.b64encode(pdf_bytes).decode('ascii')