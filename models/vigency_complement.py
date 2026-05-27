from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo import models, fields, api


class vigency_complement(models.Model):
    _name = 'vigency_complement'
    _description = 'vigency_complement'

    applicant_id = token = fields.Integer('Id applicant')
    token = fields.Char('Token')
    vigency = fields.Datetime('Vigencia')