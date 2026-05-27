# NOT IMPLEMENTED YET
from odoo import models, api
import logging
from ..models.firebase_service import FirebaseNotificationService


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        message = super(MailMessage, self).create(vals)
        self._send_push_notification(message)
        return message

    def _send_push_notification(self, message):
        recipient_partners = message.partner_ids.filtered(lambda p: p.id != message.author_id.id)
        firebase_service = FirebaseNotificationService(self.env)

        for partner in recipient_partners:
            device_tokens = partner.device_tokens.mapped('device_token')
            if device_tokens:
                for token in device_tokens:
                    firebase_service.send_firebase_notification(token, message.body)
