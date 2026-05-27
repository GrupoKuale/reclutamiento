from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'
    _KUALE_LOGIN_SESSION_KEY = 'kuale_recruitment_auth_ok'

    _KUALE_PUBLIC_PATH_PREFIXES = (
        '/kuale/login',
        '/web',
        '/website/lang/',
        '/website/force/',
        '/website/image',
        '/website/translations/',
        '/favicon.ico',
        '/robots.txt',
        '/sitemap.xml',
        '/sitemap-',
    )

    @classmethod
    def _dispatch(cls, endpoint):
        if cls._must_force_kuale_login():
            target = cls._current_path_with_query()
            return request.redirect_query('/kuale/login', {'redirect': target})
        return super()._dispatch(endpoint)

    @classmethod
    def _must_force_kuale_login(cls):
        if not getattr(request, 'is_frontend', False):
            return False

        website = getattr(request, 'website', False)
        if not website:
            website = request.env['website'].get_current_website()
        if not website.sudo().kuale_force_login:
            # Leaving the recruitment website resets its dedicated auth gate.
            request.session.pop(cls._KUALE_LOGIN_SESSION_KEY, None)
            return False

        # Recruitment website requires explicit login handshake for this session.
        if request.session.uid and request.session.get(cls._KUALE_LOGIN_SESSION_KEY):
            return False

        path = request.httprequest.path or '/'
        if cls._is_public_path(path):
            return False

        return True

    @classmethod
    def _is_public_path(cls, path):
        if '/static/' in path:
            return True
        return any(path.startswith(prefix) for prefix in cls._KUALE_PUBLIC_PATH_PREFIXES)

    @staticmethod
    def _current_path_with_query():
        path = request.httprequest.path or '/'
        query = request.httprequest.query_string.decode()
        return f'{path}?{query}' if query else path
