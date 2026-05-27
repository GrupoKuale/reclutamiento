from odoo import fields, models, api

class HrWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    latitude = fields.Float(string="Latitud", required=True, help="Latitud de lugar de trabajo",  digits=(20, 16))
    longitude = fields.Float(string="Longitud", required=True, help="Longitud de lugar de trabajo",  digits=(20, 16))
    allowed_distance = fields.Float(string="Distancia permitida en metros", required=True, default=100, help="Distancia permitida para marcar asistencia") 
