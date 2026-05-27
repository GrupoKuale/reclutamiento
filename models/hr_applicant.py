import json
from datetime import date, timedelta, datetime
import locale
from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError, AccessError
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
from html import unescape
import re
import requests
import random  
import string  
import logging

_logger = logging.getLogger(__name__)

# Define la lista de selección una sola vez
RELATIONSHIP_SELECTION = [
    ('mother', 'Madre'),
    ('father', 'Padre'),
    ('sibling', 'Hermano(a)'),
    ('child', 'Hijo(a)'),
    ('spouse', 'Conyuge'),
    ('other', 'Otro'),
]
ONE_SELECTION = [
    ('yes', 'Si'),
    ('no', 'No')
]
PROGRESS_SELECTION = [
    ('viable', 'Viable'),
    ('no_viable', 'No viable'),
    ('new', 'Nuevo'),
    ('progress', 'En progreso'),
    ('archived', 'Archivado')
]
class hr_applicant(models.Model):
    _inherit = 'hr.applicant'

    # Abandono de proceso
    abandonment_reason = fields.Selection([
        ('school',      'Prioridad a la escuela'),
        ('moving',      'Cambio de domicilio'),
        ('health',      'Enfermedad/Salud'),
        ('better_job',  'Mejor oferta de trabajo'),
        ('wait_time',   'Tiempo de espera demasiado largo'),
        ('ux',          'Página poco amigable al usuario'),
        ('bad_service', 'Mala atención de alguien de la empresa'),
        ('distance',    'Complicación con distancia o transportes al trabajo'),
        ('city_change', 'Cambio de ciudad'),
        ('salary',      'Salario'),
        ('other',       'Otros/Motivos personales'),
    ], string='Motivo de abandono')

    abandonment_comment = fields.Text(string='Comentario de abandono')
    abandoned = fields.Boolean(string='Abandonó el proceso', default=False)
    hidden_by_applicant = fields.Boolean(string='Oculto por el aplicante', default=False)
    abandonment_display = fields.Char(string='Motivo abandono', compute='_compute_abandonment_display')
    status_with_reason = fields.Char(string='Estado', compute='_compute_status_with_reason')
    
    lives_with = fields.Selection([
        ('parents', 'Padres'),
        ('mother', 'Madre'),
        ('father', 'Padre'),
        ('grandparents', 'Abuelos'),
        ('spouse', 'Cónyuge'),
        ('alone', 'Solo'),
        ('roommates', 'Compañero de cuarto'),
        ('other', 'Otro'),
    ], string='Vive con')

    lives_with_other = fields.Char(string='Especifique con quién vive')
    has_family_working_with_us = fields.Selection([
        ('yes', 'Sí'),
        ('no', 'No'),
    ], string="¿Tiene familiares trabajando con nosotros?", default='no', required=True)
    children = fields.Boolean(string='¿Tiene hijos?')
    number_children = fields.Integer(string='Número de hijos')
    family_worker_name = fields.Char(string="Nombre del familiar", required=False)
    date_applicant = fields.Datetime(string="Fecha en que aplicó")
    days_elapsed = fields.Integer(string="Dias que han transcurrido",compute='_compute_days_elapsed')
    # Puesto
    position_name = fields.Char(string='Puesto', readonly=True)
    # Empresa
    company_name = fields.Char(string='Empresa', readonly=True)
    # Sucursal
    branch = fields.Char(string='Sucursal', readonly=True, compute="_computeBranch")
    # Requisition - sutituir por el Branch
    requisition_id = fields.Many2one("reclutamiento__kuale.requisitions", string="Requisicion")
    # ¿Cómo te enteraste de la vacante?
    about_vacancy = fields.Selection([
        ('periodico',  'Periódico'),
        ('friendship', 'Amistad'),
        ('initiative', 'Iniciativa propia'),
        ('other',      'Otro'),
    ], string='¿Cómo te enteraste de la vacante?', required=True)
    # Otra razon-especificar
    other_reason = fields.Char(string='Otro (especifique)')
    # CURP
    curp = fields.Char(string='CURP', required=True, store=True)
    # ¿Has laborado anteriormente con nosotros?
    previous_experience = fields.Selection(ONE_SELECTION, string='Ha laborado con nosotros')
    start_job = fields.Date(string='Fecha en que puede empezar')
    # full_name = fields.Char(string='Fullname')
    # Apellido paterno
    last_name = fields.Char(string='Primer apellido', required=True)
    # Apellido materno
    last_name2 = fields.Char(string='Segundo apellido')
    # Teléfono celular 2
    phone_number = fields.Char(string='Teléfono celular 2', size=10, required=False)
    job_tab_id = fields.Many2one(
        related='job_id.job_tab_ids',
        string="Tabulador",
        readonly=True,
        store=True
    )
    # Fecha de Nacimiento
    birthdate = fields.Date(string='Fecha de Nacimiento', default=fields.Date.context_today, required=True)
    # Lugar de nacimiento
    birthplace_select = fields.Many2one('reclutamiento__kuale.city', string='Lugar de nacimiento')

    # Entidad federativa de nacimiento
    state_birth_Select = fields.Many2one('reclutamiento__kuale.city', string='Entidad federativa de nacimiento')
    # Edad
    age = fields.Integer(string='Edad', readonly=True, compute='_compute_age')
    #Fecha en que mpuede empezar
    start_date = fields.Date(string='Fecha en que puede empezar')
    type_road = fields.Selection([
        ('calle', 'Calle'),
        ('ampliacion', 'Ampliación'),
        ('avenida', 'Avenida'),
        ('callejon', 'Callejón'),
        ('andador', 'Andador'),
        ('cerrada', 'Cerrada'),
        ('privada', 'Privada'),
        ('calzada', 'Calzada')
    ], string='Tipo de vía', required = True)
    # Genero
    gender = fields.Selection([
        ('male',       'Masculino'),
        ('female',     'Femenino'),
        ('non_binary', 'No binario'),
    ], string='Genero', compute='_compute_gender', store=True, readonly=True)
    # Escolaridad
    scholarship = fields.Selection([
        ('ninguno', 'Ninguno'),
        ('preescolar', 'Preescolar'),
        ('primaria', 'Primaria'),
        ('secundaria', 'Secundaria'),
        ('bachillerato', 'Bachillerato'),
        ('licenciatura', 'Licenciatura'),
        ('posgrado', 'Posgrado')
    ], string='Ultimo grado de estudios', default='ninguno', required=True)
    scholarship_Related = fields.Many2one(
        'reclutamiento__kuale.schooling',
        string='Último grado de estudios',
        required=True
    )
    specify_career = fields.Char(string="Especifico")
    other_scholarship = fields.Char(string='Otro')
    # ¿Estudia actualmente?
    is_studying = fields.Selection(ONE_SELECTION, string='Estudia actualmente', default='no', required=True)
    academic_situation = fields.Selection([
        ('estudiante', 'Estudiante'),
        ('graduado', 'Graduado'),
        ('incompleto', 'Incompleto'),
    ], string='Situación académica')
    school_name = fields.Char(string='Escuela o instituto')
    career = fields.Char(string='Carrera o especialidad')
    graduation_year = fields.Integer(string='Año de egreso')
    #Otros estudios
    other_studies_ids = fields.One2many('hr.applicant.other_studies','applicant_id', string="Otros estudios")
    #Nombre de otros estudios carrera
    other_career = fields.Char(string='Carrera o especialidad')
    # Horario, depends='is_studying'
    schedule_student = fields.One2many('reclutamiento__kuale.schedule_student', 'applicant_id',
                                         string="Horario de estudiante")
    # Carrera , depends='is_studying'
    current_degree = fields.Char(string='Carrera en curso',
                                 required=False)
    #Conocimientos
    knowledge_applicant = fields.Char(string="Nombre del conocimiento")
    knowledge_experience = fields.Many2one(
        'reclutamiento__kuale.knowledge_experience',
        string='Experiencia'
    )
    language_id = fields.Many2one(
        'reclutamiento__kuale.language',
        string='Idioma'
    )
    level_id = fields.Many2one(
        'reclutamiento__kuale.language_level',
        string='Nivel'
    )
    knowledge_certification = fields.Char(string="Tiene alguna certificación")
    #Herramientas
    tool_applicant = fields.Char(string="Nombre de la herramienta")
    tool_experience = fields.Many2one(
        'reclutamiento__kuale.knowledge_experience',
        string='Experiencia'
    )
    tool_certification = fields.Char(string="Tiene alguna certificación")
    # Conocimientos y Herramientas (tabla)
    knowledge_ids = fields.One2many(
        'reclutamiento__kuale.applicant_knowledge',
        'applicant_id',
        string='Conocimientos y Herramientas'
    )
    # Idiomas (tabla)
    language_ids = fields.One2many(
        'reclutamiento__kuale.applicant_language',
        'applicant_id',
        string='Idiomas'
    )
    
    #Actividades
    abilities = fields.Char(string="Actividades")
    #Competencias
    competencies_ids = fields.Many2many('reclutamiento__kuale.competencies', string="Competencias")
    ability_ids = fields.Many2many('hr.skill.type', string="Otra habilidad o competencia")

    #Disponibilidad
    preferred_time = fields.Char(string="Horario que más te convenga")
    can_travel = fields.Boolean(string="¿Puede viajar?")
    can_move = fields.Boolean(string="¿Puedes radicar en otra entidad?")
    #Salario
    desired_monthly_salary = fields.Float(string="Salario mensual deseado")
    actual_benefits = fields.Text(string="Prestaciones que percibe en su trabajo actual")
    # Formas de identificación
    has_ine = fields.Selection(ONE_SELECTION, string='¿Cuentas con INE vigente?', required=True)
    # ,required=lambda self: (self.has_ine == 'yes')[1] if self.has_ine else False
    ine_document = fields.Binary(string='Adjuntar archivo INE')
    ine_validity = fields.Char(string="Vigencia INE")
    identification_options_ids = fields.Many2many('reclutamiento__kuale.identification_option', string="Documentos de Identificación")
    # Domicilio Actual
    current_address = fields.Char(string='Calle', required=True)
    exterior_number = fields.Char(string='No. Exterior', required=True)
    interior_number = fields.Char(string='No. Interior', required=False)
    colony = fields.Char(string='Colonia', required=True)
    municipality = fields.Char(string='Municipio', required=True)
    state = fields.Char(string='Estado', required=True)
    full_address = fields.Char(string='Domicilio actual', required=True, compute='_compute_address')
    # Codigo postal
    postal_code = fields.Char(string='Codigo postal', size=5, help='Only 5 digits allowed.', required=True)

    postal_code_id = fields.Many2one('reclutamiento__kuale.city', string='Código Postal',domain="[('code', '!=', '')]")
    state_id = fields.Many2one('reclutamiento__kuale.city', string='Estado', domain="[('id', 'in', allowed_state)]")
    municipality_id = fields.Many2one('reclutamiento__kuale.city', string='Municipio',domain="[('id', 'in', allowed_municipality)]")
    colony_id=fields.Many2one('reclutamiento__kuale.city', string='Colonia',domain="[('id', 'in', allowed_colony)]")

    # NSS
    has_social_security = fields.Selection(ONE_SELECTION, string='Cuenta con Número de Seguridad Social', required=True)
    # required=lambda self: (self.has_social_security == 'yes')[1] if self.has_social_security else False
    social_security_number = fields.Char(string='Número de Seguridad Social')
    nss_files = fields.One2many('multiples_files', 'partner_id', string='NSS Files')
    # RFC
    has_rfc = fields.Selection(ONE_SELECTION, string='Tiene RFC', required=True)
    # required=lambda self: (self.has_rfc == 'yes')[1] if self.has_rfc else False
    rfc_number = fields.Char(string='RFC', size=13, default="")
    rfc_files = fields.One2many('multiples_files', 'partner_id', string='RFC Files')
    # Licencia de manejo
    has_driver_license = fields.Selection(ONE_SELECTION, string='Tiene licencia de manejo')
    driver_license_number = fields.Char(string=' Licencia de manejo')
    driver_license_validity = fields.Date(string='Vigencia de licencia de manejo', default=fields.Date.context_today)
    driver_files = fields.One2many('multiples_files', 'partner_id', string='Adjuntar archivo Licencia de Manejo')
    # Experiencia laboral
    has_experience = fields.Selection(ONE_SELECTION, string='Experiencia laboral actual/anterior', default='no')
    experiencies_ids = fields.One2many('hr.applicant.experience', 'applicant_id', string="Experiencia laboral")
    # Adjuntar complementos según perfil
    is_minor = fields.Boolean(string='', default=False)
    # en caso de ser menor adjuntar ine tutor legal
    attachments = fields.One2many('job.application.attachment', 'application_id', string='Attachments')
    # , required=lambda self: self.is_minor
    ineTutor_document = fields.Binary(string='INE Document')
    # Terminos y condiciones
    terms_conditions = fields.Boolean(string='', default=False, required=True)
    # ADICIONALES
    marital_status = fields.Selection([
        ('single', 'Soltero'),
        ('married', 'Casado'),
        ('cohabitant', 'Unión libre'),
        ('widower', 'Viudo'),
        ('divorced', 'Divorciado')
    ], string='Estado Civil')
    nationality = fields.Selection([
        ('mexican', 'Mexicana'),
        ('other', 'Otra')
    ], string='Nacionalidad')
    other_nationality = fields.Char(string='Nacionalidad')
    desk_phone = fields.Char(string='Teléfono Fijo')
    fiscal_address = fields.Char(string='Calle')
    full_fiscal_address = fields.Char(string='Domicilio Fiscal', required=False, compute='_compute_fiscal_address')
    exterior_number_fiscal = fields.Char(string='No. Exterior', required=False)
    interior_number_fiscal = fields.Char(string='No. Interior', required=False)
    colony_fiscal = fields.Char(string='Colonia',required=False)
    municipality_fiscal = fields.Char(string='Municipio',required=False)
    state_fiscal = fields.Char(string='Estado',required=False)
    postal_code_fiscal = fields.Char(string='Código Postal', size=5, help='Only 5 digits allowed.', required=True)
    between_streets = fields.Text(string='Entre Calle')
    between_street2 = fields.Text(string='Y calle')
    additional_ref= fields.Char(string='Referencias adicionales')
    address_details = fields.Text(string='Características del domicilio')
    clothing_size = fields.One2many('hr.applicant.product', 'applicant_id', string="Talla Uniforme")
    bank_account_ids = fields.One2many('bank.account', 'applicant_id', string="Cuentas")
    beneficiaries_ids = fields.One2many('hr.applicant.beneficiary', 'applicant_id', string="Beneficiarios")
    know_clinic = fields.Selection(ONE_SELECTION, string='Do you know which IMSS clinic corresponds to you?')
    imss_clinic = fields.Many2one(
        'reclutamiento__kuale.clinic',
        string='Clinica'
    )
    medical_unity = fields.Char(string='Unidad Medica Familiar')
    blood_type = fields.Selection([
        ('a_p', 'A+'),
        ('a_n', 'A-'),
        ('b_p', 'B+'),
        ('b_n', 'B-'),
        ('ab_p', 'AB+'),
        ('ab_n', 'AB-'),
        ('o_p', 'O+'),
        ('o_n', 'O-')
    ], string='Tipo de sangre')
    has_allergy = fields.Selection(ONE_SELECTION, string='¿Eres alérgico a algún medicamento/alimento?', required=True,
                                   default='no')
    allergy = fields.Char(string='¿Cuál alergia padece?')
    has_medical_tx = fields.Selection(ONE_SELECTION, string='¿Recibe algún tratamiento médico?', required=True,
                                      default='no')
    medical_tx = fields.Char(string='¿Qué tratamiento recibe?')
    emergency_contacts = fields.One2many('hr.applicant.emergency', 'applicant_id', string="Contactos de emergencia")
    has_chronic_disease = fields.Selection(ONE_SELECTION, string='¿Padeces de alguna enfermedad crónica?',
                                           required=True,
                                           default='no')
    chronic_disease = fields.Char(string='¿Cuál enfermedad crónica?')
    mother_name = fields.Char(string="Nombre de la madre")
    father_name = fields.Char(string="Nombre del padre")
    # REINGRESO
    rehired = fields.Boolean(string='Recontratar', default=False)
    re_company = fields.Char(string='Empresa')
    re_branch = fields.Char(string='Sucursal')
    re_boss = fields.Char(string='Jefe inmediato')
    re_date = fields.Date(string='Fecha renuncia')
    re_lastDay = fields.Date(string='Último día laborado')
    termination_Date = fields.Date(string='Fecha finiquito')
    re_reason = fields.Char(string='Motivo de baja')
    re_comments = fields.Text(string='Comentarios')
    status_stage_id = fields.Integer(string='Status', compute='_compute_stage_id')
    is_hired_stage = fields.Boolean(string='Etapa contratación', compute='_compute_is_hired_stage', store=False)
    #
    process = fields.Selection(PROGRESS_SELECTION, default='progress',string="Progreso")
    color_process = fields.Integer(compute='_compute_color')
    pre_hired=fields.Boolean(default=False)
    resend_complement=fields.Boolean(default=False, compute='_resend_complement')
    home_work_time = fields.Char(string="Tiempo de traslado casa - trabajo")
    identity_document = fields.One2many('reclutamiento__kuale.documents_applicant', 'applicant_id', string="Documentos de identidad")
    related_records = fields.One2many('hr.applicant',  compute='_compute_related_records',  string="Solicitudes relacionadas")
    stage_history_ids = fields.One2many('hr.applicant.stage_history', 'applicant_id', string="Timer")
    allowed_state = fields.Many2many(
        'reclutamiento__kuale.city', compute='_compute_allowed_state'
    )
    allowed_municipality= fields.Many2many(
        'reclutamiento__kuale.city', compute='_compute_allowed_municipality'
    )
    allowed_colony = fields.Many2many(
        'reclutamiento__kuale.city', compute='_compute_allowed_colony'
    )
    duration_actual = fields.Char(string="Duración Actual", compute='_compute_duration_actual', store=False)
    check_id = fields.Boolean(default=False)
    stage_id_aux = fields.Many2one('hr.recruitment.stage', string="Etapa",
                                   domain=[('visualize_form', '=', True)], compute='_compute_stage_id_aux', store=True)
    allowed_stage_ids = fields.Many2many(
        'hr.recruitment.stage',
        string="Allowed Stages",
        compute='_compute_allowed_stage_ids'
    )
    body_temp = fields.Html(
        'Cuerpo del formato dinamico', render_engine='qweb', render_options={'post_process': True},
        prefetch=True, translate=True, sanitize=False)
    actual_date = fields.Date('Fecha actual')
    is_bachelor_degree = fields.Boolean(string="Licenciatura", compute="_compute_is_bachelor_degree")
    #Carta recomendacion
    recommendation_letter = fields.Binary(string='Carta de recomendación')
    #Recibir ofertas
    receive_offer_whatsapp = fields.Boolean(string="Whatsapp")
    receive_offer_call = fields.Boolean(string="Llamada")
    receive_offer_email = fields.Boolean(string="Correo electrónico")
    facebook_profile = fields.Char(string="Facebook")
    other_network_profile = fields.Char(string="Otra red")
    #Bolsa de trabajo
    from_bolsa_trabajo = fields.Boolean(
        string='Bolsa de trabajo',
        default=False,
        store=True
    )
    # Verificacion de estados para crear empleado
    check_id_verified = fields.Boolean(string='Check ID verificado', default=False, store=True)
    huellas_verified = fields.Boolean(string='Huellas verificadas', default=False, store=True)
    formatos_verified = fields.Boolean(string='Formatos completados', default=False, store=True)
    check_id_opened = fields.Boolean(string='Check ID abierto', default=False, store=True)
    applicant_photo = fields.Binary(string='Foto del candidato', attachment=True)

    documentacion_verified = fields.Boolean(
        string='Documentación verificada',
        compute='_compute_documentacion_verified',
        store=True,
    )

    documentation_ids = fields.One2many(
        'hr.applicant.documentation', 'applicant_id',
        string='Documentación de contratación'
    )

    company_parent_name = fields.Char(
        string='Empresa padre',
        compute='_compute_company_parent_name',
        store=False
    )

    contract_start_date = fields.Date(string='Fecha de inicio de contrato')

   #Direccion maps
    map_iframe = fields.Html(string='Mapa', compute='_compute_map_iframe', sanitize=False)

    @api.depends('full_address')
    def _compute_map_iframe(self):
        import urllib.parse
        for rec in self:
            # Construir dirección limpia
            ext = str(rec.exterior_number).strip() if rec.exterior_number else ''
            # Quitar exterior si es solo 1 carácter (letra suelta como 'E', 'S', etc.)
            if len(ext) <= 1:
                ext = ''
            interior = str(rec.interior_number).strip() if rec.interior_number else ''
            if interior in ('S/N', 'False', 'false', '0', 'N/A') or len(interior) <= 1:
                interior = ''
            parts = [
                rec.current_address or '',
                ext,
                interior,
                rec.colony or '',
                rec.municipality or '',
                rec.state or '',
                rec.postal_code or '',
            ]
            clean_address = ', '.join(p for p in parts if p.strip())
            if clean_address:
                addr = urllib.parse.quote(clean_address)
                rec.map_iframe = f'<div style="width:100%;height:400px;overflow:hidden;"><iframe src="https://maps.google.com/maps?q={addr}&output=embed&hl=es&z=16&iwloc=B" width="100%" height="400" style="border:0;display:block;" allowfullscreen="" loading="lazy"></iframe></div>'
            else:
                rec.map_iframe = '<div style="width:100%;height:400px;overflow:hidden;"><iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3692.6498097818594!2d-97.8658576246244!3d22.253361844594984!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x85d7f9f04df1cbe3%3A0xe22335de8907e56f!2sOficinas%20Grupo%20Kuale!5e0!3m2!1ses-419!2smx!4v1729800637591!5m2!1ses-419!2smx" width="100%" height="400" style="border:0;display:block;" allowfullscreen="" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></div>'
    
    @api.model
    def _convert_to_write(self, values):
        if 'from_bolsa_trabajo' in values:
            raw = values['from_bolsa_trabajo']
            if isinstance(raw, str):
                values['from_bolsa_trabajo'] = raw.lower() in ('true', '1', 'yes')
        return super()._convert_to_write(values)
    
    @api.depends('documentation_ids.state')
    def _compute_documentacion_verified(self):
        for rec in self:
            docs = rec.documentation_ids
            if not docs:
                rec.documentacion_verified = False
            else:
                rec.documentacion_verified = all(
                    d.state == 'confirmed' for d in docs
                )
    
    @api.depends('company_id')
    def _compute_company_parent_name(self):
        for rec in self:
            company = rec.company_id
            if company and company.parent_id:
                rec.company_parent_name = company.parent_id.name
            else:
                rec.company_parent_name = company.name if company else ''
                
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'from_bolsa_trabajo' in vals:
                raw = vals['from_bolsa_trabajo']
                vals['from_bolsa_trabajo'] = str(raw).lower() in ('true', '1', 'yes')
        record = super(hr_applicant, self).create(vals_list)
        record.write({'date_applicant': str(date.today())})
        print("pre record.stage_id")
        if record.stage_id:
            print("record.stage_id",record.stage_id)
            record.stage_history_ids.create({
                'applicant_id': record.id,
                'stage_id': record.stage_id.id,
                'start_time': fields.Datetime.now(),
            })
        if record.identity_document:
            print("hay documentos identity_document",record.identity_document)
            self.env['ir.attachment'].create({
                'name': 'DocumentoIdentidad.pdf',
                'type': 'binary',
                'datas': record.identity_document.doc_data,
                'res_model': 'hr.applicant',
                'res_id': record.id,
                'mimetype': 'application/pdf',
            })
        if record.ine_document:
            print("hay documento INE")
            self.env['ir.attachment'].create({
                'name': 'INE.pdf',
                'type': 'binary',
                'datas': record.ine_document,
                'res_model': 'hr.applicant',
                'res_id': record.id,
                'mimetype': 'application/pdf',
            })
        # Detectar si viene de bolsa de trabajo
        try:
            pass  
        except Exception as e:
            print("Error detectando bolsa_trabajo:", e)
        try:
            archived_applicant = self.env['hr.applicant'].search(
                [('application_status', '=', 'archived'), ('curp', '=', record.curp), ('job_id', '=', record.job_id.id)])
            print('archived_applicant', archived_applicant)
            if archived_applicant:
                print('Empleado archivado')
                record.write({'rehired': True})
            else:
                record.write({'rehired': False})
            users_applicant = self.env['hr.applicant'].search([('curp', '=', record.curp), ('job_id', '=', record.job_id.id)])
            print("users_applicant",users_applicant)
            if users_applicant:
                print('Ya existe aplicante con la misma CURP ')
                company = self.env['res.company'].search([('name', '=', record.company_name)])
                print('company', company)
                employees_noti = self.env['hr.employee'].search(
                    [('rol_employee_selection', '=', 'lgp'), ('company_id', '=', company.id)])
                print('employees_noti', employees_noti)
                message = f"Ya existe aplicante con la misma CURP: "+record.curp +" para la empresa: "+record.company_name+" en el puesto de trabajo:"+record.job_id.name
                if employees_noti:
                    mail_values = {
                        'subject': 'Aplicante duplicada',
                        'body_html': message,
                        'email_to': employees_noti.work_email
                    }
                    mail = self.env['mail.mail'].create(mail_values)
                    mail.send()
        except Exception as e:
            print("Error Creando aplicante :", e)
        return record

    def write(self, vals):
        if self.env.context.get('_writing_hr_applicant'):
            return super(hr_applicant, self).write(vals)
        
        self = self.with_context(_writing_hr_applicant=True)
        
        if 'stage_id' in vals:
            user = self.env.user
            if user.has_group('reclutamiento__kuale.group_dh_access') and not user._is_superuser():
                raise AccessError(
                    "El equipo de Desarrollo Humano (DH) solo puede consultar postulaciones, "
                    "no tiene permiso para mover candidatos entre etapas."
                )
            print("stage_id in vals")
            print("=== WRITE CON STAGE_ID ===", self.ids)
            import traceback
            traceback.print_stack()
            if self.stage_history_ids:
                self.stage_history_ids[-1].close_stage()
            self.stage_history_ids.create({
                'applicant_id': self.id,
                'stage_id': vals.get('stage_id'),
                'start_time': fields.Datetime.now(),
            })
            
            new_stage = self.env['hr.recruitment.stage'].browse(vals['stage_id'])

            # ── Inicializar documentación al llegar a Proceso de contratación ──
            if new_stage.sequence == 7:
                try:
                    for rec in self:
                        print(f"Inicializando docs para applicant {rec.id}")
                        self.env['hr.applicant.documentation'].init_docs_for_applicant(rec.id)
                        print(f"Docs inicializados OK para {rec.id}")
                except Exception as e:
                    print(f"ERROR inicializando documentación: {e}")
                    import traceback
                    traceback.print_exc()

            if new_stage.name == 'Segunda entrevista':
                for applicant in self:
                    existing = self.env['vigency_complement'].sudo().search(
                        [('applicant_id', '=', applicant.id)], limit=1
                    )
                    if not existing:
                        import random, string
                        token = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                        try:
                            self.env['vigency_complement'].sudo().create({
                                'applicant_id': applicant.id,
                                'token': token,
                                'vigency': fields.Datetime.now(),
                            })
                            print(f"Token complemento generado para applicant {applicant.id}: {token}")
                        except Exception as e:
                            print("Error al crear vigency_complement:", e)
        
        # ── Crear adjuntos para documentos que llegan desde el formulario ──
        docs_to_attach = [
            ('ine_document',          'INE.pdf'),
            ('recommendation_letter', 'carta_recomendacion.pdf'),
        ]
        for field_name, attach_name in docs_to_attach:
            if field_name in vals and vals.get(field_name):
                self.env['ir.attachment'].create({
                    'name':      attach_name,
                    'type':      'binary',
                    'datas':     vals.get(field_name),
                    'res_model': 'hr.applicant',
                    'res_id':    self.id,
                    'mimetype':  'application/pdf',
                })
        
        print("fin editado")
        return super(hr_applicant, self).write(vals)

    def _resend_complement(self):
        for record in self:
            existing_record = self.env['vigency_complement'].sudo().search([('applicant_id', '=', self.id)], limit=1)
            if existing_record:
                # Obtener la fecha de vigency
                vigency_date = fields.Datetime.from_string(existing_record.vigency)
                current_date = fields.Datetime.from_string(fields.Datetime.now())
                # Comparar si han pasado más de 7 días
                if current_date > vigency_date + timedelta(days=7):
                    record.resend_complement=True
                else:
                    record.resend_complement = False
            else:
                record.resend_complement = False

    @api.depends('requisition_id')
    def _computeBranch(self):
        for record in self:
            req = record.requisition_id
            record.branch = str(req.branch_ids.name)+", "
            for detail in req.details:
                record.branch = record.branch + str(detail.shift.name)+"; "

    @api.depends('process')
    def _compute_color(self):
        for record in self:
            if record.process == 'new':
                record.color_process = 7 #Grey
            elif record.process == 'viable':
                record.color_process = 10 #Green
            elif record.process == 'no_viable':
                record.color_process = 1 #Red
            else:
                record.color_process = 3 #Yellow

    def update_garments(self):
        if self.job_id:
            job_products = self.job_id.products.mapped('product_template_id')
            applicant_products = self.clothing_size.mapped('product_template_id')
            missing_products = job_products - applicant_products
            product_list = []
            for product_id in missing_products.ids:
                product = self.env['product.product'].search([('product_tmpl_id', '=', product_id)], limit=1)
                product_list.append((0, 0, {
                    'applicant_id': self.id,
                    'quantity': 1,
                    'product_id': product.id,
                    'product_template_id': product_id,
                    'job_id': self.job_id.id
                }))
            self.write({'clothing_size': product_list})

    @api.depends('date_applicant')
    def _compute_days_elapsed(self):
        print("calculando _compute_days_elapsed")
        for record in self:
            if record.date_applicant:
                # Calcular la diferencia entre la fecha actual y la fecha en que aplicó
                now = datetime.now()
                days_difference = (now - record.date_applicant).days
                record.days_elapsed = days_difference
            else:
                record.days_elapsed = 0

    @api.depends('current_address', 'exterior_number', 'interior_number', 'colony', 'municipality', 'state',
                 'postal_code')
    def _compute_address(self):
        for record in self:
            record.full_address = ", ".join(filter(None, [
                record.current_address,
                str(record.exterior_number),
                str(record.interior_number),
                record.colony,
                record.municipality,
                record.state,
                record.postal_code
            ]))

    @api.depends('fiscal_address', 'exterior_number_fiscal', 'interior_number_fiscal', 'colony_fiscal',
                 'municipality_fiscal', 'state_fiscal',
                 'postal_code_fiscal')
    def _compute_fiscal_address(self):
        for record in self:
            record.full_fiscal_address = ", ".join(filter(None, [
                record.fiscal_address,
                str(record.exterior_number_fiscal),
                str(record.interior_number_fiscal),
                record.colony_fiscal,
                record.municipality_fiscal,
                record.state_fiscal,
                record.postal_code_fiscal
            ]))

    @api.onchange('stage_id')
    def _change_stage_id(self):
        for record in self:
            print("cambio a: ",record.stage_id)

    @api.depends('stage_id')
    def _compute_stage_id_aux(self):
        for record in self:
            stage = self.env['hr.recruitment.stage'].browse([record.stage_id.id])
            print("STAGE", stage)
            print(" stage.visualize_form",  stage.visualize_form)
            if stage.visualize_form:
                record.stage_id_aux = stage.id
            else:
                record.stage_id_aux = 1
            print("record.stage_id_aux", record.stage_id_aux)

    @api.depends('stage_id')
    def _compute_allowed_stage_ids(self):
        user = self.env.user
        Stage = self.env['hr.recruitment.stage']

        is_guia_gen = user.has_group('reclutamiento__kuale.group_guias_generales')
        is_guia_for = user.has_group('reclutamiento__kuale.group_guias_foraneos')
        is_dh = user.has_group('reclutamiento__kuale.group_dh_access') and not user._is_superuser()

        if is_dh:
            # DH solo puede ver, no mover etapas
            allowed = Stage.browse([])
        elif is_guia_gen:
            # Solo Primera entrevista y Segunda entrevista (filtrar por nombre, sequence duplicado)
            allowed = Stage.search([
                ('name', 'in', ['Primera entrevista', 'First Interview',
                                'Segunda entrevista', 'Second Interview'])
            ])
        elif is_guia_for:
            # Todas las etapas excepto Nuevo y Calificación inicial
            allowed = Stage.search([
                ('name', 'not in', ['Nuevo', 'New',
                                    'Calificación inicial', 'Initial Qualification'])
            ])
        else:
            # LGP y demás: todas las etapas visibles
            allowed = Stage.search([('visualize_form', '=', True)])

        for record in self:
            record.allowed_stage_ids = allowed

    def get_stage_ids_allowed(self):
        user = self.env.user
        Stage = self.env['hr.recruitment.stage']

        is_guia_gen = user.has_group('reclutamiento__kuale.group_guias_generales')
        is_guia_for = user.has_group('reclutamiento__kuale.group_guias_foraneos')
        is_dh = user.has_group('reclutamiento__kuale.group_dh_access') and not user._is_superuser()

        if is_dh:
            return []
        elif is_guia_gen:
            return Stage.search([
                ('name', 'in', ['Primera entrevista', 'First Interview',
                                'Segunda entrevista', 'Second Interview'])
            ]).ids
        elif is_guia_for:
            return Stage.search([
                ('name', 'not in', ['Nuevo', 'New',
                                    'Calificación inicial', 'Initial Qualification'])
            ]).ids
        else:
            return Stage.search([('visualize_form', '=', True)]).ids

    @api.constrains('stage_id')
    def _check_stage_allowed(self):
        """Barrera de seguridad: bloquea cambios de etapa no autorizados."""
        user = self.env.user
        is_guia_gen = user.has_group('reclutamiento__kuale.group_guias_generales')
        is_guia_for = user.has_group('reclutamiento__kuale.group_guias_foraneos')

        if not (is_guia_gen or is_guia_for):
            return

        for rec in self:
            if not rec.stage_id:
                continue
            allowed_ids = rec.allowed_stage_ids.ids
            if rec.stage_id.id not in allowed_ids:
                raise ValidationError(
                    "No tienes permiso para mover esta postulación "
                    "a la etapa '%s'.\n"
                    "Etapas permitidas: %s" % (
                        rec.stage_id.name,
                        ', '.join(rec.allowed_stage_ids.mapped('name')) or 'ninguna',
                    )
                )
    

    #@api.model
    #def search(self, args, **kwargs):
        #context = self.env.context
        # Elimina la condición de kanban_view que no funciona bien
        # El filtro de stages NO debe aplicarse en búsquedas de agrupación
        #if not context.get('group_by'):
            #allowed_stage_ids = self.get_stage_ids_allowed()
            #if allowed_stage_ids and not any(
                #isinstance(a, (list, tuple)) and len(a) >= 1 and a[0] == 'stage_id'
                #for a in args
            #):
                #args = list(args) + [('stage_id', 'in', allowed_stage_ids)]
        #return super(hr_applicant, self).search(args, **kwargs)
    
    #@api.model
    #def search(self, args, **kwargs):
        # Ajustar el dominio para la búsqueda basada en los stages permitidos
        #allowed_stage_ids = self.get_stage_ids_allowed()
        #print("STAGE PERMITIDOS", allowed_stage_ids)
        #if 'stage_id' not in args:
            #print("if dentro")
            #args.append(('stage_id', 'in', allowed_stage_ids))
        #print("fuera")
        #return super(hr_applicant, self).search(args, **kwargs)
        #return super(hr_applicant, self).search(args)


    @api.depends('stage_id')
    def _compute_stage_id(self):
        for record in self:
            stage = record.stage_id
            print("stage anterior:",stage)
            if stage:
                sequence = stage.sequence
                record.status_stage_id = sequence
                print("sequence:", record.status_stage_id)
            else:
                allowed_stage_ids = self.get_stage_ids_allowed()
                first_stage_id = allowed_stage_ids[
                    0] if allowed_stage_ids else None
                record.status_stage_id = first_stage_id
    
    @api.depends('stage_id')
    def _compute_is_hired_stage(self):
        for rec in self:
            rec.is_hired_stage = rec.stage_id.sequence in [7, 8]

    # Age automatically
    @api.depends('birthdate')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.birthdate:
                birthdate = fields.Date.from_string(record.birthdate)
                age = relativedelta(today, birthdate).years
                record.age = age
                record.is_minor = age < 18  # INDICA SI ES MENOR DE EDAD
            else:
                record.age = 0


    # Get gender
    @api.depends('curp')
    def _compute_gender(self):
        for record in self:
            if record.curp and len(record.curp) > 10:
                gender_char = record.curp[10].upper()
                if gender_char == 'H':
                    record.gender = 'male'
                elif gender_char == 'M':
                    record.gender = 'female'
                else:
                    record.gender = 'non_binary'
            else:
                record.gender = False

    @api.depends('curp')
    def _compute_related_records(self):
        for record in self:
            if record.curp:
                # Buscar otros registros con el mismo CURP
                related_records = self.env['hr.applicant'].search([('curp', '=', record.curp), ('id', '!=', record.id or record._origin.id)])
                record.related_records = related_records
            else:
                record.related_records = False

    @api.depends('postal_code_id')
    def _compute_allowed_state(self):
        for record in self:
            states = self.env['reclutamiento__kuale.city'].search([
                ('code', '=', self.postal_code_id.code),
                ('state', '!=', '')])
            unique_states = list(set(states.mapped('state')))
            allowed_states = []
            for state in unique_states:
                state_record = self.env['reclutamiento__kuale.city'].search([('state', '=', state)], limit=1)
                allowed_states.append(state_record.id)
            record.allowed_state = [(6, 0, allowed_states)]

    @api.depends('state_id')
    def _compute_allowed_municipality(self):
        for record in self:
            municipality = self.env['reclutamiento__kuale.city'].search([('code', '=', self.postal_code_id.code),
                                                                         ('state', '=', self.state_id.state)])
            unique_municipality = list(set(municipality.mapped('municipality')))
            # for city in municipality:
            #     print("CAMBIANDO NAME GET")
            #     print(city.name_get())
            allowed_municipality = []
            for municipality in unique_municipality:
                municipality_record = self.env['reclutamiento__kuale.city'].search(
                    [('municipality', '=', municipality)], limit=1)
                allowed_municipality.append(municipality_record.id)
            record.allowed_municipality = [(6, 0, allowed_municipality)]

    @api.depends('scholarship_Related')
    def _compute_is_bachelor_degree(self):
        for record in self:
            record.is_bachelor_degree = (
                record.scholarship_Related.name == 'Licenciatura'
        )

    @api.depends('municipality_id')
    def _compute_allowed_colony(self):
        for record in self:
            colony = self.env['reclutamiento__kuale.city'].search(
                [('code', '=', self.postal_code_id.code),
                 ('state', '=', self.state_id.state),
                 ('municipality', '=', self.state_id.municipality)])
            record.allowed_colony = [(6, 0, colony.ids)]

    @api.depends('stage_history_ids')
    def _compute_duration_actual(self):
        for record in self:
            if record.stage_history_ids:
                last_history = record.stage_history_ids[-1]
                if last_history.start_time:
                    delta = datetime.now() - last_history.start_time
                    days = delta.days
                    record.duration_actual = f"{days} día{'s' if days != 1 else ''}"
                else:
                    record.duration_actual = ''
            else:
                record.duration_actual = ''

    def rehire_action(self, **kwargs):
        try:
            print('Accion de recontratar')
            self.write({'application_status': 'hired'})
            stage = self.env['hr.recruitment.stage'].search([('sequence', '=', 7)], limit=1)
            if stage:
                self.write({'stage_id': stage.id})
            else:
                print('No se encontró etapa con secuencia 7')
        except Exception as e:
            print("Error al recontratar:", e)
            
    def interview_modal(self):
         return {
            'name': 'Send Interview',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.mail_mail',
            'view_mode': 'form',
            'view_id': self.env.ref('reclutamiento__kuale.view_modal_form_mail_interview').id,
            'target': 'new',
            'context': {'applicant_id': self.id},
        }

    def consult_interview(self):
        print('consultar formulario de reclutamiento')

    def request_complement(self):
        return {
            'name': 'Send complement',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.mail_mail',
            'view_mode': 'form',
            'view_id': self.env.ref('reclutamiento__kuale.view_modal_form_mail_complement').id,
            'target': 'new',
            'context': {'applicant_id': self.id},
        }

    def request_documentation(self):
        doc = self.env.ref('reclutamiento__kuale.hr_applicant_view_request_documentation')
        doc_id = doc.id
        return {
            'name': 'Request Documentation',
            'type': 'ir.actions.act_window',
            'res_model': 'hr_applicant_doc',
            'view_mode': 'form',
            'view_id': doc_id,
            'target': 'new',
            'context': {'default_applicant_id': self.id},
        }

    def modal_selected(self):
        view_id = self.env.ref('reclutamiento__kuale.view_modal_form_mail_selected').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Selected',
            'res_model': 'reclutamiento__kuale.mail_mail',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {'applicant_id': self.id}
        }

    def auth_check_id(self):
        self.write({'check_id':True})
        pass

    @api.onchange('check_id')
    def _onchange_check_id(self):
        print("cambio valor", self.check_id)
        pass

    def toggle_active(self):
        for record in self:
            if record.active:
                # Archivando
                previous_stage_id = record.stage_id.id
                job = self.env['hr.job'].search([('id', '=', record.job_id.id), ('active', '=', True)], limit=1)
                if job:
                    record.write({'process': 'archived'})
                    super(hr_applicant, record).toggle_active()
                    record.write({'last_stage_id': previous_stage_id})
                else:
                    msjError = "No es posible restaurar, ya no existe la requisicion para el puesto: " + record.job_id.name
                    raise exceptions.ValidationError(msjError)
            else:
                # Desarchivando
                previous_stage_id = record.last_stage_id.id if record.last_stage_id else record.stage_id.id
                super(hr_applicant, record).toggle_active()
                record.write({
                    'stage_id': previous_stage_id,
                    'process': 'progress'
                })
                    
    def set_viable(self):
        self.write({'process': 'viable'})

    def create_employee_from_applicant(self):
        # Siempre abrir el wizard — él decide si hay bloqueantes o no
        wizard = self.env['reclutamiento__kuale.complement_warning_wizard'].create({
            'applicant_id': self.id,
        })
        return {
            'name': 'Información incompleta',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.complement_warning_wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    def _do_create_employee(self, complement_pending=False):
        # Validar bloqueantes: check_id, huellas, documentación, formatos
        if not (self.check_id_verified
                and self.huellas_verified
                and self.documentacion_verified
                and self.formatos_verified):
            from odoo.exceptions import ValidationError
            faltantes = []
            if not self.check_id_verified:
                faltantes.append('• Check ID')
            if not self.huellas_verified:
                faltantes.append('• Huellas')
            if not self.documentacion_verified:
                docs = self.documentation_ids.filtered(lambda d: d.state != 'confirmed')
                faltantes.append(f'• Documentación ({len(docs)} pendientes)')
            if not self.formatos_verified:
                faltantes.append('• Formatos')
            raise ValidationError(
                'No se puede crear el empleado. Completa:\n' +
                '\n'.join(faltantes)
            )
 
        self.write({'pre_hired': True})
 
        # ... resto del método igual que antes (no cambia nada más)
        email = self.email_from or ''
        existing_user = self.env['res.users'].sudo().search(
            [('login', '=', email)], limit=1
        )
        res      = None
        employee = None
        try:
            res = super(hr_applicant, self).create_employee_from_applicant()
            employee = self.env['hr.employee'].search([('id', '=', res['res_id'])])
        except Exception as e:
            if 'dos usuarios' in str(e) or 'two users' in str(e).lower() or 'misma información de inicio' in str(e):
                employee = self.env['hr.employee'].sudo().create({
                    'name':         self.partner_name,
                    'job_id':       self.job_id.id if self.job_id else False,
                    'company_id':   self.company_id.id if self.company_id else self.env.company.id,
                    'applicant_id': self.id,
                    'work_email':   email,
                })
                if existing_user:
                    employee.sudo().write({'user_id': existing_user.id})
                res = {
                    'type':      'ir.actions.act_window',
                    'res_model': 'hr.employee',
                    'view_mode': 'form',
                    'res_id':    employee.id,
                }
            else:
                raise e
 
        nationality = self.nationality
        if self.nationality == 'other':
            nationality = self.other_nationality
 
        try:
            employee.with_context(skip_user_sync=True).write({
                'complement_pending': complement_pending,
                'rol_tab_id':         self.job_tab_id.rol_id.id,
                'curp':               self.curp,
                'rfc_number':         self.rfc_number,
                'ssnid':              self.social_security_number,
                'medical_unity':      self.medical_unity,
                'last_name':          self.last_name,
                'last_name2':         self.last_name2,
                'gender':             self.gender,
                'birthday':           self.birthdate,
                'age':                self.age,
                'marital':            self.marital_status,
                'nationality':        nationality,
                'state_birth_Select': self.state_birth_Select,
                'birthplace_select':  self.birthplace_select,
                'desk_phone':         self.desk_phone,
                'private_zip':        self.postal_code_id.code,
                'between_streets':    self.between_streets,
                'state_id':           self.state_id.id,
                'municipality_id':    self.municipality_id.id,
                'colony_id':          self.colony_id.id,
                'exterior_number':    self.exterior_number,
                'interior_number':    self.interior_number,
                'additional_ref':     self.additional_ref,
                'address_details':    self.address_details,
                'current_address':    self.current_address,
                'blood_type':         self.blood_type,
                'has_allergy':        self.has_allergy,
                'allergy':            self.allergy,
                'has_medical_tx':     self.has_medical_tx,
                'medical_tx':         self.medical_tx,
                'emergency_contacts': self.emergency_contacts.ids,
                'mother_name':        self.mother_name,
                'father_name':        self.father_name,
                'postal_code_fiscal': self.postal_code_fiscal,
                'bank_account_ids':   self.bank_account_ids.ids,
                'beneficiaries_ids':  self.beneficiaries_ids.ids,
                'home_work_time':     self.home_work_time,
                'about_vacancy':      self.about_vacancy,
                'previous_experience': self.previous_experience,
                'has_experience':     self.has_experience,
                'experiencies_ids':   self.experiencies_ids.ids,
                'has_driver_license': self.has_driver_license,
                'driver_license_number':   self.driver_license_number,
                'driver_license_validity': self.driver_license_validity,
                'has_ine':            self.has_ine,
                'ine_validity':       self.ine_validity,
            })
            if email:
                self.env.cr.execute(
                    "UPDATE hr_employee SET private_email = %s WHERE id = %s",
                    (email, employee.id)
                )
        except Exception as e:
            print("Error al mapear datos de empleado:", e)
 
        return res
    
    #Seccion de verificacion de check id, huellas y formatos antes de crear empleado
    def action_open_check_id_modal(self):
        partner = self.partner_id
        if not partner:
            raise exceptions.ValidationError('No hay contacto vinculado al candidato.')
        if self.curp and not partner.curp:
            partner.write({'curp': self.curp})
        if self.rfc_number and not partner.rfc:
            partner.write({'rfc': self.rfc_number})
        self.write({'check_id_opened': True})
        return partner.action_verify_checkid()
    
    def action_open_confirm_check_id(self):
        return {
            'name': 'Confirmar verificación Check ID',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.confirm_check_id',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_applicant_id': self.id}
        }

    def action_huellas_verified(self):
        return {
            'name': 'Registrar Huella',
            'type': 'ir.actions.act_window',
            'res_model': 'zk.biometric.create.user.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id,
                'default_applicant_id': self.id,
                'default_user_id': str(self.id),
                'default_name': self.partner_name or '',
                'default_last_name': self.last_name or '',
            }
        }

    def action_formatos_verified(self):
        wizard = self.env['reclutamiento__kuale.formatos_wizard'].create_for_applicant(self.id)
        return {
            'name': 'Formatos',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formatos_wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }
    
    def generate_Contract(self):
        emp_id = self.env['hr.employee'].search([('applicant_id', '=', self.id)])
        contract_id = self.job_id.job_tab_ids.contract_format
        print("contrato a aplicar ", contract_id)
        if contract_id:
            print("aplicar contrato por default")
            structure_id = self.env['hr.payroll.structure.type'].search([('name', '=', 'Employee')])
            contract = {
                'structure_type_id': structure_id.id,
                'employee_id': emp_id.id,
                'department_id': emp_id.department_id.id,
                'job_id': self.job_id.id,
                'resource_calendar_id': 1,
                'company_id': emp_id.company_id.id,
                'hr_responsible_id': emp_id.parent_id.id,
                'name': 'Contrato Automatico',
                'date_start': fields.Datetime.now(),
                'wage': self.job_id.basic_salary,
                'contract_format_id': self.job_id.job_tab_ids.contract_format.id
            }
            contract_c = self.env['hr.contract'].sudo().create(contract)
            name_format=self.job_id.job_tab_ids.contract_format.type_format_id.name
            if name_format.strip().lower() == "determinado":
                contract_duration = self.job_id.job_tab_ids.contract_duration
                current_date = datetime.today()
                end_date = current_date + timedelta(days=contract_duration)
                contract_c.write({'date_end': end_date})
        self.write({'pre_hired': False})

    def send_whatsapp(self):
        print("enviando whatsapp")
        try:
            setting = self.env['reclutamiento__kuale.recruitment_settings'].sudo().search([], limit=1)
            url = "https://graph.facebook.com/v20.0/"+setting.number_id+"/messages"
            print("url",url)
            headers = {
                "Authorization": "Bearer "+setting.access_token_wsp,
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product": "whatsapp",
                "to": "52"+str(self.partner_mobile),
                "type": "template",
                "template": {
                    "name": setting.template_wsp,
                    "language": {
                        "code": "en_US"
                    }
                }
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))
            print("response",response.json())
        except Exception as e:
            print("Error send_whatsapp:", e)

    def format_regulation(self):
        self._render_dynamic_body('regulation')
        pdf = self.env.ref('reclutamiento__kuale.regulation_received').report_action(self)
        return pdf

    def format_confidentiality(self):
        self._render_dynamic_body('confidentiality')
        pdf = self.env.ref('reclutamiento__kuale.confidentiality_received').report_action(self)
        return pdf

    def format_uniform_voucher(self):
        self._render_dynamic_body('uniform_voucher')
        pdf = self.env.ref('reclutamiento__kuale.uniform_voucher_format').report_action(self)
        return pdf

    def format_promissory(self):
        self._render_dynamic_body('promissory')
        pdf = self.env.ref('reclutamiento__kuale.promissory_format').report_action(self)
        return pdf

    def generate_contract_summary(self):
        self.actual_date = date.today()
        pdf = self.env.ref('reclutamiento__kuale.contract_summary').report_action(self)
        return pdf

    def _render_dynamic_body(self, type_format):
        try:
            for record in self:
                template = (self.env['reclutamiento__kuale.format_employee'].sudo()
                            .search([('job_id', '=', self.job_id.id), ('type_format', '=', type_format)], limit=1))
                template = template.body or ''
                context = {'object': record}

                def replace_match(match):
                    expr = match.group(1).strip()
                    try:
                        value = eval(expr, {**context, '__builtins__': __builtins__})
                        if expr == "object.actual_date":
                            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
                            actual_date = date.today()
                            print("hoy", actual_date)
                            value = actual_date.strftime('%d de %B del %Y')
                    except Exception as e:
                        value = str(e)
                        print("value except", value)
                    return str(value)

                template = unescape(template)
                print("TEMPLATE ANTES:", template[:500])
                matches = re.findall(r'<t t-out="([^"]+)"></t>', template)
                print("MATCHES ENCONTRADOS:", matches)
                body_rendered = re.sub(r'<t t-out="([^"]+)"></t>', replace_match, template)
                self.write({'body_temp': Markup(body_rendered)})
                record.body_temp = Markup(body_rendered)
        except Exception as e:
            value = str(e)
            print("ERROR Creando formato", value)

    @api.model
    def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        result = super()._read_group(domain, groupby, aggregates, having, offset, limit, order)

        if 'stage_id' not in (groupby or []):
            return result

        job_id = None
        for condition in domain:
            if isinstance(condition, (list, tuple)) and len(condition) >= 3 and condition[0] == 'job_id':
                job_id = condition[2]
                break

        show_propuesta = False
        if job_id:
            job = self.env['hr.job'].sudo().browse(int(job_id))
            if job.exists():
                show_propuesta = job.show_propuesta_contrato

        if job_id:
            stage_domain = ['|', ('job_ids', '=', False), ('job_ids', 'in', [job_id])]
        else:
            stage_domain = [('job_ids', '=', False)]

        all_stages = self.env['hr.recruitment.stage'].sudo().search(stage_domain, order='sequence')
        existing_stage_ids = {group[0].id for group in result if group[0]}

        for stage in all_stages:
            if stage.name == 'Propuesta de contrato' and not show_propuesta:
                result = [g for g in result if not (g[0] and g[0].id == stage.id)]
                continue

            if stage.id not in existing_stage_ids:
                if result:
                    dummy = tuple([stage] + [0] * (len(result[0]) - 1))
                else:
                    dummy = (stage, 0)
                result.append(dummy)

        result.sort(key=lambda x: x[0].sequence if x[0] else 0)
        return result

    @api.model
    def web_read_group(self, domain, fields, groupby, **kwargs):

        job_id = None
        for condition in domain:
            if isinstance(condition, (list, tuple)) and len(condition) >= 3 and condition[0] == 'job_id':
                job_id = condition[2]
                break

        show_propuesta = False
        if job_id:
            job = self.env['hr.job'].sudo().browse(int(job_id))
            if job.exists():
                show_propuesta = job.show_propuesta_contrato

        result = super().web_read_group(domain, fields, groupby, **kwargs)

        if 'stage_id' in (groupby or []) and not show_propuesta:
            stage = self.env['hr.recruitment.stage'].sudo().search(
                [('name', '=', 'Propuesta de contrato')], limit=1
            )
            if stage:
                result['groups'] = [
                    g for g in result.get('groups', [])
                    if g.get('stage_id') != (stage.id, stage.name)
                ]
                result['length'] = len(result['groups'])

        return result
    
    @api.depends('abandoned', 'abandonment_reason', 'abandonment_comment')
    def _compute_abandonment_display(self):
        for rec in self:
            if rec.abandoned:
                reason = dict(rec._fields['abandonment_reason'].selection).get(rec.abandonment_reason, '')
                text = f"Abandonado por: {reason}"
                if rec.abandonment_comment:
                    text += f" - {rec.abandonment_comment}"
                rec.abandonment_display = text
            else:
                rec.abandonment_display = ''
    
    @api.depends('application_status', 'refuse_reason_id')
    def _compute_status_with_reason(self):
        for rec in self:
            if rec.application_status == 'refused':
                reason = rec.refuse_reason_id.name if rec.refuse_reason_id else ''
                rec.status_with_reason = f"Rechazado: {reason}" if reason else "Rechazado"
            else:
                rec.status_with_reason = ""
    
    ###Captura de Datos Biometricos
    def action_open_enroll_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registrar Huella',
            'res_model': 'zk.biometric.create.user.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name':         self.partner_name,
                'default_last_name':    self.last_name,
                'default_user_id':      self.id,
                'default_applicant_id': self.id,
            }
        }
    
    ###Alta IMSS
    def action_imss(self):
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Aviso',
                    'message': 'Aquí va ir lo del IMSS',
                    'type': 'info', 
                    'sticky': False, 
                }
            }

class HrApplicantProduct(models.Model):
    _name = 'hr.applicant.product'
    _description = 'Applicant Product'

    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Garments", required=True,
                                 domain="[('product_tmpl_id', '=', product_template_id)]")
    product_template_id = fields.Many2one('product.template', string="Product Template",
                                          domain="[('id', 'in', allowed_product_templates)]")
    quantity = fields.Integer(string="Cantidad")
    job_id = fields.Many2one('hr.job', string="Job")
    allowed_product_templates = fields.Many2many(
        'product.template', string="Allowed Product Templates", compute='_compute_allowed_product_templates'
    )

    @api.depends('applicant_id')
    def _compute_allowed_product_templates(self):
        for record in self:
            job = record.applicant_id.job_id
            jobs = job.products.mapped('product_template_id.id')
            record.allowed_product_templates = [(6, 0, jobs)]


class BeneficiaryApplicant(models.Model):
    _name = 'hr.applicant.beneficiary'
    _description = 'Applicant Beneficiary'
    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True)
    beneficiary_name = fields.Char(string='Nombre del beneficiario')
    beneficiary_relationship = fields.Selection(RELATIONSHIP_SELECTION, string='Parentesco del beneficiario')
    other_relationship = fields.Char(string='Otro')
    beneficiary_percentage = fields.Char(string=' Porcentaje del beneficiario')

    @api.model
    def create(self, vals):
        if 'applicant_id' in vals:
            applicant = self.env['hr.applicant'].browse(vals['applicant_id'])
            if len(applicant.beneficiaries_ids) >= 4:
                raise exceptions.ValidationError("Solo 4 beneficiarion permitidos")
        return super(BeneficiaryApplicant, self).create(vals)

    def write(self, vals):
        if 'applicant_id' in vals:
            for record in self:
                applicant = self.env['hr.applicant'].browse(vals['applicant_id'])
                if len(applicant.beneficiaries_ids) >= 4 and vals['applicant_id'] != record.applicant_id.id:
                    raise exceptions.ValidationError("Solo son permitidos 4 beneficiarion")
        return super(BeneficiaryApplicant, self).write(vals)


class BankAccount(models.Model):
    _name = 'bank.account'
    _description = 'Bank Account'

    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True)
    account_type = fields.Char(string="Tipo de cuenta")
    account_number = fields.Char(string="No. de Cuenta", required=True)
    interbank_clabe = fields.Char(string="Clabe Interbancaria", required=True)
    payroll_card_number = fields.Char(string="Número de tarjeta de nómina")
    bank = fields.Char(string="Banco", required=True)
    branch_bank = fields.Char(string="Sucursal para pago electrónico")

    @api.model
    def create(self, vals):
        if 'applicant_id' in vals:
            applicant = self.env['hr.applicant'].browse(vals['applicant_id'])
            if len(applicant.bank_account_ids) >= 2:
                raise exceptions.ValidationError("Solo dos cuentas son permitidas")
        return super(BankAccount, self).create(vals)

    def write(self, vals):
        if 'applicant_id' in vals:
            for record in self:
                applicant = self.env['hr.applicant'].browse(vals['applicant_id'])
                if len(applicant.bank_account_ids) >= 2 and vals['applicant_id'] != record.applicant_id.id:
                    raise exceptions.ValidationError("Solo dos cuentas son permitidas")
        return super(BankAccount, self).write(vals)


class ExperienceApplicant(models.Model):
    _name = 'hr.applicant.experience'
    _description = 'Previous experience'
    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True)
    companyE = fields.Char(string='Empresa')
    cityE = fields.Char(string='Ciudad')
    cityESelect = fields.Many2one('reclutamiento__kuale.city',string='Ciudad')
    periodEIn = fields.Date(string="Fecha de Ingreso")
    periodEOut = fields.Date(string="Fecha de salida")
    positionE = fields.Char(string='Puesto')
    salaryE = fields.Integer(string='Sueldo')
    supervisorE = fields.Char(string='Nombre del jefe directo')
    referenceE = fields.Char(string='Persona para referencias')
    referencePhoneE = fields.Char(string='No. Contacto para referencias')
    reasonE = fields.Char(string='Motivo de salida')
    functionsE = fields.Text(string='Función realizada')
    currently = fields.Boolean(string='Actualmente', default=False)


class EmergencyApplicant(models.Model):
    _name = 'hr.applicant.emergency'
    _description = 'Emergency contacts'
    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True)
    name = fields.Char(string='Nombre')
    relationship = fields.Selection(RELATIONSHIP_SELECTION, string='Parentesco')
    phone_number = fields.Char(string='Teléfono')


class Documents(models.Model):
    _name = 'reclutamiento__kuale.documents_applicant'
    _description = 'Documentos de identificación'

    applicant_id = fields.Many2one("hr.applicant", string="Aplicacion")
    doc_data = fields.Binary()
    doc_name = fields.Char()

    @api.model
    def create(self,vals):
        record=super(Documents, self).create(vals)
        try:
            archivo_binario = record.doc_data
            nombre_archivo = record.doc_name
            print("archivo name", nombre_archivo)
            self.env['ir.attachment'].create({
                'name': nombre_archivo,
                'type': 'binary',
                'datas': archivo_binario,
                'res_model': 'hr.applicant',
                'res_id': record.applicant_id.id,
                'mimetype': 'application/pdf',
            })
            print("LISTO")
        except Exception as e:
            print("Error al crear identity_document:", e)
        return record

class IdentificationOption(models.Model):
    _name = 'reclutamiento__kuale.identification_option'

    name = fields.Char(string="Nombre de la opción", required=True)
    description = fields.Char(string="Descripción")


class ScheduleStudent(models.Model):
    _name = 'reclutamiento__kuale.schedule_student'
    _description = 'Horario de estudiante'

    applicant_id = fields.Many2one("hr.applicant", string="Aplicacion")
    day = fields.Selection([
        ('sunday', 'Domingo'),
        ('monday', 'Lunes'),
        ('tuesday', 'Martes'),
        ('wednesday', 'Miercoles'),
        ('thursday', 'Jueves'),
        ('friday', 'Viernes'),
        ('saturday', 'Sábado')
    ], string='Día de la semana')
    time_start = fields.Char(string="Hora de inicio")
    time_end = fields.Char(string="Hora fin")


class ApplicantGetRefuseReason(models.TransientModel):
    _inherit = 'applicant.get.refuse.reason'

    comments = fields.Text('Comentario adicional')

    def action_refuse_reason_apply(self):
        self.write({'send_mail': False})
        result = super().action_refuse_reason_apply()
        for applicant in self.applicant_ids:
            applicant.write({'process': 'no_viable'})
        return result

class OtherStudies(models.Model):
    _name = 'hr.applicant.other_studies'
    _description = 'Otros estudios'
    applicant_id = fields.Many2one('hr.applicant', string="Applicant", required=True)

    name_study = fields.Char(string='Curso o diplomado')
    school_studies = fields.Char(string='Escuela o instituto')
    has_document = fields.Selection(ONE_SELECTION, string='¿Cuentas con documento aprobatorio?')
    document_type = fields.Char(string='Tipo de documento')

class HrRecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        return self.sudo().search([], order=order)

class ApplicantKnowledge(models.Model):
    _name = 'reclutamiento__kuale.applicant_knowledge'
    _description = 'Conocimientos y Herramientas del Aplicante'

    applicant_id = fields.Many2one('hr.applicant', string='Aplicante', required=True, ondelete='cascade')
    tipo = fields.Selection([
        ('Conocimiento', 'Conocimiento'),
        ('Herramienta',  'Herramienta'),
    ], string='Tipo', required=True)
    name = fields.Char(string='Nombre', required=True)

class ApplicantLanguage(models.Model):
    _name = 'reclutamiento__kuale.applicant_language'
    _description = 'Idiomas del Aplicante'

    applicant_id = fields.Many2one('hr.applicant', string='Aplicante', required=True, ondelete='cascade')
    language_id  = fields.Many2one('reclutamiento__kuale.language',       string='Idioma', required=True)
    level_id     = fields.Many2one('reclutamiento__kuale.language_level', string='Nivel',  required=True)