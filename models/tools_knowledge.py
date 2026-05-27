# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class OperationalTools(models.Model):
    _name = 'reclutamiento__kuale.tools_knowledge'
    _description = "reclutamiento__kuale.tools_knowledge"
    _order = "name"

    active = fields.Boolean(default=True)
    name = fields.Char('Nombre',required=True)
    type = fields.Selection([
        ('tool', 'Herramientas'),
        ('software', 'Software')
    ], required=True, string="Tipo")
    description = fields.Text('Descripcion')

    # Relation Job
    job_ids = fields.Many2many('hr.job', 'job_toolknow_rel', 'tool_id', 'job_id', string='Job')
    job_soft_ids = fields.Many2many('hr.job', 'job_software_rel', 'soft_id', 'job_id', string='Job')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre del conocimiento de la herramienta ya existe!"),
    ]

class KnowledgeExperience(models.Model):
    _name = 'reclutamiento__kuale.knowledge_experience'
    _description = "reclutamiento__kuale.knowledge_experience"

    name = fields.Char('Experiencia', required=True)