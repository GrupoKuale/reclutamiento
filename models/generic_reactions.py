from odoo import api, fields, models


class GenericReactions(models.Model):
    _name = 'reclutamiento__kuale.generic.reaction'
    _description = 'Reacciones Genéricas'

    res_model = fields.Char(string='Modelo relacionado', required=True)
    res_id = fields.Integer(string='Id de registro relacionado', required=True)
    user_id = fields.Many2one('res.users', string='Usuario', required=True, default=lambda self: self.env.user)
    reaction_type = fields.Selection([
        ('like', 'Me gusta'),
        ('dislike', 'No me gusta'),
        ('love', 'Amo'),
        ('wow', 'Wow'),
        ('sad', 'Triste'),
        ('angry', 'Enojado')
    ], string='Reacción', required=True)
    date = fields.Datetime(string='Fecha', default=fields.Datetime.now)

    _sql_constraints = [
        ('unique_reaction', 'unique(res_model, res_id, user_id)', 'Solo puedes reaccionar una vez.')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('res_model'):
            vals['res_model'] = self._context.get('res_model')
        if not vals.get('res_id'):
            vals['res_id'] = self._context.get('res_id')
        return super(GenericReactions, self).create(vals)
