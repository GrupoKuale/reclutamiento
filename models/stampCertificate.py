from odoo import fields, models, api

# Modelo para Certificado de Timbrado
class DigitalStampCertificate(models.Model):
    _name = 'reclutamiento__kuale.digital.stamp.certificate'
    _description = 'Certificado de sellado'

    name = fields.Char(string='Nombre', required=True)
    imss_registration_id = fields.Many2one('reclutamiento__kuale.imss.registration', string='ID Registro IMSS', required=True)
    certificate_number = fields.Char(string='Número de certificado', required=True)
    password = fields.Char(string='Contraseña', required=True)
    confirmation = fields.Char(string='Confirmación', required=True)
    validity = fields.Date(string='Validez', required=True)
    valid_from = fields.Date(string='De', required=True)
    valid_to = fields.Date(string='A', required=True)
    status = fields.Selection([
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ], string='Estatus', default='Activo', required=True)

