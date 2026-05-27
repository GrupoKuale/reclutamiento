from odoo import models, fields, api
class ApplicantGetRefuseReason(models.TransientModel):
    _inherit = 'applicant.get.refuse.reason'

    def action_refuse_reason_apply(self):
        try:
            res = super(ApplicantGetRefuseReason, self).action_refuse_reason_apply()
            self.applicant_ids.write({'process': 'no_viable'})
        except Exception as e:
            print("Error refuse reason:", e)
