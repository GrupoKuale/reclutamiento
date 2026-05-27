from odoo import http
from odoo.http import request
import json
from ..utils import json_response, authenticate

class EmployeeTodoController(http.Controller):

    @http.route('/api/todo', type='http', auth='none', methods=['POST'], csrf=False)
    def create_todo(self, **kwargs):
        try:
            
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)

            data = request.httprequest.json
            data['userId'] = employee.user_id.id

            todo = request.env['reclutamiento__kuale.employee.todo'].sudo().create(data)

            return json_response(success=True, task={"id": todo.id, "title": todo.title}, status=201)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/todo', type='http', auth='none', methods=['GET'], csrf=False)
    def get_all_todos(self, **kwargs):
        try:
            
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)

            todos = request.env['reclutamiento__kuale.employee.todo'].sudo().search([('userId', '=', employee.user_id.id)])

            if not todos:
                return json_response(success=True, task=[], status=200)

            todos_data = [{
                "id": todo.id,
                "title": todo.title,
                "description": todo.description,
                "status": todo.status,
                "dueDate":todo.dueDate.isoformat() if todo.dueDate else None,
                "completedDate": todo.completedDate.isoformat() if todo.completedDate else None,
                "employee_id": employee_id
            } for todo in todos]

            return json_response(success=True, task=todos_data, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/todo/<int:todo_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_todo(self, todo_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            
            todo = request.env['reclutamiento__kuale.employee.todo'].sudo().browse(todo_id)
            if not todo.exists():
                return json_response(success=False, error="Todo not found", status=404)
            
            if todo.userId.id != employee.user_id.id:
                return json_response(success=False, error="Access denied: Not your todo", status=403)

            todo_data = {
                "id": todo.id,
                "title": todo.title,
                "description": todo.description,
                "status": todo.status,
                "dueDate": todo.dueDate.isoformat() if todo.dueDate else None,
                "completedDate": todo.completedDate.isoformat() if todo.completedDate else None,
                "employee_id": employee_id
            }
            return json_response(success=True, task=todo_data, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/todo/<int:todo_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_todo(self, todo_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            employee = request.env['hr.employee'].sudo().browse(employee_id)

            data = request.httprequest.json

            todo = request.env['reclutamiento__kuale.employee.todo'].sudo().browse(todo_id)
            if not todo.exists():
                return json_response(success=False, error="Todo not found", status=404)
            
            if todo.userId.id != employee.user_id.id:
                return json_response(success=False, error="Access denied: Not your todo", status=403)

            todo.write(data)

            return json_response(success=True, task="Todo updated successfully", status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/todo/<int:todo_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_todo(self, todo_id, **kwargs):
        try:

            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)

            todo = request.env['reclutamiento__kuale.employee.todo'].sudo().browse(todo_id)
            if not todo.exists():
                return json_response(success=False, error="Todo not found", status=404)
            
            if todo.userId.id != employee.user_id.id:
                return json_response(success=False, error="Access denied: Not your todo", status=403)
            
            todo.unlink()

            return json_response(success=True, data="Todo deleted successfully", status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)