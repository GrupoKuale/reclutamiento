from odoo import models, fields, api
from datetime import datetime


class job_tab(models.Model):
    _name = 'reclutamiento__kuale.job_tab'
    _description = 'reclutamiento__kuale.job_tab'

    active = fields.Boolean(default=True)
    name = fields.Char('Nombre', required=True, translate=True)
    company_id = fields.Many2one('res.company', string='Empresa', index=True, default=lambda self: self.env.company, required=True)
    branch_id = fields.Many2one('res.company', domain="[('parent_id', '=', company_id)]", string="Sucursal")
    job_id = fields.Many2one('hr.job', string="Puesto", required=True)
    department_id = fields.Many2one('hr.department', "Departamento", check_company=True, required=True)
    area_id = fields.Many2one('reclutamiento__kuale.company_area', string="Área", required=True)
    cost_center_id = fields.Many2one('reclutamiento__kuale.cost_center', string="Centro de costos", required=True)
    segment_id = fields.Many2one('reclutamiento__kuale.segments', string="Segmento de negocio", required=True)
    rol_id = fields.Many2one('reclutamiento__kuale.rol_tab', string="Rol asignado", required=True)
    hierarchical_level_id = fields.Many2one('reclutamiento__kuale.hierarchical_level', string="Nivel jerárquico", required=True)
    #Plantilla
    ideal_staffing = fields.Integer("Plantilla ideal", required=True)
    minimum_staffing = fields.Integer("Plantilla mínima", required=True)
    maximum_staffing = fields.Integer("Plantilla máxima", required=True)
    current_staffing = fields.Integer("Plantilla actual", compute="_compute_current_staffing")


    salary = fields.Integer('Salario')
    # report_to_id = fields.Many2one('res.users', 'Report to', check_company=True)
    report_to_id = fields.Many2one(
        'hr.employee', 'Reporta a', compute='_compute_parent_id', store=True, readonly=False,
        check_company=True)
    address = fields.Char('Domicilio físico del trabajo')
    # subordinates_ids = fields.Many2many('res.users', string='Subordinates', domain="[('share', '=', False),
    # ('company_ids', 'in', company_id)]")
    subordinates_ids = fields.Many2many('hr.employee', 'Subordinados', compute='_compute_subordinate_ids', store=True,
                                        readonly=False,
                                        check_company=True)

    business_name = fields.Char('Razón social')
    currency_id = fields.Many2one(string="Moneda", related='company_id.currency_id', readonly=True)
    daily_contract_salary = fields.Monetary('Salario diario (Para contrato)', currency_field='currency_id')
    daily_salary_integrated = fields.Monetary('Salario diario integrado', currency_field='currency_id')
    net_monthly_salary = fields.Monetary('Salario neto mensual (Para ofrecimiento)', currency_field='currency_id')
    capped_net_monthly_salary = fields.Monetary('Salario neto mensual topado (Para ofrecimiento)', currency_field='currency_id')
    gross_monthly_salary = fields.Monetary('Salario bruto mensual (Para contrato)', currency_field='currency_id')
    #Impuestos sobre sueldo
    isrtps = fields.Monetary('ISRTPS', currency_field='currency_id')
    monthly_imss_emp_cont = fields.Monetary('Cuota Imss Patronal mensual', currency_field='currency_id')
    monthly_imss_worker_cont = fields.Monetary('Cuota Imss obrero mensual', currency_field='currency_id')
    monthly_sar_emp_cont = fields.Monetary('Cuota SAR, CyV Patronal mensual', currency_field='currency_id')
    monthly_sar_worker_cont = fields.Monetary('Cuota SAR, CyV Patronal obrero mensual', currency_field='currency_id')
    emp_infonavit_cont = fields.Monetary('Aportación Infonavit patronal', currency_field='currency_id')
    employer_total = fields.Monetary('Total patronal', currency_field='currency_id')
    worker_total = fields.Monetary('Total obrero', currency_field='currency_id')

    #Historial de salarios
    date_historical = fields.Date('Fecha')
    fixed_base_salary = fields.Monetary('Salario base de cotización parte fija', currency_field='currency_id')
    variable_base_salary = fields.Monetary('Salario base de cotización parte variable', currency_field='currency_id')
    capped_base_salary = fields.Monetary('Salario base de cotización topado a 25 UMA', currency_field='currency_id')
    uma_value = fields.Monetary(
        string="Valor UMA actual",
        compute="_compute_uma_value",
        store=True
    )
    historical_salary= fields.One2many('reclutamiento__kuale.salary_history','tab_id', string="Histórico",readonly=True)
    type_benefits = fields.Char('Tipo')
    benefits = fields.Char('Prestaciones')
    description_policies = fields.Char('Descripción/Políticas')
    type_bonus = fields.Char('Tipo')
    name_bonus = fields.Char('Nombre')
    amount_bonus = fields.Integer('Monto')
    #Configuraciones
    type_employee = fields.Many2one('reclutamiento__kuale.type_employee', string='Tipo de empleado')
    interviewer_id = fields.Many2one('hr.employee', string='Entrevistador',
                                     domain="[('company_id', '=', company_id)]")
    recruiter_id = fields.Many2one('hr.employee', string='Reclutador',
                                     domain="[('company_id', '=', company_id)]")
    manager_id = fields.Many2one('hr.employee', string='Gerente',
                                   domain="[('company_id', '=', company_id)]")
    instructor_id = fields.Many2one('hr.employee', string='Instructor',
                                 domain="[('company_id', '=', company_id)]")

    #Contrato
    contract_format = fields.Many2one('reclutamiento__kuale.contract_format', string='Nombre del Contrato')
    contract_type_sat = fields.Many2one('catalog_sat.type_contract', string='Tipo de Contrato')
    working_schedule_id = fields.Many2one('resource.calendar', string='Horas laborales')
    contract_duration = fields.Integer(string="Duración del contrato", help="Especificar días de duración del contrato (30,60,90, 120, 150, 180)")
    expiration_notif_period = fields.Integer(string="Plazo de notificación de vencimiento del contrato", help="Es el número de días a avisar/notificar antes de la fecha de vencimiento al trabajador / LGP")
    legal_representative = fields.Many2one('reclutamiento__kuale.legal.representative', string="Representante legal")
    # employee_ids = fields.Many2many('hr.employee', 'employee_category_rel', 'category_id', 'emp_id',
    #                                string='Employees')
    #SAT
    payment_periodicity = fields.Many2one('catalog_sat.payment_periodicity', string='Periodicidad de pago')
    unionized = fields.Boolean('Sindicalizado', default=False)
    type_workday = fields.Many2one('catalog_sat.type_workday', string='Tipo de jornada')
    fiscal_regime = fields.Many2one('catalog_sat.fiscal_regime', string='Régimen Fiscal del receptor')
    type_regime = fields.Many2one('catalog_sat.type_regime', string='Tipo de regimen receptor')
    use_cfdi = fields.Many2one('catalog_sat.use_cfdi', string='Uso de CFDI del receptor')
    #El registro patronal se va a ligar a la sucursal.
    imss_registration = fields.Many2one('reclutamiento__kuale.imss.registration', string='Número de registro patronal', compute="_compute_id_imms")
    risk_placed = fields.Many2one('catalog_sat.risk_placed', string='Riesgo Puesto')
    payment_method = fields.Many2one('catalog_sat.payment_method', string='Método de Pago')
    federal_entity_code = fields.Many2one('catalog_sat.federal_entity_code', string='Clave de Entidad Federativa')
    #NOMINA
    payment_basis = fields.Many2one('catalog_payroll.payment_basis', string='Base de pago')
    type_benefit = fields.Many2one('catalog_payroll.type_benefit', string='Tipo de prestación')
    #IMSS
    salary_zone = fields.Many2one('catalog_imss.salary_zone', string='Zona de salario')
    type_movement = fields.Many2one('catalog_imss.type_movement', string='Tipo de Movimiento')
    type_worker = fields.Many2one('catalog_imss.type_worker', string='Tipo de Trabajador')
    type_workday_imss = fields.Many2one('catalog_imss.type_workday', string='Tipo de Jornada')
    type_salary = fields.Many2one('catalog_imss.type_salary', string='Tipo de Salario')
    type_working_day_reduced = fields.Many2one('catalog_imss.type_working_day_reduced', string='Tipo de Jornada/Semana reducida')


    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Job Tab name already exists!"),
    ]

    @api.depends('department_id')
    def _compute_parent_id(self):
        for employee in self.filtered('department_id.manager_id'):
            employee.report_to_id = employee.department_id.manager_id

    @api.depends('department_id')
    def _compute_subordinate_ids(self):
        for employee in self.filtered('department_id.manager_id'):
            employee.subordinates_ids = employee.department_id.manager_id

    @api.depends('company_id')
    def _compute_branch_id(self):
        for record in self:
            if not record.company_id:
                record.branch_id = False
            else:
                branch = record.company_id.child_ids
                record.branch_id = branch[0] if branch else False

    @api.depends('branch_id')
    def _compute_current_staffing(self):
        for record in self:
            #No. de trabajadores de ese puesto que ya trabajen en esa sucursal, que esten vigentes
            record.current_staffing = 0
            try:
                employees = self.env['hr.employee'].search([
                    ('job_id', '=', record.job_id.id),  # Buscar por puesto
                    ('active', '=', True),  # Que estén activos
                ])
                print("empleados encontrados", employees)
                record.current_staffing = len(employees)
            except Exception as e:
                print("Error _compute_current_staffing:", e)


    @api.onchange('fixed_base_salary')
    def _compute_sbc_capped(self):
        for record in self:
            # Calcula el salario base de cotización sin tope
            sbc = record.fixed_base_salary + record.variable_base_salary
            # Calcula el tope de 25 UMA
            tope_uma = 25 * record.uma_value
            record.capped_base_salary = min(sbc, tope_uma)
            print("record capped created")

    @api.depends('uma_value')
    def _compute_uma_value(self):
        current_year = str(datetime.now().year)  # Obtener el año actual como string
        uma_record = self.env['reclutamiento__kuale.unit_mesure_update'].search([('name', '=', current_year)], limit=1)
        for record in self:
            record.uma_value = uma_record.daily_value if uma_record else 0.0

    @api.depends('company_id')
    def _compute_id_imms(self):
        for record in self:
            if record.company_id:
                record.imss_registration = record.company_id.imss_registration.id if record.company_id.imss_registration else False
            else:
                record.imss_registration = False

    @api.model
    def write(self, vals):
        for record in self:
            if 'fixed_base_salary' in vals:
                # Crear el registro del historial antes de actualizar el salario
                today = datetime.today().date()
                try:
                    if record.id:
                        print("creando historial")
                        self.env['reclutamiento__kuale.salary_history'].create({
                            'tab_id': record.id,
                            'job_id': record.job_id.id,
                            'company_id': record.company_id.id,
                            'name': record.date_historical, #fecha que se coloco como inicial
                            'end_date': today, #fecha en que dejo de ser valido
                            'daily_contract_salary': record.daily_contract_salary,
                            'fixed_base_salary': record.fixed_base_salary,
                            'variable_base_salary': record.variable_base_salary,
                            'capped_base_salary': record.capped_base_salary,
                            'daily_salary_integrated': record.daily_salary_integrated,
                            'gross_monthly_salary': record.gross_monthly_salary,
                            'capped_net_monthly_salary': record.capped_net_monthly_salary
                        })
                except Exception as e:
                    print("Error Creando historial :", e)
        return super().write(vals)

class CompanyArea(models.Model):
    _name = 'reclutamiento__kuale.company_area'
    _description = 'Áreas'

    name = fields.Char('Nombre', required=True)
    description = fields.Char('Description')


class CostCenter(models.Model):
    _name = 'reclutamiento__kuale.cost_center'
    _description = 'Centros de costos'

    name = fields.Char('Nombre', required=True)
    description = fields.Char('Description')


class RolTab(models.Model):
    _name = 'reclutamiento__kuale.rol_tab'
    _description = 'Rol asignado'

    name = fields.Char('Nombre', required=True)
    description = fields.Char('Description')
    #rol_employee = fields.Many2one('hr.employee.rol', string='Tipo')
    rol_employee_selection = fields.Selection([
        ('lgp','LGP'),
        ('dh', 'DH'),
        ('pxc', 'PXC')
    ], string="Rol")
    groups_ids = fields.Many2many(
        'res.groups', string="Permisos",
        help="Selecciona los permisos que tendrá este rol."
    )

class HierarchicalLevel(models.Model):
    _name = 'reclutamiento__kuale.hierarchical_level'
    _description = 'Nivel jerárquico'

    name = fields.Char('Nombre', required=True)
    description = fields.Char('Description')


class EmployeeType(models.Model):
    _name = 'reclutamiento__kuale.type_employee'
    _description = 'Tipo de empleado'

    name = fields.Char('Nombre', required=True)
    description = fields.Char('Description')


class UnitMeasureUpdate(models.Model):
    _name = 'reclutamiento__kuale.unit_mesure_update'
    _description = 'Unidad de Medida y Actualización (UMA)'

    name = fields.Char('Año', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string="Moneda",
        default=lambda self: self.env.ref('base.MXN').id,
        readonly=True
    )
    daily_value = fields.Monetary('Valor Diario',currency_field='currency_id', required=True)
    monthly_value = fields.Monetary('Valor Mensual',currency_field='currency_id', required=True)
    annual_value = fields.Monetary('Valor Anual',currency_field='currency_id', required=True)
    publication_date = fields.Date('Fecha de publicación')
    source = fields.Char('Fuente')


class SalaryHistory(models.Model):
    _name = 'reclutamiento__kuale.salary_history'
    _description = 'Historial de salarios'

    name = fields.Date('Fecha inicial', required=True)
    end_date = fields.Date('Fecha final', required=True)
    tab_id = fields.Many2one('reclutamiento__kuale.job_tab', string="Tabulador", required=True)
    job_id = fields.Many2one('hr.job', string="Puesto", required=True)
    company_id = fields.Many2one('res.company', string='Empresa', required=True)
    currency_id = fields.Many2one(string="Moneda", related='company_id.currency_id', readonly=True)
    daily_contract_salary = fields.Monetary('Salario diario', currency_field='currency_id')
    fixed_base_salary = fields.Monetary('Salario base de cotización parte fija', currency_field='currency_id')
    variable_base_salary = fields.Monetary('Salario base de cotización parte variable', currency_field='currency_id')
    capped_base_salary = fields.Monetary('Salario base de cotización topado a 25 UMA', currency_field='currency_id')
    daily_salary_integrated = fields.Monetary('Salario diario integrado', currency_field='currency_id')
    gross_monthly_salary = fields.Monetary('Salario mensual bruto', currency_field='currency_id')
    capped_net_monthly_salary = fields.Monetary('Salario mensual neto', currency_field='currency_id')

