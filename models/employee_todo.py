from odoo import api, fields, models
from datetime import date


class EmployeeTodo(models.Model):
    _name = 'reclutamiento__kuale.employee.todo'
    _description = 'Tareas de los empleados'

    title = fields.Char(string='Título',help="Palabras clave de la tarea")
    description = fields.Text(string='Descripción',help="Descripción detallada de la tarea")
    status = fields.Selection(
        [
            ('pending', 'Pendiente'),
            ('completed', 'Completada'),
        ],
        default='pending', string='Estado'
    )
    dueDate = fields.Date(string='Fecha límite')
    completedDate = fields.Date(string='Fecha de completado')
    userId = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)

    @api.model
    def create(self, vals):
        if 'userId' not in vals:
            vals['userId'] = self.env.user.id
        if vals.get('status') == 'completed':
            vals['completedDate'] = date.today()
        return super(EmployeeTodo, self).create(vals)

    def write(self, vals):
        if vals.get('status') == 'completed':
            vals['completedDate'] = date.today()
        elif 'status' in vals and vals['status'] != 'completed':
            vals['completedDate'] = False
        return super(EmployeeTodo, self).write(vals)
