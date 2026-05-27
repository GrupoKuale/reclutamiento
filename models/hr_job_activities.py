# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from collections import defaultdict


class HRJobActivities(models.Model):
    _name = 'reclutamiento__kuale.job_activities'
    _description = "Actividades del Trabajo"
    _order = "skill_type_id, skill_level_id"

    """
    employee_id = fields.Many2one('hr.employee', required=True, ondelete='cascade')
    skill_id = fields.Many2one('hr.skill', compute='_compute_skill_id', store=True, domain="[('skill_type_id', '=', skill_type_id)]", readonly=False, required=True, ondelete='cascade')
    skill_level_id = fields.Many2one('hr.skill.level', compute='_compute_skill_level_id', domain="[('skill_type_id', '=', skill_type_id)]", store=True, readonly=False, required=True, ondelete='cascade')
    skill_type_id = fields.Many2one('hr.skill.type',
                                    default=lambda self: self.env['hr.skill.type'].search([], limit=1),
                                    required=True, ondelete='cascade')
    level_progress = fields.Integer(related='skill_level_id.level_progress')
    """

    # Activities
    job_id = fields.Many2one('hr.job', required=True, ondelete='cascade', string="Trabajo")
    a_knowledge_id = fields.Many2many('reclutamiento__kuale.a_knowledge', compute='_compute_knowledge_id',
                                      domain="[('activities_k_id', '=', activities_k_id)]", store=True,
                                      readonly=False,
                                      ondelete='cascade',
                                      string="Conocimiento")
    activities_k_id = fields.Many2one('reclutamiento__kuale.activities', 'Actividades',
                                      default=lambda self: self.env['reclutamiento__kuale.activities'].search(
                                          [], limit=1),
                                      )
