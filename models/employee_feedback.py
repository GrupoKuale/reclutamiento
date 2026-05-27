from odoo import api, models, fields
from odoo.exceptions import ValidationError
import datetime


class EmployeeFeedback(models.Model):
    _name = 'reclutamiento__kuale.employee.feedback'
    _description = 'Comentarios de los empleados'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    folio = fields.Char(string='Folio',readonly=True, copy=False)
    feedbackType = fields.Selection([
        ('complaint', 'Queja'),
        ('suggestion', 'Suegerencia'),
    ], string='Tipo de comentario', required=True)
    feedback = fields.Text(string='Comentario', required=True)
    subject = fields.Selection([
        ('work', 'Trabajo'),
        ('staff', 'Personal'),
        ('services', 'Servicios'),
        ('technology', 'Tecnología'),
        ('customer', 'Cliente'),

    ], string='Tema', required=True)

    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('examination', 'En examinación'),
        ('solved', 'Resuelto'),
    ], string='Estado', required=True, default='pending')

    feedbackBy = fields.Many2one('hr.employee', string='Reportado por')

    """def _generate_folio(self, feedback_type):
        feedback_type_code = {
            'complaint': 'com',
            'suggestion': 'sug',
        }.get(feedback_type, 'XXX')
        today = datetime.date.today()
        date_code = today.strftime('%d%m%y')

        return f'kuale-{feedback_type_code}-{date_code}'"""
    
    def _generate_folio(self, feedback_type):
        # Mapeo de códigos para tipos de retroalimentación
        feedback_type_code = {
            'complaint': 'COM',
            'suggestion': 'SUG',
        }.get(feedback_type, 'XXX')

        # Nombre del parámetro para mantener el contador
        param_name = f'feedback_folio_{feedback_type}'

        # Obtener el contador actual desde los parámetros del sistema
        counter = int(self.env['ir.config_parameter'].get_param(param_name, default='0'))

        # Incrementar el contador
        counter += 1

        # Guardar el nuevo contador en los parámetros del sistema
        self.env['ir.config_parameter'].set_param(param_name, str(counter))

    # Formatear el folio
        return f'kuale-{feedback_type_code}-{counter:04d}'  # Número incremental con 4 dígitos


    @api.constrains('status')
    def _check_status_sequence(self):
        status_order = {
            'pending': 0,
            'examination': 1,
            'solved': 2,
        }
        for record in self:
            if record.status and record._origin.status:
                if status_order[record.status] < status_order[record._origin.status]:
                    raise ValidationError("No puedes retroceder a un estado anterior")

    @api.model
    def create(self, vals):
        if not vals.get('feedbackBy'):
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            if not employee:
                raise ValidationError("No se encontró un registro de empleado para el usuario actual.")
            vals['feedbackBy'] = employee.id
        if not vals.get('folio'):
            vals['folio']=self._generate_folio(vals['feedbackType'])
        if vals.get('feedbackBy'):
            vals['feedbackBy'] = vals.get('feedbackBy')
        else:
            raise ValidationError("No se encontró un registro de empleado para el usuario actual.")
        record = super(EmployeeFeedback, self).create(vals)
        return record

    def write(self, vals):
        if 'status' in vals:
            status_order = {
                'pending': 0,
                'examination': 1,
                'solved': 2,
            }
            for record in self:
                if record.status and record._origin.status:
                    if status_order[vals['status']] < status_order[record._origin.status]:
                        raise ValidationError("No puedes retroceder a un estado anterior")
        return super(EmployeeFeedback, self).write(vals)

    def message_post(self, **kwargs):
        for record in self:
            if record.status == 'solved':
                raise ValidationError("No puedes enviar mensajes a un reporte resuelto")
        return super(EmployeeFeedback, self).message_post(**kwargs)
