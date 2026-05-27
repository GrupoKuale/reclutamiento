from odoo import models, fields

class ConfirmCheckIdWizard(models.TransientModel):
    _name = 'reclutamiento__kuale.confirm_check_id'
    _description = 'Confirmar verificación Check ID'

    applicant_id = fields.Many2one('hr.applicant', required=True)

    def action_confirm(self):
        self.applicant_id.write({'check_id_verified': True})
        return {'type': 'ir.actions.act_window_close'}