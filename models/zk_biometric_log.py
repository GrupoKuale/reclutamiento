from odoo import models, fields, api
from datetime import datetime


class ZktecoLog(models.Model):
    _name = 'reclutamiento__kuale.zkteco_log'
    _description = 'Zkteco clock log module'

    @api.constrains('punching_time', 'employee_id')
    def _check_validity(self):
        """
        Validar que los registros de asistencia sean coherentes,
        como no permitir tiempos duplicados o inconsistentes.
        """
        # Puedes implementar las reglas de validación aquí.
        pass

    device_employee_id = fields.Char(
        string='ID del Dispositivo Biométrico',
        help="El ID del empleado en el dispositivo biométrico",
        required=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        compute='_compute_employee_id',
        store=True,
        help="Empleado asociado basado en el ID del dispositivo"
    )
    action = fields.Selection([
        ('0', 'Check In'),
        ('1', 'Check Out'),
        ('2', 'Break Out'),
        ('3', 'Break In'),
        ('4', 'Overtime In'),
        ('5', 'Overtime Out'),
        ('255', 'Duplicate')
    ], string='Tipo de Acción', required=True)

    attendance_type = fields.Selection([
        ('1', 'Finger'),
        ('15', 'Face'),
        ('2', 'Type_2'),
        ('3', 'Password'),
        ('4', 'Card'),
        ('255', 'Duplicate')
    ], string='Método de Asistencia', required=True)

    punching_time = fields.Datetime(
        string='Hora de Registro',
        help="Fecha y hora del registro de asistencia",
        required=True
    )

    work_location = fields.Many2one(
        'hr.work.location',
        string='Lugar de Trabajo',
        help="Ubicación del lugar de trabajo del empleado"
    )

    migrated = fields.Boolean(string='Migrado', default=False,
                              help='Indica si el registro ha sido migrado a la asistencia')

    @api.depends('device_employee_id')
    def _compute_employee_id(self):
        for record in self:
            employee = self.env['hr.employee'].search(
                [('device_id_num', '=', record.device_employee_id)], limit=1
            )
            record.employee_id = employee.id if employee else False

    # cron activity migrate to attendance model


    @api.model
    def migrate_information(self):
        print("CRON JOB EXECUTION STARTED")
        zkteco_logs = self.env['reclutamiento__kuale.zkteco_log'].search([
            ('employee_id','!=',False),
            ('migrated','=',False),
        ],order='punching_time asc')

        for log in zkteco_logs:

            if log.migrated:
                continue

            existing_attendance = self.env['hr.attendance'].search([
                ('employee_id', '=', log.employee_id.id),
                ('check_out', '=', False)
            ], limit=1)

            if not existing_attendance:
                if log.action == "0":
                    attendance = self.env['hr.attendance'].create({
                        'employee_id': log.employee_id.id,
                        'check_in': log.punching_time,
                        'in_latitude': log.work_location.latitude,
                        'in_longitude': log.work_location.longitude,
                    })
                else:
                    continue
                print("check in for employee: {}".format(log.employee_id))
            else:
                if log.action == "1":
                    last_check = log.punching_time
                else:
                    next_checkout = self.env['reclutamiento__kuale.zkteco_log'].search([
                        ('employee_id', '=', log.employee_id.id),
                        ('punching_time', '>', existing_attendance.check_in),
                        ('action', '=', "1")  # Check out
                    ], order='punching_time asc', limit=1)

                    if next_checkout:
                        last_check = next_checkout[0].punching_time
                    else:
                        logs = self.env['reclutamiento__kuale.zkteco_log'].search([
                            ('employee_id', '=', log.employee_id.id),
                            ('punching_time', '>=', fields.Date.today()),  # Logs de hoy
                            ('action', '=', 0)
                        ], order='punching_time desc', limit=1)
                        if logs:
                            last_check = logs[0].punching_time
                    # if logs:
                    #     last_check = logs[0].punching_time
                    # else:
                    #     last_check = fields.Datetime.to_string(datetime.combine(fields.Date.today(), datetime.max.time()))

                existing_attendance.write({
                    'employee_id': log.employee_id.id,
                    'check_out': last_check,
                    'out_latitude': log.work_location.latitude,
                    'out_longitude': log.work_location.longitude,
                })
                print('check out for employee: {}'.format(log.employee_id))

                # mark as migrated the inbetween logs
                merged_logs = self.env['reclutamiento__kuale.zkteco_log'].search([
                    ('employee_id', '=', log.employee_id.id),
                    ('punching_time', '>=', existing_attendance.check_in),
                    ('punching_time', '<=', last_check),
                ])

                if merged_logs:
                    merged_logs.write({'migrated': True})

            log.write({'migrated': True})
        print("CRON JOB EXECUTION FINISHED")
