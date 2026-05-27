from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    signup_email_template_id = fields.Many2one(
        'mail.template',
        string='Plantilla de bienvenida',
        domain=[('model', '=', 'res.users')],
        config_parameter='my_recruitment.signup_email_template_id',
    )

    reset_password_email_template_id = fields.Many2one(
        'mail.template',
        string='Plantilla de cambio de contraseña',
        domain=[('model', '=', 'res.users')],
        config_parameter='my_recruitment.reset_password_email_template_id',
    )

    stage_change_email_template_id = fields.Many2one(
        'mail.template',
        string='Plantilla de cambio de etapa',
        domain=[('model', '=', 'hr.applicant')],
        config_parameter='reclutamiento__kuale.stage_change_email_template_id',
    )