from odoo import fields, models, api
#Modelo  para Tipo de Sucursal
class BranchType(models.Model):
    _name = 'reclutamiento__kuale.branch.type'
    _description = 'Tipos de sucursales'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripcion')
    status = fields.Selection([
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ], string='Estatus', default='Active', required=True)
