from odoo import _, http
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.web.controllers.utils import ensure_db


class RecruitmentWebsiteLoginController(http.Controller):
    _KUALE_LOGIN_SESSION_KEY = 'kuale_recruitment_auth_ok'

    @staticmethod
    def _sanitize_redirect(redirect):
        if not redirect:
            return '/'
        redirect = redirect.strip()
        if redirect.startswith('/') and not redirect.startswith('//') and not redirect.startswith('/kuale/login'):
            return redirect
        return '/'

    @http.route('/kuale/login', type='http', auth='public', website=True, sitemap=False, methods=['GET', 'POST'])
    def kuale_login(self, redirect=None, **post):
        ensure_db()

        if not request.website.kuale_force_login:
            request.session.pop(self._KUALE_LOGIN_SESSION_KEY, None)
            return request.redirect('/')

        safe_redirect = self._sanitize_redirect(redirect or post.get('redirect'))
        if request.session.uid and request.session.get(self._KUALE_LOGIN_SESSION_KEY):
            return request.redirect(safe_redirect)

        values = {
            'error': False,
            'login': (post.get('login') or '').strip(),
            'redirect': safe_redirect,
        }

        if request.httprequest.method == 'POST':
            password = post.get('password') or ''
            try:
                request.session.authenticate(request.db, values['login'], password)
                request.session[self._KUALE_LOGIN_SESSION_KEY] = True
                return request.redirect(safe_redirect)
            except AccessDenied:
                values['error'] = _('Usuario o contrasena incorrectos.')

        response = request.render('reclutamiento__kuale.kuale_recruitment_login_page', values)
        response.headers['Cache-Control'] = 'no-cache'
        return response
