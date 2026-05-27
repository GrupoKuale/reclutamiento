
from odoo import api, fields, models, exceptions

class EmployeeRequestUniform(models.Model):
    _name = 'reclutamiento__kuale.employee.request.uniform'
    _description = 'Solicitud de uniforme'

    item = fields.Char(string='Prenda', required=True)
    size = fields.Integer(string='Tamaño', required=True)
    uniformRequestReason = fields.Selection([
        ('size change','Cambio de talla'),
        ('lost','Extravío'),
        ('malfunction','Defectuoso'),
        ('pregnancy','Embarazo'),
        ('other','Otro'),
    ],string='Razón de cambio de uniforme', required=True)

    requestId = fields.Many2one('reclutamiento__kuale.employee.request',  string='Solicitud')

    @api.model
    def create(self, vals):
        if 'requestId' in vals:
            related_request = self.env['reclutamiento__kuale.employee.request'].browse(vals['requestId'])
            if related_request.uniformRequestId:
                raise exceptions.ValidationError(
                    'Solo puedes agregar un registro de uniforme por solicitud.'
                )
        return super(EmployeeRequestUniform, self).create(vals)