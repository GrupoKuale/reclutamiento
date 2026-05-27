from odoo import fields, models, api


class res_company(models.Model):
    _inherit = 'res.company'

    # Razon social (Alfanumérico)
    business_name = fields.Char(string='Razon social', required=False, default="")
    # RFC (Alfanumérico)
    rfc = fields.Char(string='RFC', required=False, size=13, default="")
    # Representante legal (Selección)
    legal_representative = fields.Many2one(
        'reclutamiento__kuale.legal.representative',
        string='Representante legal',
        required=False
    )
    # Domicilio fiscal (Alfanumérico)
    fiscal_address = fields.Text(string='Domicilio fiscal', required=False)
    # Giro (Seleccion)
    business_type = fields.Many2one(
        'reclutamiento__kuale.business.type',
        string='Giro',
        required=False
    )
    # Registro patronal:IMSS (Seleccion)
    imss_registration = fields.Many2one(
        'reclutamiento__kuale.imss.registration',
        string='Registro patronal (IMSS)',
        required=False
    )
    # Certificado para timbrado (Seleccion)
    certificate_for_stamp = fields.Many2one(
        'reclutamiento__kuale.digital.stamp.certificate',
        string='Certificado para timbrado',
        required=False
    )
    # Fecha de apertura (Fecha)
    opening_date = fields.Date(string='Fecha de apertura', required=False)
    # SUCURSALES
    # No. de tienda
    no_store = fields.Integer(string='No.de tienda', required=True, default=None)
    # Tipo de Sucursal (Selección unica)
    branch_type = fields.Many2one('reclutamiento__kuale.branch.type', string='Tipo de Sucursal', required=False)
    # Nombre sucursal
    branch_name = fields.Char(string='Nombre sucursal', required=True)
    # Reporta a (seleccion)
    reports_to = fields.Many2one('res.users', string='Reporta a',
                                 domain="[('company_id', '=', parent_id), ('active', '=', True)]")
    # Entrenador (Selección múltiple)
    trainers = fields.Many2many('res.users', string='Entrenador(es)',
                                domain="[('company_id', '=', parent_id), ('active', '=', True)]")
    # Guia general
    general_guide = fields.Many2one('res.users', string='Guía General',
                                    domain="[('company_id', '=', parent_id), ('active', '=', True)]")
    # Capacitación (Selección múltiple)
    training_available = fields.Boolean(string='Capacitación')
    # Metros cuadrados de construcción (Numérico)
    construction_area = fields.Float(string='Metros cuadrados de construcción')
    # Metros cuadrados de terreno (Numérico)
    land_area = fields.Float(string='Metros cuadrados de terreno')
    # Layout (File)
    layout = fields.Binary(string='Layout')
    layout_filename = fields.Char(string='Layout (Croquis)')
    # Póliza de seguro
    insurance_policy = fields.Binary(string='Póliza de seguro')
    insurance_policy_filename = fields.Char(string='Póliza de seguro')
    # Entre calles
    between_streets = fields.Text(string='Entre calles')
    citySelect = fields.Many2one('reclutamiento__kuale.city', string='Ciudad')
    # Diferencia sucursal de company
    is_parent_id_set = fields.Boolean(compute='_compute_is_parent_id_set', store=True)
    is_company = fields.Boolean(compute='_compute_is_company', store=False)
    # Saber si tendra sucursales o ubicaciones de trabajo
    company_type = fields.Selection([
        ('branch', 'Sucursales'),
        ('work_location', 'Ubicaciones de trabajo')
    ], string='La empresa tendrá')

    work_location_ids= fields.One2many('hr.work.location','company_id',string='Ubicaciones de trabajo')

    # Banderas para mostrar empresas en PCX
    allow_alliance = fields.Boolean(string="Permitir solicitudes de convenios")
    allow_vouchers = fields.Boolean(string="Permitir solicitudes de vales prepagados")

    @api.onchange('citySelect')
    def _onchange_citySelect(self):
        if self.partner_id:
            self.partner_id.city = self.citySelect.name

    def _inverse_citySelect(self):
        for company in self:
            if company.partner_id:
                company.city = company.citySelect
                company.partner_id.city = company.citySelect

    @api.onchange('rfc')
    def set_caps(self):
        rfc_aux = str(self.rfc)
        self.rfc = rfc_aux.upper()

    @api.depends('parent_id')
    def _compute_is_parent_id_set(self):
        for record in self:
            record.is_parent_id_set = bool(record.parent_id)

    @api.depends('no_store')
    def _compute_is_company(self):
        for record in self:
            if record.parent_id:
                print("True")
                record.is_company = True
            else:
                print("False")
                record.is_company = False

    @api.model
    def get_all_companies(self):
        companies = self.env['res.company'].sudo().search([]).ids
        print("companies", companies)
        company_context = dict(self.env.context, allowed_company_ids=companies)

        # Preferir compañías que sí tienen vacantes publicadas
        jobs_domain = ['|', ('website_published', '=', True), ('is_published', '=', True)]
        job_companies = self.env['hr.job'].with_context(company_context).sudo().search(jobs_domain).mapped('company_id')
        # Mostrar la compañía padre si existe, para que el listado sea consistente
        companiesT = (job_companies.mapped('parent_id') | job_companies).filtered(lambda c: not c.parent_id)

        # Fallback: si no hay vacantes publicadas, mostrar empresas principales
        if not companiesT:
            companiesT = self.env['res.company'].with_context(company_context).sudo().search([('parent_id', '=', False)])
        if not companiesT:
            companiesT = self.env['res.company'].with_context(company_context).sudo().search([])
        companies = []
        for company in companiesT:
            print("compañia")
            image_base64 = company.logo
            if not image_base64:
                image_base64 = ""
            elif isinstance(image_base64, bytes):
                print("image_bin decode")
                image_base64 = image_base64.decode('utf-8')
            elif not isinstance(image_base64, str):
                image_base64 = str(image_base64)
            image_base64 = image_base64.replace("b'", "").replace("'", "")
            image_data = {
                'id': company.id,
                'logo': image_base64,
                'name': company.name
            }
            companies.append(image_data)
        return companies
