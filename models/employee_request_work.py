from odoo import api, models, fields, exceptions


class EmployeeRequestWork(models.Model):
    _name = 'reclutamiento__kuale.employee.request.work'
    _description = 'Solicitud de trabajo'

    type = fields.Selection([
        ('rest_day', 'Día de descanso'),
        ('shift_change', 'Cambio de turno'),
        ('overtime', 'Horas extras'),
    ], string='Tipo', required=True)

    requestId = fields.Many2one('reclutamiento__kuale.employee.request',  string='Solicitud')

    @api.model
    def create(self, vals):
        if 'requestId' in vals:
            related_request = self.env['reclutamiento__kuale.employee.request'].browse(vals['requestId'])
            if related_request.workRequestId:
                raise exceptions.ValidationError(
                    'Solo puedes agregar un registro de trabajo por solicitud.'
                )
        return super(EmployeeRequestWork, self).create(vals)
