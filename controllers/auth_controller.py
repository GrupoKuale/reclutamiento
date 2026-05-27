from odoo import http, exceptions, fields
from odoo.http import request
import hashlib, base64, json
from ..utils import json_response, authenticate

class AuthController(http.Controller):
    @http.route('/api/employee/login', type='http', auth='none', methods=['POST'], csrf=False)
    def login(self):
        data = request.httprequest.json

        username = data.get('username')
        password = data.get('password')
        device_token = data.get('device_token')

        if not username or not password:
            return json_response(success=False, error='Username and password are required', status=400)
        
        employee = request.env['hr.employee'].sudo().search([('username', '=', username)], limit=1)
        
        if not employee:
            return json_response(success=False, error='Invalid username or password', status=401)
            
       
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if employee.password != hashed_password:
            return json_response(success=False, error='Invalid username or password', status=401)
        
        request.session['employee_id'] = employee.id

        partner_id = employee.work_contact_id.id

        if device_token:
            existing_token = request.env['partner.device.token'].sudo().search([
                ('partner_id', '=', partner_id),
                ('device_token', '=', device_token)
            ], limit=1)

            if existing_token:
                
                existing_token.sudo().write({'last_login': fields.Datetime.now()})
            else:
                
                request.env['partner.device.token'].sudo().create({
                    'partner_id': partner_id,
                    'device_token': device_token,
                    'last_login': fields.Datetime.now()
                })

        full_name = f"{employee.name or ''} {employee.last_name or ''} {employee.last_name2 or ''}".strip()
        return request.make_response(
            json.dumps({
                'success': True,
                'session_id': request.session.sid,
                'employee_id': employee.id,
                'employee_name': full_name,
            }),
            headers={'Content-Type': 'application/json'},
            status=200
        )
    
    @http.route('/api/employee/logout', type='http', auth='none', methods=['POST'], csrf=False)
    def logout(self):
        if request.session.get('employee_id'):
            employee_id = authenticate()
            data = request.httprequest.json
            device_token = data.get('device_token')
            if not device_token:
                return json_response(success=False, error='Device token is required', status=400)
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            partner_id = employee.work_contact_id.id
            token_to_remove = request.env['partner.device.token'].sudo().search([
                ('partner_id', '=', partner_id),
                ('device_token', '=', device_token)
            ], limit=1)

        if token_to_remove:
            token_to_remove.sudo().unlink()
            request.session.logout()

            return json_response(success=True, message='Logged out successfully', status=200)
            
        else:
            return json_response(success=False, error='No active session', status=400)