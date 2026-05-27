from odoo import http
from odoo.http import request
import json
from ..utils import json_response, authenticate, format_dates

class EmployeeRequestController(http.Controller):

    @http.route('/api/employee/request/create', type='http', auth='none', methods=['POST'], csrf=False)
    def create_request(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            

            data = request.httprequest.json
            request_type = data.get('requestType')
            request_description = data.get('requestDescription')

            if request_type not in ['work', 'loan', 'labor_letter', 'uniform', 'vacation', 'expenses']:
                return json_response(success=False, error='Invalid request type', status=400)

            
            existing_request = request.env['reclutamiento__kuale.employee.request'].sudo().search([
                ('requestedBy', '=', employee.user_id.id),
                ('status', '=', 'pending'),
                ('requestType', '=', request_type)
            ])
            if existing_request:
                return json_response(success=False, error='You already have a pending request of this type', status=400)

            specific_request = request.env[f'reclutamiento__kuale.employee.request.{request_type}'].sudo().create(data.get('specific_request_data', {}))

            new_request = request.env['reclutamiento__kuale.employee.request'].sudo().create({
                'requestType': request_type,
                'requestDescription': request_description,
                'requestedBy': employee.user_id.id,
                f'{request_type}RequestId': [(6, 0, [specific_request.id])],
            })

            return json_response(success=True, requested={'request_id':new_request.id, 'requested_by': new_request.requestedBy.id }, status=201)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/request', type='http', auth='none', methods=['GET'], csrf=False)
    def get_all_requests(self):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            requests = request.env['reclutamiento__kuale.employee.request'].sudo().search([])

            request_data = [{
                'id': req.id,
                'folio': req.folio,
                'requestType': req.requestType,
                'requestDescription': req.requestDescription,
                'requestedBy': req.requestedBy.name,
                'status': req.status,
                'specific_request_data': format_dates(req[req.requestType + 'RequestId'].read()[0])
            } for req in requests]

            return json_response(success=True, requested=request_data, status=200)
        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/employee/request', type='http', auth='none', methods=['GET'], csrf=False)
    def get_my_requests(self):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            requests = request.env['reclutamiento__kuale.employee.request'].sudo().search([('requestedBy', '=', employee.user_id.id)])

            request_data = [{
                'id': req.id,
                'folio': req.folio,
                'requestType': req.requestType,
                'requestDescription': req.requestDescription,
                'requestedBy': req.requestedBy.name,
                'status': req.status,
                'specific_request_data':format_dates(req[req.requestType + 'RequestId'].read()[0])
            } for req in requests]

            return json_response(success=True, requested=request_data, status=200)
        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/request/<int:request_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_request(self, request_id, **kwargs):
        try:
            
            request_data = request.env['reclutamiento__kuale.employee.request'].sudo().browse(request_id)
            if not request_data.exists():
                return json_response(success=False, error='Request not found', status=404)

            return json_response(success=True, requested={
                'id': request_data.id,
                'folio': request_data.folio,
                'requestType': request_data.requestType,
                'requestDescription': request_data.requestDescription,
                'requestedBy': request_data.requestedBy.name,
                'status': request_data.status,
                'specific_request_data': format_dates(request_data[request_data.requestType + 'RequestId'].read()[0])
            }, status=200)
        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/request/<int:request_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_request(self, request_id, **kwargs):
        try:
            employee_id = authenticate()
            if not employee_id:
                return json_response(success=False, error='Unauthorized', status=401)
            
            request_data = request.env['reclutamiento__kuale.employee.request'].sudo().browse(request_id)
            if not request_data.exists():
                return json_response(success=False, error='Request not found', status=404)

            data = request.httprequest.json
            status = data.get('status')
            if status not in ['pending', 'approved','rejected','cancelled','closed']:
                return json_response(success=False, error='Invalid status', status=400)
            if request_data.status != 'pending' and status == 'pending':
                return json_response(success=False, error="You cannot revert to 'pending' status once it has been changed.", status=400)

            request_data.status = status

            return json_response(success=True, requested={
                'id': request_data.id,
                'folio': request_data.folio,
                'requestType': request_data.requestType,
                'requestDescription': request_data.requestDescription,
                'requestedBy': request_data.requestedBy.name,
                'status': request_data.status,
                'specific_request_data': format_dates(request_data[request_data.requestType + 'RequestId'].read()[0])
            }, status=200)
        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/request/<int:request_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_request(self, request_id, **kwargs):
        try:
            employee_id = authenticate()
            if not employee_id:
                return json_response(success=False, error='Unauthorized', status=401)
            
            request_data = request.env['reclutamiento__kuale.employee.request'].sudo().browse(request_id)
            if not request_data.exists():
                return json_response(success=False, error='Request not found', status=404)

            request_data.unlink()

            return json_response(success=True, requested='Request deleted successfully', status=200)
        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
