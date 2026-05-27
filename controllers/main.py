# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class KualeAuth(http.Controller):
    
    @http.route('/kuale/logout', type='http', auth='public', website=True)
    def kuale_logout(self):
        request.session.logout(keep_db=True)
        return request.redirect('/reclutamiento')