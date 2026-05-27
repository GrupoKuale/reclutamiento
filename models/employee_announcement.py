from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import io
from PIL import Image


def _get_image_format(image_data):
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    return image.format.lower() if image.format else 'octet-stream'


class EmployeeAnnouncement(models.Model):
    _name = 'reclutamiento__kuale.employee.announcement'
    _description = 'Anuncios de empleados'
    _inherit = ['reclutamiento__kuale.reaction.mixin']
    _order = 'create_date desc'

    header = fields.Text(string='Encabezado', help='Encabezado del anuncio')
    image = fields.Binary(string='Imagen', attachment=True)
    image_url = fields.Char(string='URL de la imagen', compute='_compute_image_url', store=True)
    postedBy = fields.Many2one('res.users', string='Subido por', default=lambda self: self.env.user)

    @api.model
    def create(self, vals):
        if 'postedBy' not in vals:
            vals['postedBy'] = self.env.uid
        record = super(EmployeeAnnouncement, self).create(vals)
        if record.image:
            Attachment = self.env['ir.attachment'].sudo()
            image_data = record.image
            type = _get_image_format(image_data)
            file_name = f"announcement_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{type}"

            attachment = Attachment.create({
                'name': file_name,
                'type': 'binary',
                'datas': record.image,
                'res_model': 'reclutamiento__kuale.employee.announcement',
                'res_id': record.id,
                'res_field': 'image',
                'mimetype': f'image/{type}',
                'public': True,
            })
            # Generar la URL pública de la imagen
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            record.image_url = f"{base_url}/web/content/{attachment.id}"
        return record


@api.depends('image')
def _compute_image_url(self):
    for record in self:
        if record.image:
            Attachment = self.env['ir.attachment'].sudo()
            attachment = Attachment.search([
                ('res_model', '=', 'reclutamiento__kuale.employee.announcement'),
                ('res_id', '=', record.id),
                ('res_field', '=', 'image')
            ], limit=1)

            if attachment:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                record.image_url = f"{base_url}/web/content/{attachment.id}"
            else:
                record.image_url = False
        else:
            record.image_url = False


@api.constrains('postedBy')
def _check_posted_by(self):
    for record in self:
        if not record.postedBy:
            raise ValidationError("El campo 'Subido por' no puede estar vacío.")


@api.constrains('header', 'image')
def _check_post(self):
    for record in self:
        if not (record.header or record.image):
            raise ValidationError("Al menos uno de los campos 'Encabezado' o 'Imagen' debe ser llenado")
