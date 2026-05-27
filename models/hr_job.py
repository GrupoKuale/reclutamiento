from pkg_resources import require

from odoo import fields, models, api
import base64
import string

class hr_job(models.Model):
    _inherit = 'hr.job'

    name_kuale = fields.Char(string='Nombre del puesto (Kuale)', required=True, translate=True)
    city_Job = fields.Many2one('reclutamiento__kuale.city', string='Ciudad')
    detail_branch_job = fields.One2many('reclutamiento__kuale.branch_job', 'job_id', string="Sucursales")
    business_name = fields.Char(string='Razón social', compute="_compute_business_name", readonly=True)

    job_tab_ids = fields.Many2one('reclutamiento__kuale.job_tab', string="Tab")
    subordinate_id = fields.Many2one('res.users', "Subordinados",
                                     domain="[('share', '=', False), ('company_ids', 'in', company_id)]", tracking=True)
    objective = fields.Text(string='Objetivo', translate=True)
    justify = fields.Text(string='Justificación', translate=True)
    administrative = fields.Boolean(string='Administrativa', default=False)

    is_career_path_eligible = fields.Boolean(string='¿Es elegible la trayectoria profesional?', default=False)

    # Estado requisiciones
    is_authorized = fields.Boolean(string='Autorizado', default=False)
    from_requisition = fields.Boolean(string='Creado desde Requisición', default=False, store=True)

    job_position_type = fields.Selection([
        ('Administrative', 'Administrativo'),
        ('Technical', 'Técnico'),
        ('Commercial', 'Comercial'),
        ('Finance', 'Financiero'),
        ('Creative', 'Creativo'),
    ],require=True, string="Tipo de puesto")

    # Bolsa de trabajo
    bolsa_trabajo = fields.Boolean(
        string='Bolsa de trabajo',
        default=False,
        store=True
    )
    
    # Campo para filtrado por sucursales
    branch_company_id = fields.Many2one(
        'res.company',
        string='Sucursal',
        compute='_compute_branch_company_ids',
        store=True,
        readonly=False, 
    )

    # process_details = fields.Text(string='Process Details', translate=True)

    requisition_ids = fields.One2many('reclutamiento__kuale.requisitions', 'job_id', string='Puesto de trabajo')

    recruitment_promo_image = fields.Binary(string='Imagen promocional')

    # Contracts
    trial_period_id = fields.Many2one('reclutamiento__kuale.trial_period', compute='_compute_trial_period_id',
                                      store=True,
                                      domain="[('contract_type_id', '=', contract_type_kuale_id)]", readonly=False,
                                      ondelete='cascade')
    jornada_id = fields.Many2one('reclutamiento__kuale.jornada', compute='_compute_jornada_id',
                                 string="Tipo de contrato",
                                 domain="[('contract_type_id', '=', contract_type_kuale_id)]", store=True,
                                 readonly=False,
                                 ondelete='cascade')
    contract_type_kuale_id = fields.Many2one('reclutamiento__kuale.contract_type', string="Tipo de contrato")
    working_schedule_id = fields.Many2one('resource.calendar',
                                          string='Horario de trabajo',
                                          help='definir horario de trabajo por puesto')

    comments_contract_type = fields.Char(string='Comentarios', compute="_compute_comments_contract_type", readonly=True)

    # Activities
    activities_ids = fields.Many2many('reclutamiento__kuale.activities', 'job_act_rel', 'job_id', 'act_id',
                                      string='Actividades')
    #activities_summary=fields.Text(compute="_compute_activities", default="", store=True)
    #activities_full=fields.Text(compute="_compute_full_activities", default="", store=True)
    # Experience
    experiences_ids = fields.Many2many('reclutamiento__kuale.experience', 'job_exp_rel', 'job_id', 'exp_id',
                                       string='Experiencia')
    experience_activities = fields.Char(string='Experiencia requerida para las actividades', translate=True)
    comments_specifications = fields.Text(string='Comentarios o especificaciones técnicas', translate=True)

    # Tool and knowledge
    tool_ids = fields.Many2many('reclutamiento__kuale.tools_knowledge', 'job_toolknow_rel', 'job_id', 'tool_id',
                                string='Herramientas operativas', domain=[('type', '=', 'tool')])
    software_ids = fields.Many2many('reclutamiento__kuale.tools_knowledge', 'job_software_rel', 'job_id', 'soft_id',
                                    string='Software', domain=[('type', '=', 'software')])

    # Profile
    schooling_id = fields.Many2one('reclutamiento__kuale.schooling', string='Escolaridad')

    age_id = fields.Many2one('reclutamiento__kuale.age', string='Rango de edad')

    gender_id = fields.Many2one('reclutamiento__kuale.gender', string='Género')

    language_k_ids = fields.Many2many('reclutamiento__kuale.language', 'job_language_rel', 'job_id', 'lan_id',
                                      string='Idioma')

    # Competencies
    competence_ids = fields.Many2many('reclutamiento__kuale.competencies', 'job_competencies_rel', 'job_id', 'comp_id',
                                      string='Competencias')

    # Internal and external relations
    int_rel_ids = fields.Many2many('reclutamiento__kuale.internal_relations', 'job_internalrel_rel', 'job_id',
                                   'intrel_id', string='Relaciones internas')
    ext_rel_ids = fields.Many2many('reclutamiento__kuale.external_relations', 'job_externalrel_rel', 'job_id',
                                   'extrel_id', string='Relaciones externas')
    perf_st_ids = fields.Many2many('reclutamiento__kuale.performance_standars', 'job_performancest_rel', 'job_id',
                                   'perfst_id', string='Estándares de rendimiento')
    comments_expetations = fields.Char(string='Comentarios/Expectativas generales', translate=True)
    comments_id = fields.One2many('reclutamiento__kuale.comments_exp', 'job_id',
                                  string="Comentarios/Expectativas generales.")

    # Workday
    type_workday = fields.Selection([
        ('fixed_shift', 'Turno fijo'),
        ('rotating_shift', 'Turno rotativo')
    ], string="Tipo")
    start_time_fixed = fields.Float(string='Horario inicio', store=True)
    end_time_fixed = fields.Float(string='Horario fin', store=True)
    workday = fields.Selection([
        ('diurnal - 8 hours', 'Diurna - 8 horas'),
        ('nocturnal - 7 hours', 'Nocturna - 7 horas'),
        ('mixed - 7:30 hours', 'Mixta - 7:30 horas'),
    ], string="Jornada")
    day_ids = fields.Many2many('reclutamiento__kuale.weekdays', 'job_weekdays_rel', 'job_id', 'day_id', string='Dias')
    start_time = fields.Float(string='Horario inicio', store=True)
    end_time = fields.Float(string='Horario fin', store=True)
    days_off = fields.Selection([
        ('rotating', 'Rotativo'),
        ('monday', 'Domingo'),
    ], string="Días de descanso")
    days_off2 = fields.Many2many('reclutamiento__kuale.weekdays', 'job_days_off_rel', 'job_id', 'day_id',
                                 string="Días de descanso")
    days_off_catalog = fields.Many2many('reclutamiento__kuale.weekdays', 'job_days_off_rel', 'job_id', 'day_id',
                                string="Días de descanso")
    # Child jobs
    parent_id = fields.Many2one('hr.job', string='Parent job', index=True, check_company=True)
    child_ids = fields.One2many('hr.job', 'parent_id', string='Child Jobs')
    parent_path = fields.Char(index=True, unaccent=False)
    is_Parent_Job = fields.Boolean(
        string='Is Parent Job',
        compute='_compute_branch_company_ids',
        store=True,
    )


    # Garments
    products = fields.One2many('reclutamiento__kuale.product_garments', 'job_id', string="Prendas", required=True)

    # Filter questions
    filter_question_id = fields.Many2one(
        'survey.survey', "Encuesta",
        help="Seleccione la encuesta que se realizará en el buscador de empleo que será para uso exclusivo de los reclutadores.")

    # Life and career plan
    slide_for_ids = fields.Many2many('slide.channel', 'job_slfor_rel', 'job_id', 'slfor_id',
                                     string='Capacitaciones Para')
    slide_during_ids = fields.Many2many('slide.channel', 'job_slduring_rel', 'job_id', 'sldur_id',
                                        string='Capacitaciones Durante')
    potential_future_jobs = fields.Many2many(
        'hr.job',
        'hr_job_future_rel',
        'current_job_id',
        'future_job_id',
        string='Puestos a aspirar',
        domain=[('is_Parent_Job', '=', True)]
    )

    # Salary
    net_base_salary = fields.Integer(string="Salario neto base")
    capped_net_salary = fields.Integer(string="Salario neto topado")

    # Descripción de contrato (campo exclusivo para el contrato)
    contract_description = fields.Text(string='Descripción de contrato', translate=True)

    # Anexo del contrato
    annex_file = fields.Binary(string='Archivo de Anexo', attachment=True)
    annex_filename = fields.Char(string='Nombre del archivo de Anexo')

    # Campos a mostrar opcionales
    show_linkedIn = fields.Boolean(default=False, string="Solicitar perfil de LinkedIn")
    show_driverLicense = fields.Boolean(default=False, string="Solicitar Licencia de conducir")

    #Control de etapas
    show_propuesta_contrato = fields.Boolean(
        string='Aplicar etapa Propuesta de contrato',
        default=True,
        store=True
    )

    #Formatos
    formatos_ids = fields.Many2many(
        'reclutamiento__kuale.format_employee',
        'hr_job_format_employee_rel',
        'job_id', 'format_id',
        string='Formatos requeridos',
        domain="[('active', '=', True)]",
    )

    # Filtrado por sucursal
    @api.depends('company_id')
    def _compute_branch_company_ids(self):
        for job in self:
            if job.company_id and job.company_id.parent_id:
                # Es puesto HIJO (sucursal)
                job.branch_company_id = job.company_id.parent_id
                job.is_Parent_Job = False
            else:
                # Es puesto PADRE (empresa raíz)
                job.branch_company_id = False
                job.is_Parent_Job = True

    @api.onchange('job_position_type')
    def _onchange_job_position_type(self):
        if self.job_position_type == 'Administrative':
            self.administrative = True
        else:
            self.administrative = False

    @api.depends('company_id')
    def _compute_business_name(self):
        for job in self:
            bussinnes = job.company_id.business_name
            job.business_name = bussinnes

    @api.depends('branch_ids')
    def _compute_branch(self):
        for job in self:
            branch_address_parts = []

            # Concatenar los diferentes campos de la dirección
            street = job.branch_ids.street
            if street:
                branch_address_parts.append(street)

            street2 = job.branch_ids.street2
            if street2:
                branch_address_parts.append(street2)

            city = job.branch_ids.city
            if city:
                branch_address_parts.append(city)

            state = job.branch_ids.state_id
            if state:
                branch_address_parts.append(state.name)

            zip_address = job.branch_ids.zip
            if zip_address:
                branch_address_parts.append(zip_address)

            country = job.branch_ids.country_id
            if country:
                branch_address_parts.append(country.name)

            job.branch_address = ', '.join(branch_address_parts)

            # Obtener el usuario relacionado
            report_to_user = job.branch_ids.reports_to
            if report_to_user:
                job.branch_report_to = report_to_user.name
            else:
                job.branch_report_to = False

    @api.depends('contract_type_kuale_id')
    def _compute_trial_period_id(self):
        for record in self:
            if record.contract_type_kuale_id:
                record.trial_period_id = record.contract_type_kuale_id.trial_period_ids[
                    0] if record.contract_type_kuale_id.trial_period_ids else False
            else:
                record.trial_period_id = False

    @api.depends('trial_period_id')
    def _compute_jornada_id(self):
        for record in self:
            if not record.trial_period_id:
                record.jornada_id = False
            else:
                jornada = record.contract_type_kuale_id.jornada_ids
                record.jornada_id = jornada[0] if jornada else False

    @api.depends('contract_type_kuale_id')
    def _compute_comments_contract_type(self):
        for contract in self:
            description = contract.contract_type_kuale_id.description
            contract.comments_contract_type = description

    @api.depends('activities_k_id')
    def _compute_knowledge_id(self):
        for record in self:
            if record.activities_k_id:
                record.a_knowledge_id = record.activities_k_id.a_knowledge_ids[
                    0] if record.activities_k_id.a_knowledge_ids else False
            else:
                record.a_knowledge_id = False

    @api.depends('activities_k_id')
    def _compute_knowledge_id(self):
        for record in self:
            if record.activities_k_id:
                record.a_knowledge_id = record.activities_k_id.a_knowledge_ids[
                    0] if record.activities_k_id.a_knowledge_ids else False
            else:
                record.a_knowledge_id = False

    @api.depends('language_k_ids')
    def _compute_level_id(self):
        for record in self:
            if not record.language_k_ids:
                record.level_ids = False
            else:
                level = record.language_k_ids.language_level_ids
                record.level_ids = level[0] if level else False

    # @api.depends('activities_ids')
    # def _compute_activities(self):
    #     for record in self.sudo():
    #         try:
    #             if record.activities_ids:
    #                 summary = ", ".join(str(activity.name) for activity in record.activities_ids)
    #                 record.activities_summary = summary if summary else ""
    #                 print("summary activities:", summary)
    #             else:
    #                 record.activities_summary = ""
    #         except Exception as e:
    #             record.activities_summary = ""
    #             print("ERROR _compute_activities:", str(e))
    #         if not record.activities_summary:
    #             record.activities_summary = ""
    #             print(f"Warning: activities_summary was not set for record {record.id}")
    #
    # @api.depends('activities_ids')
    # def _compute_full_activities(self):
    #     print("_compute_full_activities")
    #     for record in self.sudo():
    #         summary = ""
    #         try:
    #             record.activities_full = summary
    #             for index, activity in enumerate(record.activities_ids):
    #                 inciso = f"{string.ascii_lowercase[index]})"  # Genera a, b, c,
    #                 name = activity.name
    #                 description = activity.description or ""
    #                 summary += f"{inciso} {name}: {description}<br>"
    #             record.activities_full = summary
    #         except Exception as e:
    #             record.activities_full = summary
    #             value = str(e)
    #             print("ERROR _compute_full_activities", value)

    @api.onchange('filter_question_id')
    def _onchange_filter_question_id(self):
        if self.filter_question_id:
            try:
                _ = self.filter_question_id.id
            except AttributeError:
                self.filter_question_id = False
                
    def action_open_requisitions(self):
        return {
            'name': 'Requisiciones',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.requisitions',
            'view_mode': 'kanban,tree,form',
            'domain': [('job_id', '=', self.id)],
            'context': {'default_job_id': self.id},
        }
    
    def write(self, vals):
        print("=== HR_JOB WRITE ===")
        print("VALS KEYS:", list(vals.keys()))
        if 'formatos_ids' in vals:
            print("FORMATOS_IDS ENCONTRADO:", vals['formatos_ids'])
        else:
            print("FORMATOS_IDS NO ESTA EN VALS")

        res = super(hr_job, self).write(vals)

        for record in self:
            if record.is_Parent_Job:
                print("ES PADRE:", record.id, record.name)
                child_jobs = self.env['hr.job'].sudo().search([
                    ('name', '=', record.name),
                    ('is_Parent_Job', '=', False),
                    ('from_requisition', '=', True),
                ])
                print("HIJOS ENCONTRADOS:", child_jobs.ids)

                if not child_jobs:
                    continue

                sync_fields = {
                    'objective', 'justify', 'job_position_type',
                    'contract_type_id', 'contract_type_kuale_id',
                    'working_schedule_id', 'type_workday', 'workday',
                    'start_time', 'end_time', 'schooling_id', 'age_id',
                    'gender_id', 'net_base_salary', 'capped_net_salary',
                    'show_linkedIn', 'show_driverLicense', 'filter_question_id',
                    'recruitment_promo_image', 'website_description',
                    'description', 'name_kuale', 'show_propuesta_contrato',
                    'contract_description','annex_file', 'annex_filename',
                }
                sync_vals = {k: vals[k] for k in vals if k in sync_fields}
                if sync_vals:
                    child_jobs.write(sync_vals)

                m2m_fields = {
                    'activities_ids', 'experiences_ids', 'tool_ids',
                    'software_ids', 'competence_ids', 'language_k_ids',
                    'int_rel_ids', 'ext_rel_ids', 'perf_st_ids',
                    'day_ids', 'days_off_catalog', 'slide_for_ids',
                    'slide_during_ids', 'formatos_ids',
                }
                for field in m2m_fields:
                    if field in vals:
                        print("SINCRONIZANDO M2M:", field, vals[field])
                        for child in child_jobs:
                            child.write({field: vals[field]})
                    else:
                        if field == 'formatos_ids':
                            print("formatos_ids NO esta en vals al sincronizar")
                
                # Sincronizar productos (prendas) - One2many
                if 'products' in vals:
                    for child in child_jobs:
                        child.products.unlink()
                        for product in record.products:
                            self.env['reclutamiento__kuale.product_garments'].create({
                                'job_id': child.id,
                                'product_id': product.product_id.id,
                                'quantity': product.quantity,
                            })
                            
        return res

    def generate_pdf_job(self):
        wizard = self.env['reclutamiento__kuale.job_preview_wizard'].create({
            'job_id': self.id,
            'company_id': self.company_id.id or self.env.company.id,
        })
        return {
            'name': 'Vista previa - %s' % self.name_kuale,
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.job_preview_wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
            'context': {'dialog_size': 'extra-large'},
        }
    
    def generate_format_regulation(self):
        format_employee = self.env['reclutamiento__kuale.format_employee'].search([
            ('job_id', '=', self.id),
            ('type_format', '=', 'regulation')
        ], limit=1)
        if format_employee:
            # Si existe, abrir en modo edición
            return {
                'name': 'Formatos empleados',
                'type': 'ir.actions.act_window',
                'res_model': 'reclutamiento__kuale.format_employee',
                'view_mode': 'form',
                'res_id': format_employee.id,  # Abrir el registro existente
                'view_id': self.env.ref('reclutamiento__kuale.view_format_employee').id,
                'target': 'new',
                'context': {'job_id': self.id, 'type_format': 'regulation'},
            }
        else:
            return {
                'name': 'Formatos empleados',
                'type': 'ir.actions.act_window',
                'res_model': 'reclutamiento__kuale.format_employee',
                'view_mode': 'form',
                'view_id': self.env.ref('reclutamiento__kuale.view_format_employee').id,
                'target': 'new',
                'context': {'job_id': self.id, 'type_format': 'regulation'},
            }

    def generate_format_confidentiality(self):
        format_employee = self.env['reclutamiento__kuale.format_employee'].search([
            ('job_id', '=', self.id),
            ('type_format', '=', 'confidentiality')
        ], limit=1)
        if format_employee:
            # Si existe, abrir en modo edición
            return {
                'name': 'Formatos empleados',
                'type': 'ir.actions.act_window',
                'res_model': 'reclutamiento__kuale.format_employee',
                'view_mode': 'form',
                'res_id': format_employee.id,  # Abrir el registro existente
                'view_id': self.env.ref('reclutamiento__kuale.view_format_employee').id,
                'target': 'new',
                'context': {'job_id': self.id, 'type_format': 'confidentiality'},
            }
        else:
            return {
                'name': 'Formatos empleados',
                'type': 'ir.actions.act_window',
                'res_model': 'reclutamiento__kuale.format_employee',
                'view_mode': 'form',
                'view_id': self.env.ref('reclutamiento__kuale.view_format_employee').id,
                'target': 'new',
                'context': {'job_id': self.id, 'type_format': 'confidentiality'},
            }

    def generate_format_uniform(self):
        format_employee = self.env['reclutamiento__kuale.format_employee'].search([
            ('job_id', '=', self.id),
            ('type_format', '=', 'uniform_voucher')
        ], limit=1)
        if format_employee:
            # Si existe, abrir en modo edición
            return {
                'name': 'Formatos vale de uniforme',
                'type': 'ir.actions.act_window',
                'res_model': 'reclutamiento__kuale.format_employee',
                'view_mode': 'form',
                'res_id': format_employee.id,  # Abrir el registro existente
                'view_id': self.env.ref('reclutamiento__kuale.view_format_employee').id,
                'target': 'new',
                'context': {'job_id': self.id, 'type_format': 'uniform_voucher'},
            }
        else:
            return {
                'name': 'Formatos vale de uniforme',
                'type': 'ir.actions.act_window',
                'res_model': 'reclutamiento__kuale.format_employee',
                'view_mode': 'form',
                'view_id': self.env.ref('reclutamiento__kuale.view_format_employee').id,
                'target': 'new',
                'context': {'job_id': self.id, 'type_format': 'uniform_voucher'},
            }

    def generate_format_promissory(self):
        format_employee = self.env['reclutamiento__kuale.format_employee'].search([
            ('job_id', '=', self.id),
            ('type_format', '=', 'promissory')
        ], limit=1)
        if format_employee:
            # Si existe, abrir en modo edición
            return {
                'name': 'Formato pagaré',
                'type': 'ir.actions.act_window',
                'res_model': 'reclutamiento__kuale.format_employee',
                'view_mode': 'form',
                'res_id': format_employee.id,  # Abrir el registro existente
                'view_id': self.env.ref('reclutamiento__kuale.view_format_employee').id,
                'target': 'new',
                'context': {'job_id': self.id, 'type_format': 'promissory'},
            }
        else:
            return {
                'name': 'Formato pagaré',
                'type': 'ir.actions.act_window',
                'res_model': 'reclutamiento__kuale.format_employee',
                'view_mode': 'form',
                'view_id': self.env.ref('reclutamiento__kuale.view_format_employee').id,
                'target': 'new',
                'context': {'job_id': self.id, 'type_format': 'promissory'},
            }

class Weekdays(models.Model):
    _name = 'reclutamiento__kuale.weekdays'

    name = fields.Char()
    job_ids = fields.Many2many('hr.job', 'job_weekdays_rel', 'day_id', 'job_id', string='Job')
    job_days_off_ids = fields.Many2many('hr.job', 'job_days_off_rel', 'day_id', 'job_id', string='Job Days Off')


class Gender(models.Model):
    _name = 'reclutamiento__kuale.gender'

    name = fields.Char()
    job_ids = fields.Many2many('hr.job', 'job_gender_rel', 'gender_id', 'job_id', string='Job')


class ProductsGarments(models.Model):
    _name = 'reclutamiento__kuale.product_garments'

    # Relation Job
    # job_ids = fields.Many2many('hr.job', 'job_garments_rel', 'garment_id', 'job_id', string='Job')

    job_id = fields.Many2one("hr.job", string="Job")

    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        change_default=True, ondelete='restrict', index='btree_not_null',
        domain="[('product_tmpl_id', '=', product_template_id)]"
    )

    product_template_id = fields.Many2one(
        string="Producto",
        comodel_name='product.template',
        compute='_compute_product_template_id',
        readonly=False,
        required=True,
        search='_search_product_template_id',
        # previously related='product_id.product_tmpl_id'
        # not anymore since the field must be considered editable for product configurator logic
        # without modifying the related product_id when updated.
        domain=[('uniform_type', '=', True)])

    quantity = fields.Integer(string='Cantidad', required=True)

    @api.depends('product_id')
    def _compute_product_template_id(self):
        for line in self:
            line.product_template_id = line.product_id.product_tmpl_id

    def _search_product_template_id(self, operator, value):
        return [('product_id.product_tmpl_id', operator, value)]

    @api.onchange('product_template_id')
    def _compute_product(self):
        for record in self:
            product_id = self.product_template_id.id
            if product_id:
                product = self.env['product.product'].search([('product_tmpl_id', '=', product_id)], limit=1)
                record.product_id = product.id


class Experience(models.Model):
    _name = 'reclutamiento__kuale.experience'
    _description = 'reclutamiento__kuale.experience'

    job_ids = fields.Many2many('hr.job', 'job_exp_rel', 'exp_id', 'job_id', string='Job')

    active = fields.Boolean(default=True)
    name = fields.Char(string='Experiencia requerida para las actividades', required=True)
    comments = fields.Text(string='Comentarios o especificaciones técnicas', translate=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre de la experiencia ya existe!"),
    ]


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    job_slfor_id = fields.Many2many('hr.job', 'job_slfor_rel', 'slfor_id', 'job_id',
                                    string='Formación profesional para',
                                    help="Puestos de trabajo que necesitan de este curso en un futuro.")
    job_slduring_id = fields.Many2many('hr.job', 'job_slduring_rel', 'sldur_id', 'job_id',
                                       string='Formación profesional durante',
                                       help="Puestos de trabajo que necesitan de este curso.")


class BranchJobDetail(models.Model):
    _name = 'reclutamiento__kuale.branch_job'
    _description = 'reclutamiento__kuale.branch_job'
    job_id = fields.Many2one('hr.job')
    company_id = fields.Many2one('res.company', string='Empresa', compute="_get_company")
    branch_ids = fields.Many2one('res.company', compute='_compute_branch_id', string="Sucursal",
                                 domain="[('parent_id', '=', company_id)]", store=True,
                                 readonly=False,
                                 required=False,
                                 ondelete='cascade')
    branch_address = fields.Char(string='Domicilio físico', compute="_compute_branch", readonly=True)
    branch_report_to = fields.Char(string='Reporta a', compute="_compute_branch", readonly=True)
    basic_salary = fields.Integer(string='Salario neto base', required=True)
    capped_salary = fields.Integer(string=' Salario neto topado', required=True)
    subordinate_id = fields.Many2one('res.users', "Subordinados",
                                     domain="[('share', '=', False), ('company_ids', 'in', company_id)]", tracking=True)

    subordinate_quantity = fields.Integer('Subordinados')
    min_employees = fields.Integer(string='Empleados mínimos')
    max_employees = fields.Integer(string='Empleados máximos')
    user_id = fields.Many2one('res.users', "Reclutador",
                              domain="[('share', '=', False), ('company_ids', 'in', company_id)]", tracking=True)
    interviewer_ids = fields.Many2many('res.users', string='Entrevistadores',
                                       domain="[('share', '=', False), ('company_ids', 'in', company_id)]")

    @api.depends('job_id')
    def _get_company(self):
        for record in self:
            record.company_id = record.job_id.company_id

    @api.depends('branch_ids')
    def _compute_branch(self):
        for job in self:
            branch_address_parts = []
            # Concatenar los diferentes campos de la dirección
            street = job.branch_ids.street
            if street:
                branch_address_parts.append(street)

            street2 = job.branch_ids.street2
            if street2:
                branch_address_parts.append(street2)

            city = job.branch_ids.city
            if city:
                branch_address_parts.append(city)

            state = job.branch_ids.state_id
            if state:
                branch_address_parts.append(state.name)

            zip_address = job.branch_ids.zip
            if zip_address:
                branch_address_parts.append(zip_address)

            country = job.branch_ids.country_id
            if country:
                branch_address_parts.append(country.name)

            job.branch_address = ', '.join(branch_address_parts)
            # Obtener el usuario relacionado
            report_to_user = job.branch_ids.reports_to
            if report_to_user:
                job.branch_report_to = report_to_user.name
            else:
                job.branch_report_to = False

    @api.depends('company_id')
    def _compute_branch_id(self):
        for record in self:
            if not record.company_id:
                record.branch_ids = False
            else:
                branch = record.company_id.child_ids
                record.branch_ids = branch[0] if branch else False
