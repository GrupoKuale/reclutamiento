from odoo import api, fields, models
from datetime import datetime
import base64
import io
from PIL import Image


def _get_image_format(image_data):
    """Determina el formato de la imagen a partir de los datos binarios."""
    if not image_data:
        return None 
    try:
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))
        return image.format.lower() if image.format else 'octet-stream'
    except (IOError, ValueError) as e:
        return None



class Employee(models.Model):
    _inherit = 'hr.employee'

    image_url = fields.Char("Imagen URL", compute="_compute_image_url", store=True)

    @api.model
    def create(self, vals):
        record = super(Employee, self).create(vals)
        if record.image_1920:
            Attachment = self.env['ir.attachment'].sudo()
            image_type = _get_image_format(record.image_1920)
            
            if image_type:
                file_name = f"employee_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{image_type}"
                attachment = Attachment.create({
                    'name': file_name,
                    'type': 'binary',
                    'datas': record.image_1920,
                    'res_model': 'hr.employee',
                    'res_id': record.id,
                    'res_field': 'image_1920',
                    'mimetype': f'image/{image_type}',
                    'public': True,
                })

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                record.image_url = f"{base_url}/web/content/{attachment.id}"
        return record

    def write(self, vals):
        res = super(Employee, self).write(vals)
        if 'image_1920' in vals:
            for record in self:
                if record.image_1920:
                    Attachment = self.env['ir.attachment'].sudo()
                    
                    image_type = _get_image_format(record.image_1920)
                    if image_type:
                       
                        attachment = Attachment.search([
                            ('res_model', '=', 'hr.employee'),
                            ('res_id', '=', record.id),
                            ('res_field', '=', 'image_1920')
                        ], limit=1)

                        if attachment:
                          
                            attachment.write({
                                'datas': record.image_1920,
                                'public': True
                            })
                        else:
                            
                            file_name = f"employee_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{image_type}"
                            attachment = Attachment.create({
                                'name': file_name,
                                'type': 'binary',
                                'datas': record.image_1920,
                                'res_model': 'hr.employee',
                                'res_id': record.id,
                                'res_field': 'image_1920',
                                'mimetype': f'image/{image_type}',
                                'public': True,
                            })

                        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        record.image_url = f"{base_url}/web/content/{attachment.id}"
                else:
                    record.image_url = False
        return res


    @api.depends('image_1920')
    def _compute_image_url(self):
        for record in self:
            if record.image_1920:
                Attachment = self.env['ir.attachment'].sudo()
                attachment = Attachment.search([
                    ('res_model', '=', 'hr.employee'),
                    ('res_id', '=', record.id),
                    ('res_field', '=', 'image_1920')
                ], limit=1)

                if attachment:
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    record.image_url = f"{base_url}/web/content/{attachment.id}"
                else:
                    record.image_url = False
            else:
                record.image_url = False
