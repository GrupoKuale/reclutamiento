# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class LanguageLevel(models.Model):
    _name = 'reclutamiento__kuale.language_level'
    _description = "reclutamiento__kuale.language_level"
    _order = "name"

    name = fields.Char('Nombre', required=True)
    # sequence = fields.Integer(default=10)
    level_progress = fields.Integer(string="Porcentaje",
                                    help="Progresar desde cero conocimientos (0%) hasta dominar completamente el tema (100%).", required=True)

    language_k_id = fields.Many2one('reclutamiento__kuale.language', ondelete='cascade', string="Idioma")

    # _sql_constraints = [
    #    ('check_level_progress', 'CHECK(level_progress BETWEEN 0 AND 100)',
    #     "Progress should be a number between 0 and 100."),
    # ]

    """@api.depends('level_progress')
    @api.depends_context('from_skill_level_dropdown')
    def _compute_display_name(self):
        if not self._context.get('from_skill_level_dropdown'):
            return super()._compute_display_name()
        for record in self:
            record.display_name = f"{record.name} ({record.level_progress}%)
            """

    """@api.model_create_multi
    def create(self, vals_list):
        skill_levels = super().create(vals_list)
        for level in skill_levels:
            if level.default_level:
                level.skill_type_id.skill_level_ids.filtered(lambda r: r.id != level.id).default_level = False
        return skill_levels

    def write(self, vals):
        res = super().write(vals)
        if vals.get('default_level'):
            self.skill_type_id.skill_level_ids.filtered(lambda r: r.id != self.id).default_level = False
        return res
    """
