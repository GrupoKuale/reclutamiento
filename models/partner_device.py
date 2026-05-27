from odoo import fields, models

class PartnerDeviceToken(models.Model):
    _name = 'partner.device.token'
    _description = 'Dispositivos de los contactos'

    partner_id = fields.Many2one('res.partner', string='Contacto', required=True)
    device_token = fields.Char('Identificador de dispositivo', required=True)
    last_login = fields.Datetime('Último inicio de sesión', default=lambda self: fields.Datetime.now())
