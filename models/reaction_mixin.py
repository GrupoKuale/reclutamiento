from odoo import api, fields, models

class ReactionMixin(models.AbstractModel):
    _name = 'reclutamiento__kuale.reaction.mixin'
    _description = 'Reaction Mixin'

    reaction_ids = fields.One2many('reclutamiento__kuale.generic.reaction', 'res_id', string='Reacciones',
                                   domain=lambda self: [('res_model', '=', self._name)])

    def add_reaction(self):
        self.ensure_one()

        # verify existing reaction in the post to update the reaction instead of creating a new
        existing_reaction = self.env['reclutamiento__kuale.generic.reaction'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('user_id', '=', self.env.uid)
        ], limit=1)

        reaction_vals = {
            'reaction_type': self.env.context.get('reaction_type'),
            'user_id': self.env.uid,
            'res_model': self._name,
            'res_id': self.id,
        }

        if existing_reaction:
            # Actualiza la reacción existente
            existing_reaction.write(reaction_vals)
        else:
            # Crea una nueva reacción
            self.env['reclutamiento__kuale.generic.reaction'].create(reaction_vals)

        return True