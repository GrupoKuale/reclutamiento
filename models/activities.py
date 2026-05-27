from odoo import models, fields, api


class Activities(models.Model):
    _name = 'reclutamiento__kuale.activities'
    _description = 'reclutamiento__kuale.activities'

    active = fields.Boolean(default=True)
    name = fields.Char('Actividades a realizar', required=True, translate=True)
    description = fields.Html('Descripcion')
    a_knowledge_ids = fields.One2many('reclutamiento__kuale.a_knowledge', 'activities_k_id', string="Conocimientos técnicos")

    knowledge_ids = fields.Many2many('reclutamiento__kuale.a_knowledge', 'act_knowledge_rel', string="Conocimientos técnicos",
                                     domain="[('activities_k_id', '=', active_id)]")

    show_description = fields.Boolean(default=False, string="Mostrar descripcion",)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre de la actividad ya existe!"),
    ]

    @api.model
    def default_get(self, fields):
        res = super(Activities, self).default_get(fields)
        res['knowledge_ids'] = self._context.get('active_id', False)
        return res
 
    def open_record_activities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Editar Actividad',
            'view_mode': 'form',
            'res_model': 'reclutamiento__kuale.activities',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    def toggle_description(self):
        self.ensure_one()
        # Obtener el estado actual de `show_description`
        current_state = self.show_description
        all_activities = self.search([])  # Esto obtiene todos los registros del modelo
        for activity in all_activities:
            activity.show_description = False

        if not current_state:
            self.show_description = True