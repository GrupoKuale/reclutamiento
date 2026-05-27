from odoo import models, api, SUPERUSER_ID

class WebsiteMenuFix(models.Model):
    _inherit = "website.menu"

    @api.model
    def fix_menus_by_website(self):
        env = self.env

        # ===== Reclutamiento =====
        website_reclutamiento = env.ref('reclutamiento__kuale.website_reclutamiento')
        menu_reclutamiento = env.ref('reclutamiento__kuale.menu_reclutamiento_root')
        main_menu_reclutamiento = env['website.menu'].search([
            ('website_id', '=', website_reclutamiento.id),
            ('parent_id', '=', False)
        ], limit=1)
        if main_menu_reclutamiento:
            menu_reclutamiento.parent_id = main_menu_reclutamiento.id
            print("Menú Reclutamiento asociado correctamente")
        else:
            print("No se encontró main_menu para Reclutamiento")

        # ===== Publipuentes =====
        website_publipuentes = env.ref('reclutamiento__kuale.website_publipuentes')
        menu_publipuentes = env.ref('reclutamiento__kuale.menu_publipuentes_root')
        main_menu_publipuentes = env['website.menu'].search([
            ('website_id', '=', website_publipuentes.id),
            ('parent_id', '=', False)
        ], limit=1)
        if main_menu_publipuentes:
            menu_publipuentes.parent_id = main_menu_publipuentes.id
            print("Menú Publipuentes asociado correctamente")
        else:
            print("No se encontró main_menu para Publipuentes")
        return True
