from odoo import models, fields, api, exceptions
from datetime import timedelta


ONE_SELECTION = [
    ('yes', 'Si'),
    ('no', 'No')
]


class Rol_Employee(models.Model):
    _name = 'hr.employee.rol'
    _description = 'Employee rol'

    name = fields.Char("Rol")
    description = fields.Char("Descripcion")


class hr_employee(models.Model):
    _inherit = 'hr.employee'
    # applicant_id = fields.One2many('hr.applicant', 'emp_id', 'Applicant')
    #rol_employee = fields.Many2one('hr.employee.rol', string='Rol')
    rol_employee_selection = fields.Selection([
        ('lgp','LGP'),
        ('dh', 'DH'),
        ('pxc', 'PXC')
    ], string="Rol")
    rol_tab_id = fields.Many2one(
        'reclutamiento__kuale.rol_tab', string="Rol de usuario",
        help="Rol que asignará permisos al usuario de este empleado."
    )
    credentials = fields.One2many('reclutamiento__kuale.credential', 'employee_id', string="Credenciales",
                                  required=True)
    # Datos recuperados de solicitud como aplicante
    # Generales
    curp = fields.Char(string='CURP', required=True, store=True)
    rfc_number = fields.Char(string='RFC', size=13, default="")
    social_security_number = fields.Char(string='Número de Seguridad Social')
    medical_unity = fields.Char(string='Unidad Medica Familiar')
    last_name = fields.Char(string='Apellido paterno', required=True)
    last_name2 = fields.Char(string='Apellido materno')
    age = fields.Integer(string='Edad', readonly=True)
    nationality = fields.Char(string='Nacionalidad')
    state_birth_Select = fields.Many2one('reclutamiento__kuale.city', string='Entidad federativa de nacimiento')
    birthplace_select = fields.Many2one('reclutamiento__kuale.city', string='Ciudad de nacimiento')
    # Datos de contacto
    desk_phone = fields.Char(string='Teléfono Fijo')
    # Domicilio
    between_streets = fields.Text(string='Entre Calles')
    state_id = fields.Many2one('reclutamiento__kuale.city', string='Entidad Federativa')
    municipality_id = fields.Many2one('reclutamiento__kuale.city', string='Municipio o Alcaldía')
    colony_id = fields.Many2one('reclutamiento__kuale.city', string='Colonia')
    exterior_number = fields.Char(string='No. Exterior', required=True)
    interior_number = fields.Char(string='No. Interior', required=False)
    additional_ref = fields.Char(string='Referencias adicionales')
    address_details = fields.Text(string='Características del domicilio')
    # Tipo de vialidad
    current_address = fields.Char(string='Nombre de la vialidad', required=True)
    # Salud
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
    # Familiares
    mother_name = fields.Char(string="Nombre de la madre")
    father_name = fields.Char(string="Nombre del padre")
    # Prendas
    clothing_size = fields.One2many('hr.applicant.product', 'applicant_id', string="Talla Uniforme")
    # Datos fiscales
    postal_code_fiscal = fields.Char(string='Código Postal', size=5, help='Only 5 digits allowed.', required=True)
    bank_account_ids = fields.One2many('bank.account', 'applicant_id', string="Cuentas")
    beneficiaries_ids = fields.One2many('hr.applicant.beneficiary', 'applicant_id', string="Beneficiarios")
    home_work_time = fields.Char(string="Tiempo de traslado casa - trabajo")
    # Adicionales
    about_vacancy = fields.Selection([
        ('friendship', 'Amistad'),
        ('networking', 'Redes'),
        ('initiative', 'Iniciativa propia'),
        ('other', 'Otro'),
    ], string='¿Cómo te enteraste de la vacante?', required=True)
    previous_experience = fields.Selection(ONE_SELECTION, string='Ha laborado con nosotros')
    # Experiencia
    has_experience = fields.Selection(ONE_SELECTION, string='Experiencia laboral actual/anterior', default='no')
    experiencies_ids = fields.One2many('hr.applicant.experience', 'applicant_id', string="Experiencia laboral")
    # Licencias
    has_driver_license = fields.Selection(ONE_SELECTION, string='Cuenta con licencia de conducir', required=True)
    driver_license_number = fields.Char(string='Número de licencia')
    driver_license_validity = fields.Date(string='Vigencia de licencia', default=fields.Date.context_today)
    has_ine = fields.Selection(ONE_SELECTION, string='¿Cuentas con INE vigente?', required=True)
    ine_validity = fields.Char(string="Vigencia INE")
    has_passport = fields.Selection(ONE_SELECTION, string='Cuenta con Pasaporte')
    passport_validity = fields.Date(string="Vigencia del pasaporte")
    has_visa = fields.Selection(ONE_SELECTION, string='Cuenta con visa')
    # Documentos
    ine_document = fields.Binary(string='INE')
    nss_files = fields.One2many('multiples_files', 'partner_id', string='NSS Files')
    rfc_files = fields.One2many('multiples_files', 'partner_id', string='RFC Files')
    driver_files = fields.One2many('multiples_files', 'partner_id', string='Licencia de conducir')
    curp_file = fields.Binary(string='CURP')
    bank_account_agreement_file = fields.Binary(string='Contrato de cuenta bancaria')
    birth_act = fields.Binary(string='Acta de Nacimiento')
    address_file = fields.Binary(string='Comprobante de domicilio')
    passport_file = fields.Binary(string='Pasaporte')
    identity_document = fields.One2many('reclutamiento__kuale.documents_applicant', 'applicant_id',
                                        string="Otros")
    promissory_file = fields.Binary('Pagaré de uniforme')
    # Biometric device
    device_id_num = fields.Char(string='Biometric Device ID',
                                help="Give the biometric device id")
    
    # Flag para marcar empleados con complemento pendiente al momento de creación desde aplicante
    complement_pending = fields.Boolean(string='Complemento pendiente', default=False)

    def format_regulation(self):
        print("consult regulation format signed")

    def write(self, vals):
        # Si viene del proceso de crear empleado, no sincronizar con res.users
        if self.env.context.get('skip_user_sync'):
            return super(hr_employee, self).write(vals)
        for record in self:
            res = super(hr_employee, self).write(vals)
            if 'rol_tab_id' in vals:
                if record.user_id:
                    # Removemos y asignamos nuevos permisos
                    record.user_id.groups_id = record.rol_tab_id.groups_ids
                elif not record.user_id:
                    # Si no tiene usuario, crear uno con password autogenerada
                    password = self.generate_password()
                    user = record._create_odoo_user(self.private_email, password, {
                        'name': self.name,
                        'company_id': self.company_id.id,
                        'work_email': self.private_email
                    })
                    self.write({'user_id': user.id})
                    user.action_reset_password()  # Envía correo de invitación para reiniciar password
            return res
