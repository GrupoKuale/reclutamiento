
from odoo import fields, models


class TypeContract(models.Model):
    _name = 'catalog_sat.type_contract'
    _description = "Catálogo de Tipos de contratos"

    name = fields.Char(string='c_TipoContrato', required=True)
    description = fields.Text('Descripción', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class PaymentPeriodicity(models.Model):
    _name = 'catalog_sat.payment_periodicity'
    _description = "Catálogo de Periodicidad de pago"

    name = fields.Char(string='c_PeriodicidadPago', required=True)
    description = fields.Text('Descripción', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class TypeWorkday(models.Model):
    _name = 'catalog_sat.type_workday'
    _description = "Catálogo Tipo de jornada"

    name = fields.Char(string='c_TipoJornada', required=True)
    description = fields.Text('Descripción', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class FiscalRegime(models.Model):
    _name = 'catalog_sat.fiscal_regime'
    _description = "Catálogo Régimen Fiscal"

    name = fields.Char(string='c_RegimenFiscal', required=True)
    description = fields.Text('Descripción', required=True)
    apply_for = fields.Selection([
        ('legal_entity', 'Moral'),
        ('natural_person', 'Física'),
        ('both', 'Ambos'),
    ], string="Aplica para tipo persona")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class TypeRegime(models.Model):
    _name = 'catalog_sat.type_regime'
    _description = "Catálogo Tipo de régimen"

    name = fields.Char(string='c_tiporegimen', required=True)
    description = fields.Text('Descripción', required=True)
    apply_for = fields.Selection([
        ('legal_entity', 'Moral'),
        ('natural_person', 'Física'),
        ('both', 'Ambos'),
    ], string="Aplica para tipo persona")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class UseCFDI(models.Model):
    _name = 'catalog_sat.use_cfdi'
    _description = "Catálogo Uso CFDI"

    name = fields.Char(string='c_UsoCFDI', required=True)
    description = fields.Text('Descripción', required=True)
    apply_for = fields.Selection([
        ('legal_entity', 'Moral'),
        ('natural_person', 'Física'),
        ('both', 'Ambos'),
    ], string="Aplica para tipo persona")
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class RiskPlaced(models.Model):
    _name = 'catalog_sat.risk_placed'
    _description = "Catálogo Riesgo Puesto"

    name = fields.Char(string='c_RiesgoPuesto', required=True)
    description = fields.Text('Descripción', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class PaymentMethod(models.Model):
    _name = 'catalog_sat.payment_method'
    _description = "Catálogo Método de Pago"

    name = fields.Char(string='c_MetodoPago', required=True)
    description = fields.Text('Descripción', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class FederalEntityCode(models.Model):
    _name = 'catalog_sat.federal_entity_code'
    _description = "Catálogo de estados"

    name = fields.Char(string='c_Estado', required=True)
    c_country = fields.Char(string='c_Pais', required=True)
    description = fields.Text('Nombre del estado', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class PaymentBasis(models.Model):
    _name = 'catalog_payroll.payment_basis'
    _description = "Catálogo Base de pago"

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class TypeBenefit(models.Model):
    _name = 'catalog_payroll.type_benefit'
    _description = "Catálogo Tipo de prestación"

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]
