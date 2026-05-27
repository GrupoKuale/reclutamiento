
from odoo import api, fields, models, exceptions

class EmployeeRequestLaborLetter(models.Model):
    _name = 'reclutamiento__kuale.employee.request.labor_letter'
    _description = 'Solicitud de carta laboral'
    # suggest: change it 4 a selection
    purpose = fields.Char(string='Propósito', required=True)

    requestId = fields.Many2one('reclutamiento__kuale.employee.request',  string='Solicitud')

    @api.model
    def create(self, vals):
        if 'requestId' in vals:
            related_request = self.env['reclutamiento__kuale.employee.request'].browse(vals['requestId'])
            if related_request.labor_letterRequestId:
                raise exceptions.ValidationError(
                    'Solo puedes agregar un registro de carta laboral por solicitud.'
                )
        return super(EmployeeRequestLaborLetter, self).create(vals)


