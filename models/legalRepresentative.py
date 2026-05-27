from odoo import models, fields, api


class LegalRepresentative(models.Model):
    _name = 'reclutamiento__kuale.legal.representative'
    _description = 'Representantes legales'
    name = fields.Char(string='Nombre', required=True)
    company_branch = fields.Many2one('res.company', string='Empresa – Sucursal', required=True)
    street = fields.Char(string='Dirección')
    zip_code = fields.Char(string='Código Postal')
    phone = fields.Char(string='Teléfono')
    mobile = fields.Char(string='Teléfono celular')
    description = fields.Text(string='Descripcion')
    status = fields.Selection([
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ], string='Estatus', default='Activo', required=True)
