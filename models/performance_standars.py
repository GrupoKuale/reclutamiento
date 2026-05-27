from odoo import models, fields, api


class PerformanceStandars(models.Model):
    _name = 'reclutamiento__kuale.performance_standars'
    _description = 'reclutamiento__kuale.performance_standars'

    active = fields.Boolean(default=True)
    name = fields.Char('Nombre', required=True, translate=True)
    description = fields.Text('Descripción')

    # Relation Job
    job_ids = fields.Many2many('hr.job', 'job_performancest_rel', 'perfst_id', 'job_id', string='Trabajo')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre del estándar de rendimiento ya existe!"),
    ]
