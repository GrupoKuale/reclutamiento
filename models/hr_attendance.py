from math import radians, sin, cos, sqrt, atan2
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def create(self, values):
        employee_id = values.get('employee_id')
        in_latitude = values.get('in_latitude')
        in_longitude = values.get('in_longitude')

        if employee_id:
            existing_attendance = self.sudo().search([
                ('employee_id', '=', employee_id),
                ('check_out', '=', False)
            ], limit=1)

            if existing_attendance:
                raise UserError(_(
                    "No se puede crear el registro de asistencia para {}, el empleado no se ha registrado desde {}."
                ).format(
                    existing_attendance.employee_id.name,
                    fields.Datetime.to_string(existing_attendance.check_in)
                ))

        self._check_company_range(employee_id, in_latitude, in_longitude)
        
        return super(HrAttendance, self).create(values)

    def write(self, values):
        employee_id = values.get('employee_id')
        out_latitude = values.get('out_latitude')
        out_longitude = values.get('out_longitude')
        self._check_company_range(employee_id, out_latitude, out_longitude)
        return super(HrAttendance, self).write(values)

    def _compute_distance(self, lat1, lon1, lat2, lon2):
        # Radius of the earth in kilometers
        R = 6371.0

        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Calculate the change in coordinates
        dlon = lon2 - lon1
        dlat = lat2 - lat1

        # Apply Haversine formula
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c

        return distance

    def _check_company_range(self, employee_id,latitude,longitude):
        
        employee = self.env['hr.employee'].sudo().browse(employee_id)
        if not employee.work_location_id:
            raise UserError(_("El empleado no tiene una ubicación de trabajo asignada."))
        work_location = employee.work_location_id
        subsidiary_latitude = work_location.latitude or 0.000000
        subsidiary_longitude = work_location.longitude or 0.0000000
        allowed_distance_meters = work_location.allowed_distance or 1100

        if not (latitude and longitude):
            raise UserError(_("Oopss! No se puede registrar la asistencia. Por favor, asegúrese de que la ubicación esté activada en su dispositivo."))

        distance_meters = self._compute_distance(
            subsidiary_latitude, subsidiary_longitude,
            latitude, longitude
        ) * 1000

        if distance_meters > allowed_distance_meters:
            raise UserError(_(
                "Estás fuera de la ubicación de la empresa. "
                "Por favor, asegúrate de estar dentro del radio permitido"
                "La distancia excede el radio permitido"
            ))
