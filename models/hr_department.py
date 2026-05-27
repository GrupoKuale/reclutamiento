from odoo import fields, models, api


class hr_department(models.Model):
    _inherit = 'hr.department'

    acronym = fields.Char('Acrónimo', required=True, translate=True, size=3)
    segment_ids = fields.Many2many(
        'reclutamiento__kuale.segments', 'department_segment_rel',
        'dep_id', 'segment_id', string='Segmentos')
    internal_name = fields.Char('Nombre interno')
    # category_ids = fields.Many2many(
    #    'hr.employee.category', 'employee_category_rel',
    #    'emp_id', 'category_id', groups="hr.group_hr_user",
    #    string='Tags')

    # min_employees = fields.Integer(string='Minimum Employees', required=True)
    # max_employees = fields.Integer(string='Maximum  Employees', required=True)

    @api.onchange('acronym')
    def set_caps(self):
        acronym_aux = str(self.acronym)
        self.acronym = acronym_aux.upper()