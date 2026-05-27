from odoo import models, fields, api, exceptions

class product_template(models.Model):
    _inherit = 'product.template'
    uniform_type = fields.Boolean('Uniforme', default=False)
    service_to_purchase = fields.Boolean('Purchase on Order', default=False)