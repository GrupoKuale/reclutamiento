from odoo import fields, models, api, _
import logging
from markupsafe import Markup
from datetime import date, timedelta, datetime
import re
import locale
from html import unescape
from num2words import num2words

from lxml import etree

_logger = logging.getLogger(__name__)


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    contract_format_id = fields.Many2one('reclutamiento__kuale.contract_format', string='Tipo de Formato')
    contract_current = fields.Html(string='Contrato Actual')
    body_temp = fields.Html(
        'Cuerpo del formato dinamico', render_engine='qweb', render_options={'post_process': True},
        prefetch=True, translate=True, sanitize=False)
    # body_html = fields.Html(related="contract_format_id.body")
    # body = fields.Html(string='Cuerpo del Formato', compute='_compute_body')
    # Monto aprobado para contrato: Es el sueldo bruto que se configura en el tabulador de sueldos
    monthly_salary = fields.Char("Sueldo mensual bruto", compute="_compute_monthly_salary")
    actual_date = fields.Date('Fecha actual')
    hide_limit_det_contract = fields.Boolean(default=True, compute="_compute_limit_contract")
    send_notif_expiration = fields.Boolean(default=False)
    renew_contract = fields.Selection([
        ('without', 'No asignado'),
        ('yes', 'Renovar'),
        ('no', 'No renovar')
    ], string="Renovar contrato", default="without")

    @api.model
    def write(self, vals):
        for record in self:
            print("renew_contract", record.renew_contract)
            if record.renew_contract == 'without':
                try:
                    if vals['renew_contract'] == 'yes':
                        # crear nuevo contrato y avisar a LGP, G, GG
                        print("nuevo contrato")
                        structure_id = self.env['hr.payroll.structure.type'].search([('name', '=', 'Employee')])
                        contract = {
                            'structure_type_id': structure_id.id,
                            'employee_id': record.employee_id.id,
                            'department_id': record.employee_id.department_id.id,
                            'job_id': record.job_id.id,
                            'resource_calendar_id': 1,
                            'company_id': record.employee_id.company_id.id,
                            'hr_responsible_id': record.employee_id.parent_id.id,
                            'name': 'Contrato Renovado',
                            'date_start': fields.Datetime.now(),
                            'wage': record.job_id.basic_salary,
                            'contract_format_id': record.job_id.job_tab_ids.contract_format.id
                        }
                        contract_c = self.env['hr.contract'].sudo().create(contract)
                        employees_lgp = self.env['hr.employee'].search([
                            ('job_id', '=', record.job_id.id),
                            ('rol_tab_id.rol_employee_selection', '=', 'lgp')
                        ])
                        general_guide = record.job_id.company_id.general_guide.email
                        body = ("Se renovará el contrato con " +
                                record.employee_id.partner_name + record.employee_id.last_name +
                                ". Verifique los datos en el sistema antes de generarlo.")
                        for lgp in employees_lgp:
                            mail = self.env['mail.mail'].sudo().create({
                                'body_html': body,
                                'subject': _('Contrato Renovado'),
                                'email_to': lgp.work_email,
                                'auto_delete': True,
                            })
                            mail.send()
                        if general_guide:
                            mail = self.env['mail.mail'].sudo().create({
                                'body_html': body,
                                'subject': _('Contratos Próximos a vencer'),
                                'email_to': general_guide,
                                'auto_delete': True,
                            })
                            mail.send()
                    if vals['renew_contract'] == 'no':
                        # Avisar a LGP y Nominas para finiquito
                        print("Avisar a LGP y Nominas para finiquito")
                except Exception as e:
                    print("Error en renovar contrato:", e)
        return super(hr_contract, self).write(vals)

    @api.depends('wage')
    def _compute_monthly_salary(self):
        for record in self:
            if record.wage:
                formatted_wage = "${:,.2f}".format(record.wage)
                wage_in_words = num2words(record.wage, lang='es', to='currency', currency='MXN').capitalize()
                record.monthly_salary = f"{formatted_wage} ({wage_in_words} M.N.)"
            else:
                record.monthly_salary = ""

    @api.depends('contract_format_id')
    def _compute_limit_contract(self):
        for record in self:
            # Si es determinado, calcular limite
            type_contract = record.contract_format_id.type_format_id.name
            if type_contract.strip().lower() == "determinado":
                # Tiene fecha de vencimiento, no ocultar campo
                record.hide_limit_det_contract = False
            else:
                # No tiene fecha de vencimiento
                record.hide_limit_det_contract = True

    @api.depends('contract_format_id')
    def _render_dynamic_body(self):
        for record in self:
            if record.contract_format_id:
                template = record.contract_format_id.body or ''
                _logger.info('Rendered Body template: %s', template)

                context = {'object': record}

                # Buscar todas las etiquetas t-out y reemplazar con los valores correspondientes
                def replace_match(match):
                    expr = match.group(1).strip()
                    # Evaluar la expresión en el contexto del objeto
                    try:
                        value = eval(expr, context)
                    except Exception as e:
                        value = str(e)
                    return str(value)

                body_rendered = re.sub(r'<t t-out="([^"]+)"></t>', replace_match, template)
                # record.body = Markup(body_rendered)
                record.contract_format_id.body = Markup(body_rendered)
            else:
                record.contract_format_id.body = ''

    def print_quotation(self):
        self.ensure_one()
        # Guarda el contenido del contrato generado por primera vez
        if self.contract_current:
            return self.env.ref('reclutamiento__kuale.report_contract_employee').report_action(self)
        else:
            self._render_dynamic_body()
            self.contract_current = self.contract_format_id.body
            _logger.info('Rendered Body_contarct: %s', self.contract_format_id.body)
            return self.env.ref('reclutamiento__kuale.report_contract_employee').report_action(self)

    def generate_quotation(self):
        self._render_dynamic_body_temp()
        pdf = self.env.ref('reclutamiento__kuale.report_contract_employee_dynamic').report_action(self)
        return pdf

    def _render_dynamic_body_temp(self):
        try:
            for record in self:
                template = record.contract_format_id.body or ''
                context = {'object': record}

                def replace_match(match):
                    expr = match.group(1).strip()
                    try:
                        value = eval(expr, context)
                        if expr == "object.actual_date":
                            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
                            actual_date = date.today()
                            value = actual_date.strftime('%d de %B del %Y')
                    except Exception as e:
                        value = str(e)
                        print("value except", value)
                    return str(value)

                template = unescape(template)
                body_rendered = re.sub(r'<t t-out="([^"]+)"></t>', replace_match, template)
                self.write({'body_temp': Markup(body_rendered)})
                record.body_temp = Markup(body_rendered)
        except Exception as e:
            value = str(e)
            print("ERROR Creando formato", value)

    def check_contracts_expiring_soon(self):
        try:
            print("Verificando si el ultimo contrato sera valido por mas de una semana")
            today = fields.Date.today()
            one_week_from_today = today + timedelta(days=7)
            expiring_contracts = self.search([
                ('date_end', '<=', one_week_from_today),
                ('state', '!=', 'close'),
                ('send_notif_expiration', '!=', True),
                ('contract_format_id.type_format_id.name', '=', 'Determinado')
            ])
            print("expiring_contracts", expiring_contracts)
            for contract in expiring_contracts:
                # Activar que se enviara notificacion preguntando renovación
                contract.write({'send_notif_expiration': True})
                employee_name = contract.employee_id.name
                body = "Hay algunos contratos próximos a vencer, revise en el modulo de contratos para autorizar o no la renovación y continuar con el proceso"
                employees_lgp = self.env['hr.employee'].search([
                    ('job_id', '=', contract.job_id.id),
                    ('rol_tab_id.rol_employee_selection', '=', 'lgp')
                ])
                print("employees_lgp", employees_lgp)
                general_guide = contract.job_id.company_id.general_guide.email
                print("general_guide email", general_guide)
                for lgp in employees_lgp:
                    mail = self.env['mail.mail'].sudo().create({
                        'body_html': body,
                        'subject': _('Contratos Próximos a vencer'),
                        'email_to': lgp.work_email,
                        'auto_delete': True,
                    })
                    mail.send()
                if general_guide:
                    mail = self.env['mail.mail'].sudo().create({
                        'body_html': body,
                        'subject': _('Contratos Próximos a vencer'),
                        'email_to': general_guide,
                        'auto_delete': True,
                    })
                    mail.send()
        except Exception as e:
            print("Error check_contracts_expiring_soon:", e)
