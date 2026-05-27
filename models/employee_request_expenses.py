
from odoo import api, fields, models, exceptions

class EmployeeRequestExpenses(models.Model):
    _name = 'reclutamiento__kuale.employee.request.expenses'
    _description = 'Solicitud de gastos'

    startDate = fields.Date(string='Fecha de inicio',required=True)
    endDate = fields.Date(string='Fecha de finalización',required=True)
    destiny = fields.Char(string='Destino',required=True)

    requestId = fields.Many2one('reclutamiento__kuale.employee.request',  string='Solicitud')

    @api.model
    def create(self, vals):
        if 'requestId' in vals:
            related_request = self.env['reclutamiento__kuale.employee.request'].browse(vals['requestId'])
            if related_request.expensesRequestId:
                raise exceptions.ValidationError(
                    'Solo puedes agregar un registro de gastos por solicitud.'
                )
        return super(EmployeeRequestExpenses, self).create(vals)
