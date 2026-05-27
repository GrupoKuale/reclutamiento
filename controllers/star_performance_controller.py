from odoo import http, exceptions
from odoo.http import request
import json
from ..utils import json_response, authenticate, format_dates

class StarPerformance(http.Controller):

    @http.route('/api/my-stars', type='http', auth='none', methods=['GET'], csrf=False)
    def get_star_performance(self, **kwargs):
        try:
            employee_id = authenticate()
            if not employee_id:
                return json_response(success=False, error='Not authenticated', status=401)
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee.exists():
                return json_response(success=False, error='Employee not found', status=404)
            
            is_management = employee.department_id and employee.department_id.name and employee.department_id.name.lower() == 'management'
            
            if is_management:
                
                employees = request.env['hr.employee'].sudo().search([])
            else:

                employees = employee

            all_performance_data = []
            
            for emp in employees:
                enrolled_courses = request.env['slide.channel.partner'].sudo().search([
                    ('partner_id', '=', emp.user_id.partner_id.id)
                ])
                
                courses_data = []
                for enrollment in enrolled_courses:
                    course_data = {
                        'course_id': enrollment.channel_id.id,
                        'course_name': enrollment.channel_id.name,
                        'completed': enrollment.completion >= 100,
                        'completion_percentage': enrollment.completion,
                        'completed_slides_count': enrollment.completed_slides_count
                    }
                    courses_data.append(course_data)
                
                full_name = f"{emp.name or ''} {emp.last_name or ''} {emp.last_name2 or ''}".strip()
                
                performance_data = {
                    'employee_id': emp.id,
                    'employee_name': full_name,
                    'courses': courses_data
                }
                
                all_performance_data.append(performance_data)
            
            return json_response(success=True, data=all_performance_data, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/top10', type='http', auth='none', methods=['GET'], csrf=False)
    def get_top10_star_performance(self, **kwargs):
        try:

            employee_id = authenticate()
            if not employee_id:
                return json_response(success=False, error='No autenticado', status=401)
            
            authenticated_employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not authenticated_employee.exists():
                return json_response(success=False, error='Empleado no encontrado', status=404)

            employees = request.env['hr.employee'].sudo().search([])

            employee_data = [
                {
                    'employee_id': emp.id,
                    'employee_name': f"{emp.name or ''} {emp.last_name or ''} {emp.last_name2 or ''}".strip(),
                    'completed_courses': request.env['slide.channel.partner'].sudo().search_count([
                        ('partner_id', '=', emp.work_contact_id.id),
                        ('completion', '>=', 100)
                    ])
                }
                for emp in employees
            ]
            employee_data_sorted = sorted(employee_data, key=lambda x: x['completed_courses'], reverse=True)
            for idx, emp in enumerate(employee_data_sorted):
                emp['position'] = idx + 1

            top_10 = employee_data_sorted[:10]

            authenticated_employee_data = next((emp for emp in employee_data_sorted if emp['employee_id'] == authenticated_employee.id), None)

            if authenticated_employee_data and authenticated_employee_data not in top_10:
                top_10.append(authenticated_employee_data)

            return json_response(success=True, data=top_10, status=200)

        except Exception as e:
            # Manejo de errores
            return json_response(success=False, error=str(e), status=500)
