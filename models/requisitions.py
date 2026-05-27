import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError

from odoo import models, fields, api


class RequisitionReasons(models.Model):
    _name = 'reclutamiento__kuale.requisition_reasons'
    _description = 'reclutamiento__kuale.requisition_reasons'

    active = fields.Boolean(default=True, readonly=True)
    name = fields.Char('Nombre', required=True, translate=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre del motivo ya existe!"),
    ]


class Shifts(models.Model):
    _name = 'reclutamiento__kuale.shifts'
    _description = 'reclutamiento__kuale.shifts'

    active = fields.Boolean(default=True)
    name = fields.Char('Nombre', required=True, translate=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡El nombre del turno ya existe!"),
    ]


class RequisitionDetails(models.Model):
    _name = "reclutamiento__kuale.requisitions_details"
    _description = "Requisitions Details"
    _order = "id"

    requisition_id = fields.Many2one("reclutamiento__kuale.requisitions", string="Requisicion")
    active = fields.Boolean('Activo', default=True)
    quantity = fields.Integer('Cantidad', required=True, default=1)
    quantity_auth = fields.Integer('Vacantes autorizadas', default=0)
    shift = fields.Many2one('reclutamiento__kuale.shifts', string="Turno", required=True)
    reason = fields.Many2one('reclutamiento__kuale.requisition_reasons', string="Motivo", required=True)
    student = fields.Selection([
        ('yes', 'Si'),
        ('no', 'No')
    ], string="Estudiantes")
    description = fields.Char("Especifique")

    @api.constrains('quantity')
    def _check_campo_entero(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError("El valor del número de vacantes debe ser mayor que cero.")


class Requisitions(models.Model):
    _name = "reclutamiento__kuale.requisitions"
    _description = "Requisitions"
    _order = "id"
    _inherit = ['mail.thread']

    active = fields.Boolean('Activo', default=True)
    sequence = fields.Char('Secuencia', default=lambda self: _('New'), copy=False, readonly=True, tracking=True)
    color = fields.Integer('Color Index', default=0)
    can_authorize = fields.Boolean(compute='_compute_can_authorize')

    @api.depends_context('uid')
    def _compute_can_authorize(self):
        dh_group = self.env.ref('reclutamiento__kuale.group_dh_access', raise_if_not_found=False)
        is_dh = False
        if dh_group:
            self.env.cr.execute(
                "SELECT 1 FROM res_groups_users_rel WHERE uid=%s AND gid=%s",
                (self.env.uid, dh_group.id)
            )
            is_dh = bool(self.env.cr.fetchone())
        can = is_dh or (self.env.uid == 1)
        for record in self:
            record.can_authorize = can

    name = fields.Char('Folio', readonly=True, store=True)
    status_requisition = fields.Char('Estatus', readonly=True, default="New")
    status = fields.Integer('Estatus', default=10)
    # 10= Nuevo,  20 = Pendiente, 30=Autorizado, 40= Publicado, 50=Completado, 60= Rechazado, 70= Cancelado
    last_status = fields.Integer('Último estatus')

    job_id = fields.Many2one('hr.job', 'Puesto de trabajo', check_company=True, domain="[('is_Parent_Job', '=', True)]",
                             required=True)

    no_requisitions = fields.Integer('Cantidad a solicitar', compute="_compute_quantity_requisitions", store=True)
    date_entry = fields.Date('Fecha de ingreso', required=True)
    date_end = fields.Date('Fecha límite')
    inmediate_job_id = fields.Many2one('res.users', 'Solicitante', store=True, readonly=False, required=True)

    company_id = fields.Many2one('res.company', string='Empresa', index=True, default=lambda self: self.env.company,
                                 required=True)
    branch_ids = fields.Many2one('res.company', compute='_compute_branch_id',
                                 domain="[('parent_id', '=', company_id)]", store=True,
                                 readonly=False,
                                 required=True,
                                 ondelete='cascade',
                                 string="Sucursales")

    department_id = fields.Many2one('hr.department', "Departamento", check_company=True, required=True)

    total_employee_current = fields.Integer(compute='_compute_total_employee', string='Plantilla actual', store=True)
    total_employee_absents = fields.Integer(compute='_compute_total_employee_absent', string='Expertos ausentes',
                                            store=True)

    gender = fields.Selection([
        ('male', 'Hombre'),
        ('female', 'Mujer'),
        ('indistinct', 'Indistinto')
    ], string="Género")

    age_id = fields.Many2one('reclutamiento__kuale.age', string='Rango de edad')
    is_age_other = fields.Boolean("Es otra edad", compute='_compute_age_id')
    age_other = fields.Char('Rango de edad (Otro)', translate=True)

    workday_calendar_id = fields.Many2one('resource.calendar', string="Disponibilidad de horario", check_company=True)

    no_requisitions_auth = fields.Integer('Vacantes autorizadas', compute="_compute_quantity_requisitions", store=True)

    details = fields.One2many('reclutamiento__kuale.requisitions_details', 'requisition_id', string="Detalles",
                              required=True)
    reason_vacancy = fields.Many2one('reclutamiento__kuale.requisition_reasons',
                                     string="Motivo/Causa/Justificante de la vacante")
    applicant_ids = fields.One2many('hr.applicant', 'requisition_id', string="Solicitudes")
    application_count = fields.Integer(compute='_compute_application_count', string="Recuento de solicitudes")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "El folio ya existe"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['last_status'] = 10
            vals['status'] = 20
            vals['status_requisition'] = "Pendiente"
            if vals.get('sequence', _('New')) == _('New'):
                vals['sequence'] = self.env['ir.sequence'].next_by_code('reclutamiento__kuale.requisitions')
            company = self.env['res.company'].browse(vals.get('company_id')) or self.env.company
            branch = self.env['res.company'].browse(vals.get('branch_ids')) or self.env.company
            department = self.env['hr.department'].browse(vals.get('department_id')) or self.env.company
            current_year = str(datetime.datetime.now().year)
            folio_seq = (
                company.name[:2] + "-" + branch.name[:3] + "-" +
                current_year + "-" + department.acronym[:3] + "-" + vals['sequence']
            )
            vals['name'] = folio_seq

        records = super(Requisitions, self).create(vals_list)

        for record in records:
            message = f"Se ha creado una nueva requisición con el folio {record.name}."
            record.message_post(body=message, message_type='notification')

        for record in records:
            if record.job_id and record.branch_ids:
                branch_job = self.env['hr.job'].sudo().search([
                    ('name', '=', record.job_id.name),
                    ('company_id', '=', record.branch_ids.id),
                    ('is_Parent_Job', '=', False),
                ], limit=1)

                if not branch_job:
                    new_job = self.env['hr.job'].sudo().create({
                        'name': record.job_id.name,
                        'name_kuale': record.job_id.name_kuale or record.job_id.name,
                        'company_id': record.branch_ids.id,
                        'branch_company_id': record.company_id.id,
                        'department_id': record.department_id.id if record.department_id else False,
                        'is_authorized': False,
                        'is_Parent_Job': False,
                        'from_requisition': True,
                        'website_published': False,
                        'description': record.job_id.description or '',
                        # ── Heredar campos del padre ──
                        'job_position_type': record.job_id.job_position_type,
                        'objective': record.job_id.objective,
                        'justify': record.job_id.justify,
                        'contract_type_id': record.job_id.contract_type_id.id if record.job_id.contract_type_id else False,
                        'contract_type_kuale_id': record.job_id.contract_type_kuale_id.id if record.job_id.contract_type_kuale_id else False,
                        'working_schedule_id': record.job_id.working_schedule_id.id if record.job_id.working_schedule_id else False,
                        'type_workday': record.job_id.type_workday,
                        'workday': record.job_id.workday,
                        'start_time': record.job_id.start_time,
                        'end_time': record.job_id.end_time,
                        'schooling_id': record.job_id.schooling_id.id if record.job_id.schooling_id else False,
                        'age_id': record.job_id.age_id.id if record.job_id.age_id else False,
                        'gender_id': record.job_id.gender_id.id if record.job_id.gender_id else False,
                        'net_base_salary': record.job_id.net_base_salary,
                        'capped_net_salary': record.job_id.capped_net_salary,
                        'show_linkedIn': record.job_id.show_linkedIn,
                        'show_driverLicense': record.job_id.show_driverLicense,
                        'filter_question_id': record.job_id.filter_question_id.id if record.job_id.filter_question_id else False,
                        'recruitment_promo_image': record.job_id.recruitment_promo_image,
                        'website_description': record.job_id.website_description,
                        'job_tab_ids': record.job_id.job_tab_ids.id if record.job_id.job_tab_ids else False,
                    })
                    # ── Copiar Many2many del padre ──
                    if record.job_id.activities_ids:
                        new_job.write({'activities_ids': [(6, 0, record.job_id.activities_ids.ids)]})
                    if record.job_id.experiences_ids:
                        new_job.write({'experiences_ids': [(6, 0, record.job_id.experiences_ids.ids)]})
                    if record.job_id.tool_ids:
                        new_job.write({'tool_ids': [(6, 0, record.job_id.tool_ids.ids)]})
                    if record.job_id.software_ids:
                        new_job.write({'software_ids': [(6, 0, record.job_id.software_ids.ids)]})
                    if record.job_id.competence_ids:
                        new_job.write({'competence_ids': [(6, 0, record.job_id.competence_ids.ids)]})
                    if record.job_id.language_k_ids:
                        new_job.write({'language_k_ids': [(6, 0, record.job_id.language_k_ids.ids)]})
                    if record.job_id.int_rel_ids:
                        new_job.write({'int_rel_ids': [(6, 0, record.job_id.int_rel_ids.ids)]})
                    if record.job_id.ext_rel_ids:
                        new_job.write({'ext_rel_ids': [(6, 0, record.job_id.ext_rel_ids.ids)]})
                    if record.job_id.perf_st_ids:
                        new_job.write({'perf_st_ids': [(6, 0, record.job_id.perf_st_ids.ids)]})
                    if record.job_id.day_ids:
                        new_job.write({'day_ids': [(6, 0, record.job_id.day_ids.ids)]})
                    if record.job_id.days_off_catalog:
                        new_job.write({'days_off_catalog': [(6, 0, record.job_id.days_off_catalog.ids)]})
                    if record.job_id.slide_for_ids:
                        new_job.write({'slide_for_ids': [(6, 0, record.job_id.slide_for_ids.ids)]})
                    if record.job_id.slide_during_ids:
                        new_job.write({'slide_during_ids': [(6, 0, record.job_id.slide_during_ids.ids)]})

                    # Apuntar la requisición al job hijo recién creado
                    record.write({'job_id': new_job.id})
                else:
                    # Ya existe un hijo para esta sucursal
                    branch_job.write({
                        'from_requisition': True,
                        'branch_company_id': record.company_id.id,
                    })
                    # Apuntar la requisición al job hijo existente
                    record.write({'job_id': branch_job.id})
                    authorized_reqs = self.search([
                        ('job_id.name', '=', branch_job.name),
                        ('branch_ids', '=', record.branch_ids.id),
                        ('status', '=', 30),
                        ('id', '!=', record.id),
                    ], limit=1)
                    if not authorized_reqs:
                        branch_job.write({'is_authorized': False})

        return records

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if not default.get('name'):
            default['sequence'] = self.env['ir.sequence'].next_by_code('reclutamiento__kuale.requisitions')
            nameSeq = self.name.rfind("-")
            default['name'] = self.name[:nameSeq + 1] + default['sequence']
        return super(Requisitions, self).copy(default)

    @api.depends('company_id', 'branch_ids', 'department_id', 'sequence')
    def _compute_folio(self):
        for record in self:
            if not record.company_id and not record.branch_ids and not record.department_id:
                record.name = False
            else:
                nameCompany = record.company_id.name
                nameBranch = record.branch_ids.name
                if not record.department_id:
                    record.name = False
                else:
                    nameDepartment = record.department_id.acronym
                    current_year = str(datetime.datetime.now().year)
                    folio = (
                        nameCompany[:2] + "-" + nameBranch[:3] + "-" +
                        current_year + "-" + nameDepartment[:3] + "-" +
                        record.sequence.lstrip('0')
                    )
                    record.name = folio

    @api.depends('company_id')
    def _compute_branch_id(self):
        for record in self:
            if not record.company_id:
                record.branch_ids = False
            else:
                branch = record.company_id.child_ids
                record.branch_ids = branch[0] if branch else False

    @api.depends('age_id')
    def _compute_age_id(self):
        for record in self:
            if not record.age_id:
                record.is_age_other = False
            else:
                if record.age_id.name == "Otro":
                    record.is_age_other = True
                else:
                    record.is_age_other = False

    @api.depends('details.quantity', 'details.quantity_auth')
    def _compute_quantity_requisitions(self):
        for requisition in self:
            requisition.no_requisitions = sum(requisition.details.mapped('quantity'))
            requisition.no_requisitions_auth = sum(requisition.details.mapped('quantity_auth'))

    @api.depends('branch_ids')
    def _compute_total_employee(self):
        for record in self:
            if not record.branch_ids:
                record.total_employee_current = 0
            else:
                company_id = record.company_id.id
                if company_id:
                    emp_data = self.env['hr.employee'].read_group(
                        [('company_id', '=', company_id)],
                        ['company_id'],
                        ['company_id'],
                        lazy=False,
                        orderby='company_id',
                        offset=0,
                        limit=None
                    )
                    result = {company['company_id'][0]: company['__count'] for company in emp_data}
                    record.total_employee_current = result.get(company_id, 0)

    @api.depends('branch_ids')
    def _compute_total_employee_absent(self):
        for record in self:
            if not record.branch_ids:
                record.total_employee_absents = 0
            else:
                company_id = record.branch_ids.id
                if company_id:
                    emp_data = self.env['hr.employee'].read_group(
                        [('company_id', '=', company_id)],
                        ['company_id'],
                        ['company_id'],
                        lazy=False,
                        orderby='company_id',
                        offset=0,
                        limit=None
                    )
                    result = {company['company_id'][0]: company['__count'] for company in emp_data}
                    record.total_employee_absents = result.get(company_id, 0)

    @api.constrains('details')
    def _check_details(self):
        for requisition in self:
            if not requisition.details:
                raise ValidationError("Debes crear al menos una vacante en la sección Vacantes.")

    def authorize_requisition(self):
        dh_group = self.env.ref('reclutamiento__kuale.group_dh_access', raise_if_not_found=False)
        is_dh = False
        if dh_group:
            self.env.cr.execute(
                "SELECT 1 FROM res_groups_users_rel WHERE uid=%s AND gid=%s",
                (self.env.uid, dh_group.id)
            )
            is_dh = bool(self.env.cr.fetchone())
        if not (is_dh or self.env.uid == 1):
            raise AccessError("Solo el equipo de Desarrollo Humano (DH) o el administrador pueden autorizar requisiciones.")
        for requisition in self:
            isvalid = False
            if not requisition.details:
                raise ValidationError("Debes crear al menos una vacante en la sección Vacantes.")
            else:
                if requisition.no_requisitions_auth <= 0:
                    raise ValidationError("Se requiere la aprobación de las vacantes")
                else:
                    isvalid = True

            if isvalid:
                # FIX 3: Buscar SOLO el job hijo (is_Parent_Job=False) de esta sucursal
                # para no autorizar el puesto padre del catálogo por error
                branch_job = self.env['hr.job'].sudo().search([
                    ('name', '=', requisition.job_id.name),
                    ('company_id', '=', requisition.branch_ids.id),
                    ('is_Parent_Job', '=', False),  # ← FIX: excluir puestos padre
                ], limit=1)

                if branch_job:
                    branch_job.no_of_recruitment = (
                        branch_job.no_of_recruitment + requisition.no_requisitions_auth
                    )
                    branch_job.write({'is_authorized': True})
                else:
                    # Fallback: no debería llegar aquí con el flujo correcto
                    requisition.job_id.no_of_recruitment = (
                        requisition.job_id.no_of_recruitment + requisition.no_requisitions_auth
                    )
                    requisition.job_id.write({'is_authorized': True})

                requisition.write({
                    'status': 30,
                    'last_status': 20,
                    'status_requisition': 'Autorizado'
                })

    def refuse_requisition(self):
        for requisition in self:
            last_status = requisition.status
            requisition.write(
                {'status': 60, 'last_status': last_status, 'status_requisition': 'Rechazado'})

    def cancel_requisition(self):
        for requisition in self:
            last_status = requisition.status
            requisition.write(
                {'status': 70, 'last_status': last_status, 'status_requisition': 'Cancelado'})

    def _compute_application_count(self):
        read_group_result = self.env['hr.applicant']._read_group(
            [('requisition_id', 'in', self.ids)], ['requisition_id'], ['__count'])
        result = {job.id: count for job, count in read_group_result}
        for job in self:
            job.application_count = result.get(job.id, 0)