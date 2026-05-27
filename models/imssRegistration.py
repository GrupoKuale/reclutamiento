from odoo import fields, models, api
# Modelo para Registro Patronal (IMSS)
class IMSSRegistration(models.Model):
    _name = 'reclutamiento__kuale.imss.registration'
    _description = 'Número de registro del IMSS'

    name = fields.Char(string='Nombre', required=True)
    city = fields.Char(string='Ciudad')
    state = fields.Char(string='Estado')
    zip_code = fields.Char(string='Código Postal')
    job = fields.Char(string='Trabajo')
    risk_class = fields.Char(string='Clase de riesgo')
    risk_fraction = fields.Char(string='Fracción de riesgo')
    status = fields.Selection([
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ], string='Estatus', default='Activo', required=True)
