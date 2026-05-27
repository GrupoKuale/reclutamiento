from odoo import models, fields, api, exceptions
import logging
logger = logging.getLogger(__name__)

class EmployeeMobileCredentialsWizard(models.TransientModel):
    _name = 'employee.mobile.credentials.wizard'
    _description = 'Wizard para Asignar Credenciales de Aplicación Móvil'

    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True)
    username = fields.Char("Nombre de Usuario", required=True)
    password = fields.Char("Contraseña", required=True)

    def assign_mobile_credentials(self):
        if self.employee_id.user_id:
            raise exceptions.UserError("Este empleado ya tiene un usuario de Odoo asignado.")

        if self.env['hr.employee'].sudo().search([('username', '=', self.username)], limit=1):
            raise exceptions.ValidationError("El nombre de usuario ya existe.")
        logger.info(f'Creating user with password {self.password}, ')
        
        self.employee_id._validate_password(self.password)
        user = self.employee_id._create_odoo_user(self.username, self.password, {
            'name': self.employee_id.name,
            'company_id': self.employee_id.company_id.id,
            'work_email': self.employee_id.work_email
        })
        self.employee_id.user_id = user
        self.employee_id.username = self.username
        self.employee_id.password = self.password

