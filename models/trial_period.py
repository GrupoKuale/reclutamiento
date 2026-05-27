# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class TrialPeriod(models.Model):
    _name = 'reclutamiento__kuale.trial_period'
    _description = "reclutamiento__kuale.trial_period"
    _order = "sequence,name"

    name = fields.Char('Nombre', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    description = fields.Text('Descripcion')
    contract_type_id = fields.Many2one('reclutamiento__kuale.contract_type',string="Tipo de contrato", required=True, ondelete='cascade')

    """@api.depends('contract_type_id')
    @api.depends_context('from_skill_dropdown')
    def _compute_display_name(self):
        if not self._context.get('from_skill_dropdown'):
            return super()._compute_display_name()
        for record in self:
            record.display_name = f"{record.name} ({record.contract_type_id.name})"
    """