from odoo import api,models,fields

class ZktecoBiometricUser(models.Model):
    _name = 'reclutamiento__kuale.biometric_user'
    _description = 'Usuarios Biométricos'

    device_employee_id = fields.Char(
        string='ID del Dispositivo Biométrico',
        help="El ID del empleado en el dispositivo biométrico",
        required=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        compute='_compute_employee_id',
        store=True,
        help="Empleado asociado basado en el ID del dispositivo"
    )

    biometric_type = fields.Selection([
        ('finger', 'Finger'),
        ('face', 'Face'),
        ('card', 'Card'),
        ('password', 'Password')
    ], string='Tipo de Dato Biométrico', required=True)

    biometric_data = fields.Binary(
        string='Dato Biométrico',
        help="Dato biométrico almacenado, como huella digital o datos faciales"
    )

    @api.depends('device_employee_id')
    def _compute_employee_id(self):
        for record in self:
            employee = self.env['hr.employee'].search(
                [('device_id_num', '=', record.device_employee_id)], limit=1
            )
            record.employee_id = employee.id if employee else False
