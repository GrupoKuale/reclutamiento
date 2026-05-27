from odoo import api, models, fields


class Competencies(models.Model):
    _name = 'reclutamiento__kuale.competencies'
    _description = 'reclutamiento__kuale.competencies'

    active = fields.Boolean(default=True)
    name = fields.Char('Competencia', required=True, translate=True)
    # Used by website/PDF templates; optional descriptive text for the competency.
    description = fields.Text('Descripcion', translate=True)
    sequence = fields.Integer(default=10, string="Secuencia")
    competency_type_id = fields.Many2one('reclutamiento__kuale.competencies_type', required=True, ondelete='cascade', string="Tipo de competencia")

    # Relation Job
    job_ids = fields.Many2many('hr.job', 'job_competencies_rel', 'comp_id', 'job_id', string='Trabajo')
    # job_id = fields.Many2one('hr.job', 'Job', readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre de las competencias ya existe!"),
    ]

    @api.depends('competency_type_id')
    @api.depends_context('from_competencies_dropdown')
    def _compute_display_name(self):
        if not self._context.get('from_competencies_dropdown'):
            return super()._compute_display_name()
        for record in self:
            record.display_name = f"{record.name} ({record.competency_type_id.name})"
