from odoo import models, fields, api


class InternalRelations(models.Model):
    _name = 'reclutamiento__kuale.internal_relations'
    _description = 'reclutamiento__kuale.internal_relations'

    active = fields.Boolean(default=True)
    name = fields.Char('Nombre', required=True, translate=True)
    description = fields.Text('Descripción')

    # Relation Job
    job_ids = fields.Many2many('hr.job', 'job_internalrel_rel', 'intrel_id', 'job_id', string='Trabajo')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre de la relación interna ya existe!"),
    ]


class CommentsExp(models.Model):
    _name = 'reclutamiento__kuale.comments_exp'
    _description = 'reclutamiento__kuale.comments_exp'

    # job_ids = fields.Many2many('hr.job', 'job_exp_rel', 'exp_id', 'job_id', string='Job')

    job_id = fields.Many2one("hr.job", string="Trabajo")
    active = fields.Boolean(default=True)
    name = fields.Char(string='Comentarios generales/expectativas', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre del comentario/experiencia ya existe!"),
    ]
