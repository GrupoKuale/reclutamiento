from odoo import fields, models


class SalaryZone(models.Model):
    _name = 'catalog_imss.salary_zone'
    _description = "Catálogo Zona de salario"

    name = fields.Char(string='Nombre')

    effective_date = fields.Date('Fecha de Inicio', required=True, help="Fecha en que este salario mínimo entra en vigor")
    wage_zone_a = fields.Float('Área A', help="Monto diario del salario mínimo en la Zona A")
    wage_zone_b = fields.Float('Área B', help="Monto diario del salario mínimo en la Zona B")
    wage_zone_c = fields.Float('Área C', help="Monto diario del salario mínimo en la Zona C")

    _sql_constraints = [
        ('name_uniq', 'unique (effective_date)', "Ya existe un salario mínimo para la fecha de inicio especificados."),
    ]


class TypeMovement(models.Model):
    _name = 'catalog_imss.type_movement'
    _description = "Catálogo Tipo de Movimiento"
    id_catalog = fields.Char(string="Id")
    name = fields.Char(string='Nombre', required=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class TypeWorker(models.Model):
    _name = 'catalog_imss.type_worker'
    _description = "Catálogo Tipo de Trabajador"
    id_catalog = fields.Integer(string="Id")
    name = fields.Char(string='Nombre', required=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class TypeWorkdayIMSS(models.Model):
    _name = 'catalog_imss.type_workday'
    _description = "Catálogo Tipo de Jornada IMSS"

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class TypeSalary(models.Model):
    _name = 'catalog_imss.type_salary'
    _description = "Catálogo Tipo de Salario"
    id_catalog = fields.Integer(string="Id")
    name = fields.Char(string='Nombre', required=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]


class TypeWorkingDayReduced(models.Model):
    _name = 'catalog_imss.type_working_day_reduced'
    _description = "Catálogo Tipo de Jornada/Semana reducida"
    id_catalog = fields.Integer(string="Id")
    name = fields.Char(string='Nombre', required=True)
    description = fields.Text('Descripción')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "¡La clave ya existe!"),
    ]