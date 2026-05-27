# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Segments(models.Model):
    _name = 'reclutamiento__kuale.segments'
    _description = 'reclutamiento__kuale.segments'

    active = fields.Boolean(default=True)
    name = fields.Char("Nombre")
    description = fields.Text('Descripción')
    company_id = fields.Many2one('res.company', string='Empresa', index=True, default=lambda self: self.env.company)

    department_ids = fields.Many2many('hr.department', 'department_segment_rel', 'segment_id', 'dep_id',
                                      string='Departamento')

    # employee_ids = fields.Many2many('hr.employee', 'employee_category_rel', 'category_id', 'emp_id',
    #                                string='Employees')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre del segmento ya existe!"),
    ]