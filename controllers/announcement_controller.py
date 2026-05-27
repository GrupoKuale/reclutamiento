from datetime import datetime
from odoo import http
from odoo.http import request
import json
from ..utils import json_response, authenticate

class EmployeeAnnouncementController(http.Controller):

    @http.route('/api/announcement/create', type='http', auth='none', methods=['POST'], csrf=False)
    def create_announcement(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            
            data = request.httprequest.json
            data['postedBy'] = employee.user_id.id
            announcement = request.env['reclutamiento__kuale.employee.announcement'].sudo().create(data)

            return json_response(success=True, announcement={'announcement_id': announcement.id, 'title':announcement.header}, status=201)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)

    @http.route('/api/announcement', type='http', auth='none', methods=['GET'], csrf=False)
    def get_my_announcements(self):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
           
            announcements = request.env['reclutamiento__kuale.employee.announcement'].sudo().search([], order='create_date desc')

            announcement_data = [{
                'id': ann.id,
                'header': ann.header,
                'image_url': ann.image_url,
                'postedBy': ann.postedBy.name,
                'reaction_ids': [
                    {
                        'reaction_type': reaction.reaction_type,
                        'employee_id': request.env['hr.employee'].sudo().search([('user_id', '=', reaction.user_id.id)], limit=1).id,
                        'name': request.env['res.partner'].sudo().search([('user_id', '=', reaction.user_id.id)], limit=1).name,
                        'partner_id': reaction.user_id.partner_id.id
                    } for reaction in ann.reaction_ids
                ],
                'create_date': ann.create_date.isoformat() if isinstance(ann.create_date, datetime) else ann.create_date,
            } for ann in announcements]
            return json_response(success=True, announcement=announcement_data, status=200)
        except Exception as e: 
            return json_response(success=False, error=str(e), status=500)
        
        
    @http.route('/api/announcement/<int:announcement_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_announcement(self, announcement_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            announcement = request.env['reclutamiento__kuale.employee.announcement'].sudo().browse(announcement_id)
            if not announcement.exists():
                return json_response(success=False, error='Announcement not found', status=404)

            announcement_data = {
                'id': announcement.id,
                'header': announcement.header,
                'image_url': announcement.image_url,
                'posted_by': announcement.postedBy.id,
                'reaction_ids': [
                    {
                        'reaction_type': reaction.reaction_type,
                        'employee_id': request.env['hr.employee'].sudo().search([('user_id', '=', reaction.user_id.id)], limit=1).id,
                        'name': request.env['res.partner'].sudo().search([('user_id', '=', reaction.user_id.id)], limit=1).name,
                        'partner_id': reaction.user_id.partner_id.id
                    }
                    for reaction in announcement.reaction_ids
                ],
                'create_date': announcement.create_date.isoformat() if isinstance(announcement.create_date, datetime) else announcement.create_date,
            }
            return json_response(success=True, announcement=announcement_data, status=200)
        except Exception as e:
            return json_response(success=False, error=str(e), status=500)

    @http.route('/api/announcement/<int:announcement_id>/react', type='http', auth='none', methods=['POST'], csrf=False)
    def add_or_update_reaction(self, announcement_id, **kwargs):
        try:
            
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)

            data = request.httprequest.json
            reaction_type = data.get('reaction_type')

            if not reaction_type:
                return json_response(success=False, error='Missing required field: reaction_type', status=400)
           
            announcement = request.env['reclutamiento__kuale.employee.announcement'].sudo().browse(announcement_id)
            if not announcement.exists():
                return json_response(success=False, error='Announcement not found', status=404)

            existing_reaction = request.env['reclutamiento__kuale.generic.reaction'].sudo().search([
                ('res_model', '=', 'reclutamiento__kuale.employee.announcement'),
                ('res_id', '=', announcement_id),
                ('user_id', '=', employee.user_id.id),
            ], limit=1)

            reaction_vals = {
                'reaction_type': reaction_type,
                'user_id': employee.user_id.id,
                'res_model': 'reclutamiento__kuale.employee.announcement',
                'res_id': announcement_id,
            }

            if existing_reaction:
                existing_reaction.sudo().write(reaction_vals)
            else:
                request.env['reclutamiento__kuale.generic.reaction'].sudo().create(reaction_vals)
            return json_response(success=True, announcement="reaction added successfully", status=201)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/announcement/<int:announcement_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_announcement(self, announcement_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)

            announcement = request.env['reclutamiento__kuale.employee.announcement'].sudo().browse(announcement_id)
            if not announcement.exists():
                return json_response(success=False, error='Announcement not found', status=404)
            
            if announcement.postedBy.id != employee.user_id.id:
                return json_response(success=False, error='Access denied', status=403)

            announcement.sudo().unlink()
            return json_response(success=True, announcement="Announcement deleted successfully", status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)

