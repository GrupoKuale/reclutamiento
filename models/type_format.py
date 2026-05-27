from odoo import models, fields, api


class TypeFormat(models.Model):
    _name = 'reclutamiento__kuale.type_format'
    _description = 'reclutamiento__kuale.type_format'

    active = fields.Boolean('Activo', default=True)
    name = fields.Char('Nombre', required=True, translate=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Ya existe un tipo de formato con el mismo nombre!"),
    ]
