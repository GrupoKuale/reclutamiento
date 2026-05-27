from odoo import http, exceptions
from odoo.http import request
import hashlib, base64, json
from ..utils import json_response, authenticate

class EmployeeProfileController(http.Controller):
    @http.route('/api/employee/profile/<int:profile_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_employee_work_profile(self, profile_id):
        try:
            employee_id =authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            if employee_id != profile_id:
                return json_response(success=False, error='Access denied', status=403)
                
            target_employee = request.env['hr.employee'].sudo().browse(profile_id)

            if not target_employee.exists():
                return json_response(success=False, error='Employee profile not found', status=404)

            fields_to_read = [       
                'mobile_phone',  
                'work_phone',   
                'work_email',  
                'username',  
                'department_id', 
                'job_id',       
                'parent_id',     
                'coach_id',      
                'company_id',   
                'work_contact_id',
                "image_url"
            ]

            employee_data = target_employee.read(fields_to_read)[0]
            
            employee_data['name'] = f"{target_employee.name or ''} {target_employee.last_name or ''} {target_employee.last_name2 or ''}".strip()

            return request.make_response(
                json.dumps({
                    'success': True,
                    'employee_work_profile': employee_data,
                }),
                headers={'Content-Type': 'application/json'},
                status=200
            )
        except Exception as e:

            error_message = str(e)
            return json_response(success=False, error=error_message, status=500)
            