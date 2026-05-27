# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ActivitiesKnowledge(models.Model):
    _name = 'reclutamiento__kuale.a_knowledge'
    _description = "reclutamiento__kuale.a_knowledge"
    _order = "sequence,name"

    name = fields.Char(required=True, string="Nombre")
    sequence = fields.Integer(default=10)
    description = fields.Html('Descripcion')
    activities_k_id = fields.Many2one('reclutamiento__kuale.activities', ondelete='cascade')

