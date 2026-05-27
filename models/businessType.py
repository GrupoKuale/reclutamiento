from odoo import models, fields, api
# Modelo para Tipo de Giro
class BusinessType(models.Model):
    _name = 'reclutamiento__kuale.business.type'
    _description = 'Tipos de giros'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripcion')
    status = fields.Selection([
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ], string='Estatus', default='Activo', required=True)
