from odoo import http, fields
from odoo.http import request
from odoo.exceptions import UserError
from ..utils import authenticate, json_response

class AttendanceController(http.Controller):

    @http.route('/api/attendance/check_in', type='http', auth='none', methods=['POST'], csrf=False)
    def check_in(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            data = request.httprequest.json
            in_latitude = data.get('latitude')
            in_longitude = data.get('longitude')

            if not in_latitude or not in_longitude:
                return json_response(success=False, error='Latitude and longitude are required', status=400)
            
            work_location = request.env['hr.employee'].sudo().browse(employee_id).work_location_id
            if not work_location:
                return json_response(success=False, error="Employee does not have a work location assigned", status=400)


            attendance = request.env['hr.attendance'].sudo().create({
                'employee_id': employee_id,
                'check_in': fields.Datetime.now(),
                'in_latitude': in_latitude,
                'in_longitude': in_longitude
            })

            return json_response(success=True, data=attendance.id, status=201)

        except UserError as e:
            return json_response(success=False, error=str(e), status=400)
        except Exception as e:
           return json_response(success=False, error='An unexpected error occurred', status=500)
        
    @http.route('/api/attendance/check_out', type='http', auth='none', methods=['PUT'], csrf=False)
    def check_out(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            data = request.httprequest.json
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            if not latitude or not longitude:
                return json_response(success=False, error='Latitude and longitude are required', status=400)

            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee_id),
                ('check_out', '=', False)
            ], limit=1)

            if not attendance:
                return json_response(success=False, error="No check-in found to check-out.", status=400)

            employee = request.env['hr.employee'].sudo().browse(employee_id)
            work_location = employee.work_location_id

            if not work_location:
                return json_response(success=False, error="Employee does not have a work location assigned", status=400)

            attendance.write({
                'employee_id': employee_id,
                'check_out': fields.Datetime.now(),
                'out_latitude': latitude,
                'out_longitude': longitude
            })

            return json_response(success=True, data=attendance.id, status=200)

        except UserError as e:
            return json_response(success=False, error=str(e), status=400)
        except Exception as e:
            return json_response(success=False, error='An unexpected error occurred', status=500)

 