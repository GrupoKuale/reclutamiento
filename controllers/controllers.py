# -*- coding: utf-8 -*-
# from odoo import http


# class ReclutamientoKuale(http.Controller):
#     @http.route('/reclutamiento__kuale/reclutamiento__kuale', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/reclutamiento__kuale/reclutamiento__kuale/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('reclutamiento__kuale.listing', {
#             'root': '/reclutamiento__kuale/reclutamiento__kuale',
#             'objects': http.request.env['reclutamiento__kuale.reclutamiento__kuale'].search([]),
#         })

#     @http.route('/reclutamiento__kuale/reclutamiento__kuale/objects/<model("reclutamiento__kuale.reclutamiento__kuale"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('reclutamiento__kuale.object', {
#             'object': obj
#         })

