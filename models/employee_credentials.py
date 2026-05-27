from odoo import api, fields, models, exceptions
from odoo.http import request
import hashlib
import re
import logging
logger = logging.getLogger(__name__)
import random
import string

class EmployeeCredentials(models.Model):
    _inherit = 'hr.employee'

    username = fields.Char(string='Nombre de usuario')
    password = fields.Char(string='Contraseña')

    @api.constrains('username')
    def _check_username(self):
        for record in self:
            if not record.username:
                raise exceptions.ValidationError("El nombre de usuario no puede estar vacío.")
            if self.search([('username', '=', record.username), ('id', '!=', record.id)]):
                raise exceptions.ValidationError("El nombre de usuario ya existe.")

    @api.constrains('password')
    def _check_password(self):
        for record in self:
            if not record.password:
                raise exceptions.ValidationError("La contraseña no puede estar vacía.")
            
    @api.model
    def create(self, vals):
        required_fields = ['name', 'private_email', 'job_title']
        for field in required_fields:
            if field not in vals:
                raise exceptions.ValidationError(f'Falta el campo requerido: {field}')

        if self.sudo().search([('work_email', '=', vals.get("private_email"))], limit=1):
            raise exceptions.ValidationError(f'El correo electrónico ya existe: {vals.get("private_email")}')
        
        logger.info(f'Creating user with email {vals.get("private_email")}')
        logger.info(f'Creating user with password {vals.get("password")}, ')
        logger.info(f'Creating user with username {vals.get("username")}')

        return super(EmployeeCredentials, self).create(vals)
    
    def _validate_password(self,password):
        pattern = r'^(?=.*\d)(?=.*[A-Z])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
        if not re.match(pattern, password):
            raise exceptions.UserError("La contraseña debe tener al menos 8 caracteres, una letra mayúscula, un número y un caracter especial")
        return True

    def _hash_password(self,password):
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def generate_password():
        # Definir los conjuntos de caracteres
        digits = string.digits
        uppercase_letters = string.ascii_uppercase
        special_characters = "!@#$%^&*(),.?\":{}|<>"
        all_characters = string.ascii_letters + digits + special_characters

        password = [
            random.choice(digits),
            random.choice(uppercase_letters),
            random.choice(special_characters),
        ]

        while len(password) < 8:
            password.append(random.choice(all_characters))

        # Mezclar los caracteres para que no sigan un patrón predecible
        random.shuffle(password)

        # Convertir la lista en una cadena
        return ''.join(password)

    def is_valid_email(self, email):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email) is not None

    def write(self, vals):
        print("editando usuario ", vals)
        if 'password' in vals:
            self.env['res.users'].sudo().browse(self.user_id.id).write({'password': vals['password']})
            vals['password'] = self._hash_password(vals.get('password'))
        if 'username' in vals:
            self.env['res.users'].sudo().browse(self.user_id.id).write({'login': vals['username']})
            vals['username'] = vals.get('username')
        return super(EmployeeCredentials, self).write(vals)
    
        
    def open_user_creation_wizard(self):
        """Abre el wizard para asignar credenciales móviles"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asignar Credenciales Móviles',
            'res_model': 'employee.mobile.credentials.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_id': self.id},
        }
    
    def _create_odoo_user(self, username, password, vals):
        user_vals = {
            'name': vals.get('name'),
            'login': username,
            'password': password,
            'company_id': vals.get('company_id', self.env.company.id)
        }
        
        user = self.env['res.users'].sudo().create(user_vals)

        user.partner_id.write({
            'company_id': user.company_id.id,
            'user_id': user.id,  
            'email': vals.get('work_email') 
        })

        return user
