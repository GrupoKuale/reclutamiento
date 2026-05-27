from odoo import fields, models, api


class Credential(models.Model):
    _name = 'reclutamiento__kuale.credential'
    _description = 'reclutamiento__kuale.credential'

    employee_id = fields.Many2one("hr.employee", string="Empleado")
    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción', translate=True)
    format_id = fields.Many2one('reclutamiento__kuale.credential_format', string="Formato")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Credential name already exists!"),
    ]


class Format(models.Model):
    _name = 'reclutamiento__kuale.credential_format'
    _description = 'reclutamiento__kuale.credential_format'

    name = fields.Char(string='Nombre', required=True)
    hight = fields.Integer(string='Alto', required=True)
    width = fields.Integer(string='Ancho', required=True)
    background_image_front = fields.Image(string="Imagen de fondo frontal")
    background_image_reverse = fields.Image(string="Imagen de fondo del lado posterior")
    element_ids = fields.Many2many('reclutamiento__kuale.credential_element', 'cred_form_element_rel', 'form_id', 'elem_id', string='Elementos de Credencial')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Format name already exists!"),
    ]


class Element(models.Model):
    _name = 'reclutamiento__kuale.credential_element'
    _description = 'reclutamiento__kuale.credential_element'

    name = fields.Char(string='Nombre', required=True)
    hight = fields.Integer(string='Alto', required=True)
    width = fields.Integer(string='Ancho', required=True)
    top = fields.Integer(string='Arriba', required=True)
    bottom = fields.Integer(string='Abajo', required=True)
    left = fields.Integer(string='Izquierda', required=True)
    right = fields.Integer(string='Derecha', required=True)
    ref = fields.Char(string='Referencia', required=True)
    type = fields.Selection([
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('logo', 'Logo')
    ], string="Tipo")
    side = fields.Selection([
        ('front', 'Frontal'),
        ('reverse', 'Posterior')
    ], string="Lado") # Anverso, Reverso
    format_id = fields.Many2many('reclutamiento__kuale.credential_format', 'cred_form_element_rel', 'elem_id', 'form_id', string='Formato')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Element name already exists!"),
    ]