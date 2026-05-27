# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Schooling(models.Model):
    _name = 'reclutamiento__kuale.schooling'
    _description = "Escolaridad"
    _order = "name"

    active = fields.Boolean(default=True)
    name = fields.Char(string='Nombre', required=True, translate=True)
    description = fields.Text('Descripcion')

    job_ids = fields.Many2many('hr.job', 'job_schooling_rel', 'sch_id', 'job_id', string='Trabajo')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre de las escolaridad ya existe!"),
    ]