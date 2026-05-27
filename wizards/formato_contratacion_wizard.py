from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64


class FormatoContratacionWizard(models.TransientModel):
    _name        = 'reclutamiento__kuale.formato_contratacion_wizard'
    _description = 'Generar Formato de Contratación GK'

    applicant_id       = fields.Many2one('hr.applicant', required=True)
    formatos_wizard_id = fields.Many2one('reclutamiento__kuale.formatos_wizard')
    formato_base_id    = fields.Many2one(
        'hr.applicant.doc.format',
        string='Formato base',
        domain="[('name', 'ilike', 'Formato de Contratacion')]",
        required=False,
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'formato_base_id' in fields_list and not defaults.get('formato_base_id'):
            fmt = self.env['hr.applicant.doc.format'].search(
                [('name', 'ilike', 'Formato de Contratacion'), ('active', '=', True)],
                limit=1, order='id asc',
            )
            if not fmt:
                fmt = self.env['hr.applicant.doc.format'].with_context(active_test=False).search(
                    [('name', 'ilike', 'Formato de Contratacion')],
                    limit=1, order='id asc',
                )
            if fmt:
                defaults['formato_base_id'] = fmt.id
        return defaults

    def _get_unidad_negocio(self):
        a = self.applicant_id
        if a.requisition_id and a.requisition_id.branch_ids:
            return a.requisition_id.branch_ids.name or ''
        return a.company_id.name if a.company_id else ''

    def action_generate(self):
        """
        Retorna una client action que le dice al JS:
        - La URL para descargar el PDF (generada via controller)
        - A qué wizard regresar después
        El JS abre la descarga con window.open y luego ejecuta
        act_window para abrir el wizard principal — pero ahora
        sin cerrar nada, porque act_window sobre target:'new'
        REEMPLAZA el dialog actual cuando se llama desde JS puro
        sin pasar por doAction del stack.
        """
        self.ensure_one()
        if not self.formato_base_id or not self.formato_base_id.pdf_file:
            raise UserError(_('No se encontró el formato base con archivo PDF.'))

        try:
            from ..services.formato_contratacion_service import generate_formato_contratacion
        except ImportError as e:
            raise UserError(_('No se pudo importar el servicio: %s') % str(e))

        try:
            pdf_bytes = generate_formato_contratacion(
                self.applicant_id,
                company_name=self._get_unidad_negocio(),
                pdf_base_bytes=base64.b64decode(self.formato_base_id.pdf_file),
            )
        except Exception as e:
            raise UserError(_('Error generando el formato: %s') % str(e))

        filename = 'FormatoContratacion_%s.pdf' % (
            self.applicant_id.partner_name or 'candidato'
        ).replace(' ', '_')

        att = self.env['ir.attachment'].sudo().create({
            'name':      filename,
            'type':      'binary',
            'datas':     base64.b64encode(pdf_bytes),
            'res_model': self._name,
            'res_id':    self.id,
            'mimetype':  'application/pdf',
        })

        download_url = f'/web/content/{att.id}?download=true'

        # Pasar el wizard_id del principal para que JS pueda abrirlo
        formatos_wizard_id = self.formatos_wizard_id.id if self.formatos_wizard_id else False

        return {
            'type':   'ir.actions.client',
            'tag':    'kuale_generar_formato_contratacion',
            'params': {
                'download_url':       download_url,
                'formatos_wizard_id': formatos_wizard_id,
            },
        }

    def action_cancel(self):
        self.ensure_one()
        if self.formatos_wizard_id:
            return {
                'type':      'ir.actions.act_window',
                'res_model': 'reclutamiento__kuale.formatos_wizard',
                'view_mode': 'form',
                'res_id':    self.formatos_wizard_id.id,
                'target':    'new',
                'context':   {'dialog_size': 'medium'},
            }
        return {'type': 'ir.actions.act_window_close'}