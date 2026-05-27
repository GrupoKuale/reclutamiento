from odoo import models, fields, api

class JobPreviewWizard(models.TransientModel):
    _name = 'reclutamiento__kuale.job_preview_wizard'
    _inherit = 'base.document.layout'
    _description = 'Vista previa del puesto'

    job_id = fields.Many2one('hr.job', string='Puesto', required=True)
    preview = fields.Html(compute='_compute_preview', sanitize=False, strip_style=False)

    def _compute_preview(self):
        for wizard in self:
            if wizard.job_id:
                url = '/report/job/preview/%s' % wizard.job_id.id
                wizard.preview = (
                    '<iframe src="' + url + '" '
                    'style="width:100%; height:60vh; border:none; display:block;">'
                    '</iframe>'
                )
            else:
                wizard.preview = False

    def document_layout_save(self):
        return self.env.ref(
            'reclutamiento__kuale.job_specifications_pdf'
        ).sudo().report_action(self.job_id.sudo())