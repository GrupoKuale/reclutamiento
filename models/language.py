from odoo import models, fields, api


class Language(models.Model):
    _name = 'reclutamiento__kuale.language'
    _description = 'reclutamiento__kuale.language'

    active = fields.Boolean(default=True)
    name = fields.Char('Nombre', required=True, translate=True)
    description = fields.Text('Descripcion')
    language_level_ids = fields.One2many('reclutamiento__kuale.language_level', 'language_k_id', string="Nivel")
    level = fields.Many2one('reclutamiento__kuale.language_level', string="Nivel", domain="[('language_k_id', '=', active_id)]")
    level_progress = fields.Integer(related='level.level_progress', string="Porcentaje")

    # job_id = fields.Many2one('hr.job', string="Job", ondelete='cascade', required=True)

    """
    job_ids = fields.Many2many('hr.job', 'job_language_rel', 'lan_id', 'job_id', string='Job')

    plan_id = fields.Many2one('hr.job', string="Plan", ondelete='cascade', required=True)
    """
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre del idioma ya existe!"),
    ]

    @api.model
    def default_get(self, fields):
        res = super(Language, self).default_get(fields)
        res['level'] = self._context.get('active_id', False)
        return res

