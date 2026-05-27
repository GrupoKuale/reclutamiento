from odoo import http, exceptions
from odoo.http import request
import  json, re, hashlib
from ..utils import json_response, authenticate
class EmployeeManagementController(http.Controller):

    @http.route('/api/employee/list', type='http', auth='none', methods=['GET'], csrf=False)
    def list_employees(self):
        try:
            employee_id = authenticate()
            
            if isinstance(employee_id, http.Response):
                return employee_id
                
            employees = request.env['hr.employee'].sudo().search([('id', '!=', employee_id)])
            employee_list = []
            for employee in employees:
                full_name = f"{employee.name or ''} {employee.last_name or ''} {employee.last_name2 or ''}".strip()
                employee_list.append({
                    'id': employee.id,
                    'name':full_name,
                    'job_id': employee.job_id.name,
                    'department_id': employee.department_id.name,
                    'work_contact_id': employee.work_contact_id.id,
                })
            return json_response(success=True, employee=employee_list, status=200)
            
        except Exception as e:
            return json_response(success=False, error=str(e), status=500)

    @http.route('/api/employee/register', type='http', auth='none', methods=['POST'], csrf=False)
    def register(self, **kwargs):
        try:
            data = request.httprequest.json
            new_employee = request.env['hr.employee'].sudo().create(data)
            return json_response(success=True, employee={'employee_id': new_employee.id, 'employee_name': new_employee.name}, status=200)

        except exceptions.ValidationError as e:
            return json_response(success=False, error=str(e), status=400)
        except exceptions.AccessError as e:
            return json_response(success=False, error='Access denied', status=403)
        except Exception as e:
            return json_response(success=False, error=f'An unexpected error occurred: {str(e)}', status=500)
        
    
    @http.route('/api/employee/update', type='http', auth='none', methods=['PUT'], csrf=False)
    def update(self, **kwargs):

        employee_id = authenticate()
        if isinstance(employee_id, http.Response):
            return employee_id
        
        
        data = request.httprequest.json
        
        employee_id = data.get('employee_id')
        updates = data.get('updates', {})

        if not employee_id or not updates:
            return json_response(success=False, error='Employee ID and updates are required', status=400)
            
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        
        if not employee.exists():
            return json_response(success=False, error='Employee not found', status=404)
        
        try:
            full_name = f"{employee.name or ''} {employee.last_name or ''} {employee.last_name2 or ''}".strip()
            if 'work_email' in updates and updates['work_email'] != employee.work_email:
                employee.sudo().write(updates)
                request.session.logout()
                return json_response(success=True, employee={'employee_id': employee.id, 'employee_name': full_name}, status=200)
            
            if 'password' in updates:
                employee._validate_password(updates['password'])
            
            employee.sudo().write(updates)

            return json_response(success=True, employee={'employee_id': employee.id, 'employee_name': full_name}, status=200)
            
        except exceptions.ValidationError as e:
            return json_response(success=False, error=str(e), status=400)
            
        except exceptions.AccessError as e:
            return json_response(success=False, error='Access denied', status=403)
            
        except Exception as e:
            return json_response(success=False, error=f'An unexpected error occurred: {str(e)}', status=500)
            
        
