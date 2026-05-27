
from odoo import api,fields, models

class CompetenciesLevel(models.Model):
    _name = 'reclutamiento__kuale.competencies_level'
    _description = 'reclutamiento__kuale.competencies_level'
    _order = "level_progress desc"

    competency_type_id = fields.Many2one('reclutamiento__kuale.competencies_type', string='Tipo de competencia')
    name = fields.Char(required=True, string="Nombre")
    level_progress = fields.Integer(string="Progreso",
                                    help="Progresar desde cero conocimientos (0%) hasta dominar completamente el tema (100%).")
    default_level = fields.Boolean(
        help="Si está marcada, este nivel será el predeterminado seleccionado al elegir esta habilidad.")

    _sql_constraints = [
        ('check_level_progress', 'CHECK(level_progress BETWEEN 0 AND 100)',
         "El progreso debe ser un número entre 0 y 100."),
    ]

    @api.depends('level_progress')
    @api.depends_context('from_competency_level_dropdown')
    def _compute_display_name(self):
        if not self._context.get('from_competency_level_dropdown'):
            return super()._compute_display_name()
        for record in self:
            record.display_name = f"{record.name} ({record.level_progress}%)"

    @api.model_create_multi
    def create(self, vals_list):
        competency_levels = super().create(vals_list)
        for level in competency_levels:
            if level.default_level:
                level.competency_type_id.competencies_level_ids.filtered(lambda r: r.id != level.id).default_level = False
        return competency_levels

    def write(self, vals):
        res = super().write(vals)
        if vals.get('default_level'):
            self.competency_type_id.competencies_level_ids.filtered(lambda r: r.id != self.id).default_level = False
        return res