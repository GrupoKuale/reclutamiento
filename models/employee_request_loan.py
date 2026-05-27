
from odoo import api, models, fields, exceptions

class EmployeeRequestLoan(models.Model):
    _name = 'reclutamiento__kuale.employee.request.loan'
    _description = 'Solicitud de préstamo'

    amount = fields.Float(string='Monto', required=True)

    requestId = fields.Many2one('reclutamiento__kuale.employee.request',string='Solicitud')


    @api.model
    def create(self, vals):
        if 'requestId' in vals:
            related_request = self.env['reclutamiento__kuale.employee.request'].browse(vals['requestId'])
            if related_request.loanRequestId:
                raise exceptions.ValidationError(
                    'Solo puedes agregar un registro de préstamo por solicitud.'
                )
        return super(EmployeeRequestLoan, self).create(vals)