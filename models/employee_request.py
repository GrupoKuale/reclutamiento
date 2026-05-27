
from odoo import api, models, fields, exceptions
import datetime


class EmployeeRequest(models.Model):
    _name = 'reclutamiento__kuale.employee.request'
    _description = 'Solicitud de empleado'
    _order = 'create_date desc'

    folio = fields.Char(string='Folio',readonly=True, copy=False)
    requestType = fields.Selection([
        ('work', 'Trabajo'),
        ('loan', 'Préstamo'),
        ('labor_letter', 'Carta Laboral'),
        ('uniform', 'Uniforme'),
        ('vacation', 'Vacaciones'),
        ('expenses', 'Viáticos'),
    ], string="Categoría", required=True)

    status = fields.Selection([
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('cancelled', 'Cancelado'),
        ('closed', 'Cerrado'),
    ], string="Estado", default='pending')

    workRequestId = fields.One2many('reclutamiento__kuale.employee.request.work','requestId' ,string='Solicitud de Trabajo')
    loanRequestId = fields.One2many('reclutamiento__kuale.employee.request.loan','requestId', string='Solicitud de Préstamo')
    labor_letterRequestId = fields.One2many('reclutamiento__kuale.employee.request.labor_letter','requestId', string='Solicitud de Carta Laboral')
    uniformRequestId = fields.One2many('reclutamiento__kuale.employee.request.uniform','requestId', string='Solicitud de Uniforme')
    vacationRequestId = fields.One2many('reclutamiento__kuale.employee.request.vacation','requestId', string='Solicitud de Vacaciones')
    expensesRequestId = fields.One2many('reclutamiento__kuale.employee.request.expenses', 'requestId', string='Solicitud de Viáticos')

    requestDescription = fields.Text(string='Descripción de la solicitud', required=True)

    requestedBy = fields.Many2one('res.users', string='Solicita', default=lambda self: self.env.user)

    _sql_constraints = [
        ('unique_request_per_user', 'unique(requested_by, request_type, status)',
         'Cada usuario solo puede tener una solicitud pendiente de cada tipo.')
    ]

    def _check_exclusive_request(self):
        for record in self:
            request_ids = [
                record.workRequestId.id,
                record.loanRequestId.id,
                record.labor_letterRequestId.id,
                record.uniformRequestId.id,
                record.vacationRequestId.id,
                record.expensesRequestId.id
            ]
            non_empty_ids = [req_id for req_id in request_ids if req_id]
            if len(non_empty_ids) > 1:
                raise exceptions.ValidationError(
                    'Solo puedes tener una solicitud activa a la vez.'
                )

    def _generate_folio(self, request_type):
        request_type_code = {
            'work': 'WRK',
            'loan': 'LOA',
            'labor_letter': 'LBL',
            'uniform': 'UNI',
            'vacation': 'VAC',
            'expenses': 'EXP'
        }.get(request_type, 'XXX')

        year_code = datetime.date.today().strftime('%Y')

        param_name = f'employee_request_folio_{request_type}_{year_code}'
        counter = int(self.env['ir.config_parameter'].get_param(param_name, default='0'))

        counter += 1

        self.env['ir.config_parameter'].set_param(param_name, str(counter))

        return f'kuale-{year_code}-{request_type_code}-{counter:04d}' 
#merge ready

    def _send_request_email(self, record):
        # We can change the default group in order to filter new roles
        user_group = self.env.ref('base.group_user')

        users = self.env['res.users'].search([
            ('groups_id', 'in', user_group.id),
            ('active', '=', True),
        ])
        template = self.env.ref('reclutamiento__kuale.email_template_employee_request')
        for user in users:
            template.sudo().send_mail(record.id, email_values={'email_to': user.email}, force_send=True)

    @api.model
    def create(self, vals):
        if 'requestType' in vals:
            request_type = vals.get('requestType')
            existing_request = self.search([
                ('requestedBy', '=', vals.get('requestedBy')),
                ('status', '=', 'pending'),
                ('requestType', '=', request_type)
            ])
            if existing_request:
                raise exceptions.ValidationError(
                    'Ya tienes una solicitud pendiente de este tipo.'
                )
        vals['folio'] = self._generate_folio(vals.get('requestType'))
        record = super(EmployeeRequest, self).create(vals)
        record._check_exclusive_request()
        self._send_request_email(record)
        return record

    def write(self, vals):
        res = super(EmployeeRequest, self).write(vals)
        self._check_exclusive_request()
        return res
