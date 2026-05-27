from odoo import api, models

class Website(models.Model):
    _inherit = 'website'

    @api.model
    def create(self, vals):
        if 'show_line_subtotals_tax_selection' not in vals:
            vals['show_line_subtotals_tax_selection'] = 'tax_excluded'
        return super().create(vals)
