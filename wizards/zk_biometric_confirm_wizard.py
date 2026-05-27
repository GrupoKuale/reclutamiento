from odoo import models, fields


class ZkBiometricConfirmWizard(models.TransientModel):
    _name        = 'zk.biometric.confirm.wizard'
    _description = 'Confirmación de huella'

    applicant_id = fields.Many2one('hr.applicant')

    def action_confirm(self):
        applicant = self.env['hr.applicant'].browse(
            self.env.context.get('active_id')
        )
        if applicant:
            applicant.write({'huellas_verified': True})

        return {
            'type': 'ir.actions.client',
            'tag':  'reload',
        }