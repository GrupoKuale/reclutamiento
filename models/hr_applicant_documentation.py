# -*- coding: utf-8 -*-
import logging
import base64
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

DOCS_LIST = [
    ('imss_aviso',            'Aviso de afiliacion al IMSS'),
    ('curp',                  'CURP'),
    ('rfc_constancia',        'Constancia de RFC'),
    ('santander',             'Contrato apertura cuenta Nomina Santander'),
    ('ine',                   'INE'),
    ('acta_nacimiento',       'Acta de nacimiento'),
    ('comprobante_estudios',  'Ultimo comprobante de estudios'),
    ('carta_recomendacion',   'Cartas de recomendacion'),
    ('comprobante_domicilio', 'Comprobante de domicilio'),
]

class HrApplicantDocumentation(models.Model):
    _name        = 'hr.applicant.documentation'
    _description = 'Documentacion de contratacion'
    _order       = 'id asc'

    applicant_id  = fields.Many2one('hr.applicant', required=True, ondelete='cascade', index=True)
    doc_type      = fields.Selection(DOCS_LIST, string='Documento', required=True)
    doc_name      = fields.Char(string='Nombre del archivo')
    doc_data      = fields.Binary(string='Archivo', attachment=True)
    state         = fields.Selection([
        ('pending',   'Pendiente'),
        ('scanned',   'Escaneado'),
        ('confirmed', 'Confirmado'),
    ], default='pending')
    attachment_id = fields.Many2one('ir.attachment', ondelete='set null')
    migrated      = fields.Boolean(default=False)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_remove(self):
        for rec in self:
            if rec.attachment_id:
                rec.attachment_id.sudo().unlink()
            rec.write({
                'doc_data':      False,
                'doc_name':      False,
                'attachment_id': False,
                'state':         'pending',
            })

    def save_scanned_file(self, file_b64, filename):
        """Llamado desde el controller de escaneo."""
        self.ensure_one()
        if self.attachment_id:
            self.attachment_id.sudo().unlink()
        att = self.env['ir.attachment'].create({
            'name':      filename,
            'type':      'binary',
            'datas':     file_b64,
            'res_model': 'hr.applicant',
            'res_id':    self.applicant_id.id,
            'mimetype':  'application/pdf',
        })
        self.write({
            'doc_data':      file_b64,
            'doc_name':      filename,
            'attachment_id': att.id,
            'state':         'scanned',
        })
        return att.id

    # ── Inicialización + migración automática ────────────────────────────────
    @api.model
    def init_docs_for_applicant(self, applicant_id):
        applicant      = self.env['hr.applicant'].browse(applicant_id)
        existing       = self.search([('applicant_id', '=', applicant_id)])
        existing_types = existing.mapped('doc_type')

        for doc_key, _ in DOCS_LIST:
            if doc_key not in existing_types:
                self.create({'applicant_id': applicant_id, 'doc_type': doc_key})

        # ── 1. Migrar campo Binary directo: recommendation_letter ──────────
        if applicant.recommendation_letter:
            doc_rec = self.search([
                ('applicant_id', '=', applicant_id),
                ('doc_type',    '=', 'carta_recomendacion'),
                ('state',       '=', 'pending'),
            ], limit=1)
            if doc_rec:
                doc_rec.write({
                    'doc_data': applicant.recommendation_letter,
                    'doc_name': 'carta_recomendacion.pdf',
                    'state':    'scanned',
                    'migrated': True,
                })
                _logger.info('Migrado recommendation_letter para applicant %s', applicant_id)

        # ── 2. Migrar ir.attachment por field_name guardado en description ──
        field_to_doc = {
            'recommendation_letter': 'carta_recomendacion',
            'nss_files':             'imss_aviso',
            'rfc_files':             'rfc_constancia',
            'driver_files':          'ine',
        }
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id',    '=', applicant_id),
        ])
        for att in attachments:
            doc_type = field_to_doc.get(att.description)
            if not doc_type:
                continue
            doc_rec = self.search([
                ('applicant_id', '=', applicant_id),
                ('doc_type',    '=', doc_type),
                ('state',       '=', 'pending'),
            ], limit=1)
            if doc_rec and att.datas:
                doc_rec.write({
                    'doc_data':      att.datas,
                    'doc_name':      att.name,
                    'attachment_id': att.id,
                    'state':         'scanned',
                    'migrated':      True,
                })
                _logger.info('Migrado adjunto "%s" → "%s" applicant=%s',
                            att.description, doc_type, applicant_id)

        # ── 3. Migrar INE desde reclutamiento__kuale.documents_applicant ──
        identity_docs = self.env['reclutamiento__kuale.documents_applicant'].search([
            ('applicant_id', '=', applicant_id),
        ], limit=1)
        if identity_docs and identity_docs.doc_data:
            doc_rec = self.search([
                ('applicant_id', '=', applicant_id),
                ('doc_type',    '=', 'ine'),
            ], limit=1)  # ← ya no filtra por state='pending'
            if doc_rec and not doc_rec.attachment_id:  # ← solo si no tiene attachment
                att = self.env['ir.attachment'].create({
                    'name':      identity_docs.doc_name or 'INE.pdf',
                    'type':      'binary',
                    'datas':     identity_docs.doc_data,
                    'res_model': 'hr.applicant',
                    'res_id':    applicant_id,
                    'mimetype':  'application/pdf',
                })
                doc_rec.write({
                    'doc_data':      identity_docs.doc_data,
                    'doc_name':      identity_docs.doc_name or 'INE.pdf',
                    'attachment_id': att.id,
                    'state':         'scanned',
                    'migrated':      True,
                })
                _logger.info('Attachment INE creado para applicant %s', applicant_id)

class ScanPageBuffer(models.Model):
    _name        = 'hr.scan.page.buffer'
    _description = 'Buffer temporal de páginas escaneadas'

    doc_id    = fields.Integer(string='Doc ID', index=True)
    page_data = fields.Text(string='PDF base64')
    sequence  = fields.Integer(string='Orden')