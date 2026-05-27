from odoo import models, fields, api


class City(models.Model):
    _name = 'reclutamiento__kuale.city'
    _description = 'Ciudades mapeadas'

    active = fields.Boolean(default=True)
    name = fields.Char('Nombre', compute='_compute_name')
    state_id = fields.Many2one("res.country.state", string="Estado")

    code = fields.Char(string="Código Postal")
    settlement = fields.Char(string="Asentamiento")
    settlement_type = fields.Char(string="Tipo")
    municipality = fields.Char(string="Municipio")
    city = fields.Char(string="Ciudad")
    state = fields.Char(string="Estado")

    @api.depends('code')
    def _compute_name(self):
        for record in self:
            name_format = self.env.context.get('name_format')
            if name_format == 'code':
                name = f"{record.code}"
            elif name_format == 'municipality':
                name = f"{record.municipality}"
            elif name_format == 'state':
                name = f"{record.state}"
            elif name_format == 'colony':
                name = f"{record.settlement}"
            elif name_format == 'city':
                name = f"{record.city}"
            else:
                name = f"{record.code}"
            record.name = name

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            records = self.search([
                                      '|',
                                      ('code', operator, name),
                                      ('city', operator, name)
                                  ] + args, limit=limit)
        else:
            records = self.search(args, limit=limit)

        return records.name_get()


class TypeRoad(models.Model):
    _name = 'reclutamiento__kuale.type_road'
    _description = 'Tipo de vialidad'

    name = fields.Char('Nombre')
    description = fields.Char("Descripcion")
