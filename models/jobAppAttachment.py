from odoo import models, fields

class JobApplicationAttachment(models.Model):
    _name = 'job.application.attachment'

    name = fields.Char(string='Nombre')
    file = fields.Binary(string='Archivo')
    filename = fields.Char(string='Nombre de archivo')
    application_id = fields.Many2one('job.application', string='Solicitud')