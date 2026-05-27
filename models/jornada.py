# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Jornada(models.Model):
    _name = 'reclutamiento__kuale.jornada'
    _description = "reclutamiento__kuale.jornada"
    _order = "name"

    name = fields.Char('Nombre', required=True)
    description = fields.Text('Descripcion')
    contract_type_id = fields.Many2one('reclutamiento__kuale.contract_type', string="Tipo de contrato", required=True, ondelete='cascade')

