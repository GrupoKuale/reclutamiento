
from odoo import api,models,fields

class Calendar(models.Model):
    _inherit = 'calendar.event'

    course = fields.Boolean(string='Course',  help='Indicate if this event is a course.')