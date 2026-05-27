from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    device_tokens = fields.One2many('partner.device.token', 'partner_id', string='Dispositivos')

    # Campos Kuale - nombre separado
    kuale_first_name     = fields.Char('Nombre(s)', tracking=True)
    kuale_last_name      = fields.Char('Apellido paterno', tracking=True)
    kuale_second_last    = fields.Char('Apellido materno', tracking=True)
