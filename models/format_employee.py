from odoo import _, models, fields, api


class FormatEmployee(models.Model):
    _name = 'reclutamiento__kuale.format_employee'
    _description = 'Formatos de empleado'

    name = fields.Char('Nombre', required=True)
    description = fields.Text('Descripcion del formato')
    body = fields.Html(
        'Cuerpo del formato',
        render_engine='qweb',
        render_options={'post_process': True},
        prefetch=True,
        translate=True,
        sanitize=False,
        help="Usa la sintaxis: <t t-out='object.CAMPO'></t> para insertar datos del candidato."
    )
    job_id = fields.Many2one(
        'hr.job',
        string='Puesto de trabajo',
        default=lambda self: self._context.get('job_id')
    )
    # Mantenemos type_format para compatibilidad con codigo existente
    # pero ahora es opcional
    type_format = fields.Selection([
        ('regulation',      'Reglamento recibido'),
        ('confidentiality', 'Carta de confidencialidad'),
        ('promissory',      'Pagare'),
        ('uniform_voucher', 'Vale de uniforme'),
    ], string='Tipo de Formato (legacy)',
       default=lambda self: self._context.get('type_format'),
       help='Campo legacy. Los nuevos formatos no requieren tipo.'
    )
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        return super(FormatEmployee, self).create(vals_list)

    def write(self, vals):
        return super(FormatEmployee, self).write(vals)