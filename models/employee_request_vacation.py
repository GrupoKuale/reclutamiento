
from odoo import api, fields, models, exceptions

class EmployeeRequestVacation(models.Model):
    _name = 'reclutamiento__kuale.employee.request.vacation'
    _description = 'Solictud de vacaciones'

    startDate = fields.Date(string='Fecha de inicio', required=True)
    endDate = fields.Date(string='Fecha de finalización', required=True)

    requestId = fields.Many2one('reclutamiento__kuale.employee.request',  string='Solicitud')

    @api.model
    def create(self, vals):
        if 'requestId' in vals:
            related_request = self.env['reclutamiento__kuale.employee.request'].browse(vals['requestId'])
            if related_request.vacationRequestId:
                raise exceptions.ValidationError(
                    'Solo puedes agregar un registro de vacaciones por solicitud.'
                )
        return super(EmployeeRequestVacation, self).create(vals)
