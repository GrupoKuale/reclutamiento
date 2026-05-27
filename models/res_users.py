from odoo import fields, models, _
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _action_reset_password(self):
        create_mode = bool(self.env.context.get('create_user'))
        params = self.env['ir.config_parameter'].sudo()

        # Selecciona la plantilla según el contexto
        if create_mode:
            template_id = int(params.get_param(
                'my_recruitment.signup_email_template_id', 0))
        else:
            template_id = int(params.get_param(
                'my_recruitment.reset_password_email_template_id', 0))

        if template_id:
            template = self.env['mail.template'].browse(template_id)
            self.mapped('partner_id').signup_prepare(
                signup_type="reset", expiration=False
            )
            for user in self:
                if not user.email:
                    raise UserError(_(
                        "No se puede enviar correo: %s no tiene email.",
                        user.name
                    ))
                template.send_mail(
                    user.id,
                    force_send=True,
                    raise_exception=True,
                    email_values={
                        'email_cc': False,
                        'auto_delete': True,
                        'message_type': 'user_notification',
                        'recipient_ids': [],
                        'partner_ids': [],
                        'scheduled_date': False,
                        'email_to': user.email,
                    }
                )
            return  # No llama super(), evita el correo por defecto de Odoo

        # Si no hay plantilla configurada, comportamiento normal de Odoo
        return super()._action_reset_password()