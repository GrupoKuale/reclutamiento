import base64
import logging
import os

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def load_default_formats(cr, registry):
    """
    post_init_hook — se ejecuta automáticamente después del upgrade del módulo.
    Carga los PDFs de la carpeta data/Formatos Documentacion en hr.applicant.doc.format
    y los .docx de contratos de data/Contratos, solo si no existen ya (idempotente).
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    Format = env['hr.applicant.doc.format']

    # ── PDFs ──────────────────────────────────────────────────────────────────
    pdf_folder = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'Formatos Documentacion'
    )

    pdf_files = [
        ('CA',                            'CA.pdf'),
        ('CJr Tampico HM',                'CJr_Tampico (HM).pdf'),
        ('CJr Victoria HM',               'CJr_Victoria (HM).pdf'),
        ('DQ Tampico HM',                 'DQ_Tampico (HM).pdf'),
        ('DQ Victoria HM',                'DQ_Victoria (HM).pdf'),
        ('Hidrologica',                   'Hidrologica.pdf'),
        ('MM HM',                         'MM (HM).pdf'),
        ('PTTS',                          'PTTS.pdf'),
        ('Servicios',                     'Servicios.pdf'),
        ('Formato de Contratacion CJr',   'Formato de Contratacion CJr.pdf'),
        ('Formato de Contratacion DQ',    'Formato de Contratacion DQ.pdf'),
        ('Formato de Contratacion Hidro', 'Formato de Contratacion Hidro.pdf'),
        ('Formato de Contratacion SK',    'Formato de Contratacion SK.pdf'),
        ('Formato de Contratacion Tinto', 'Formato de Contratacion Tinto.pdf'),
        ('Formato de Contratacion GK',    'formato_contratacion_base.pdf'),
    ]

    loaded = []
    skipped = []
    missing = []

    for name, filename in pdf_files:
        path = os.path.join(pdf_folder, filename)
        if not os.path.exists(path):
            missing.append(filename)
            continue
        if Format.search([('name', '=', name)], limit=1):
            skipped.append(name)
            continue
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        Format.create({
            'name':         name,
            'pdf_file':     b64,
            'pdf_filename': filename,
        })
        loaded.append(name)

    # ── DOCX (Contratos de trabajo) ───────────────────────────────────────────
    docx_folder = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'Contratos'
    )

    docx_files = [
        (
            'Contrato Indeterminado Simple',
            '1__Contrato_Trabajo_MODIFICADO_POR_JURIDICO_Indeterminado__simple_.docx',
        ),
        (
            'Contrato Indeterminado con Anexo',
            '1__Contrato_Trabajo_MODIFICADO_POR_JURIDICO_Indeterminado__con_anexo_.docx',
        ),
        (
            'Contrato Determinado Simple',
            '2__Contrato_Trabajo_MODIFICADO_POR_JURIDICO_determinado__simple_.docx',
        ),
        (
            'Contrato Determinado con Anexo',
            '2__Contrato_Trabajo_MODIFICADO_POR_JURIDICO_determinado__con_anexo_.docx',
        ),
    ]

    for name, filename in docx_files:
        path = os.path.join(docx_folder, filename)
        if not os.path.exists(path):
            missing.append(filename)
            continue
        existing = Format.search([('name', '=', name)], limit=1)
        if existing:
            # Actualizar el docx si el registro existe pero no tiene archivo
            if not existing.docx_file:
                with open(path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode()
                existing.write({
                    'docx_file':     b64,
                    'docx_filename': filename,
                })
                loaded.append(name + ' (docx actualizado)')
            else:
                skipped.append(name)
            continue
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        Format.create({
            'name':          name,
            'docx_file':     b64,
            'docx_filename': filename,
        })
        loaded.append(name)

    if loaded:
        _logger.info('Formatos cargados: %s', loaded)
    if skipped:
        _logger.info('Formatos ya existentes (omitidos): %s', skipped)
    if missing:
        _logger.warning('Archivos no encontrados: %s', missing)
        
def post_init_hook(cr, registry):
    load_default_formats(cr, registry)
    ensure_company_xmlids(cr, registry)


def ensure_company_xmlids(cr, registry):
    """
    Asegura que las empresas tengan su xmlid registrado.
    Funciona en instalación nueva, actualización y BD limpia.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    companies = {
        'company_kuale_demo_data': 'Kuale Demo Matriz',
        'company_kuale_demo_branch_data': 'Kuale Demo Sucursal Centro',
    }

    for xmlid, name in companies.items():
        # ¿Ya existe el xmlid?
        ref = env.ref(
            f'reclutamiento__kuale.{xmlid}',
            raise_if_not_found=False
        )
        if ref:
            continue  # ya está registrado, no hacer nada

        # Busca la empresa por nombre
        company = env['res.company'].search([('name', '=', name)], limit=1)
        if not company:
            # No existe, la crea
            company = env['res.company'].create({'name': name})
            _logger.info('Empresa creada: %s', name)

        # Registra el xmlid
        env['ir.model.data'].create({
            'module': 'reclutamiento__kuale',
            'name': xmlid,
            'model': 'res.company',
            'res_id': company.id,
            'noupdate': True,
        })
        _logger.info('xmlid registrado: reclutamiento__kuale.%s → ID %s', xmlid, company.id)