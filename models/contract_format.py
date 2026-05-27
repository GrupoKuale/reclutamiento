from odoo import _, models, fields, api
from odoo.tools.safe_eval import safe_eval
from markupsafe import Markup

from lxml import etree


class ContractDetails(models.Model):
    _name = 'reclutamiento__kuale.contract_format'
    _description = 'Contract Format'

    active = fields.Boolean(default=True)
    name = fields.Char('Nombre', translate=True, required=True)
    description = fields.Text(
        'Descripción del formato', translate=True,
        help="Este campo se utiliza para la descripción interna del uso del formato del contrato.")
    body = fields.Html(
       'Cuerpo del contrato', render_engine='qweb', render_options={'post_process': True},
        prefetch=True, translate=True, sanitize=False,
        help="En este campo se agrega el contenido del cuerpo del contrato o tipo de formato seleccionado, "
             "donde para poder ingresar los valores del empleado se deberá editar en el modo código '</>', "
             "usando la siguiente sintaxis: <t t-out='object.DATO_A_MOSTRAR}'></t>")

    type_format_id = fields.Many2one('reclutamiento__kuale.type_format', string='Tipo de Formato')

    """def render_body(self, doc):
        body_template = self.body or ''
        context = {'doc': doc, 'body': Markup(body_template)}
        return self.env['ir.ui.view']._render_template('reclutamiento__kuale.dynamic_body_template', context)"""

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_("%s (copy)", self.name))
        return super(ContractDetails, self).copy(default)

    def print_quotation_preview(self):
        self.ensure_one()
        return self.env.ref('reclutamiento__kuale.report_contract_employee_preview').report_action(self)