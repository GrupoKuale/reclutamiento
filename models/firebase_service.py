# NOT IMPLEMENTED YET

from firebase_admin import credentials, initialize_app, messaging, get_app
from odoo import models, api
import logging
from ..utils import clean_html

_logger = logging.getLogger(__name__)

class FirebaseNotificationService:

    def __init__(self, env):
        self.env = env
        self.app = None
        self._initialize_firebase()

    def _initialize_firebase(self):
        try:
            self.app = get_app()
        except ValueError:
            file_env = self.env['ir.config_parameter'].sudo().get_param('firebase.credentials_file')
            cred = credentials.Certificate(file_env)
            self.app = initialize_app(cred)

    def send_firebase_notification(self, token, message_body):
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="Nuevo mensaje",
                    body=clean_html(message_body),
                ),
                token=token,
            )

            response = messaging.send(message, app=self.app)
            _logger.info(f'Firebase notification sent: {response}')
        except Exception as e:
            _logger.error(f'Error sending Firebase notification: {str(e)}')
