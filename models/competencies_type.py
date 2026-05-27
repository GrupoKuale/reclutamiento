from odoo import fields, models


class CompetenciesType(models.Model):
    _name = 'reclutamiento__kuale.competencies_type'
    _description = 'reclutamiento__kuale.competencies_type'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    competencies_ids = fields.One2many('reclutamiento__kuale.competencies', 'competency_type_id',
                                       string='Competencias')
    competencies_level_ids = fields.One2many('reclutamiento__kuale.competencies_level', 'competency_type_id', string='Niveles')
