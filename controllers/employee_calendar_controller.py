from odoo import http
from odoo.http import request
import json
from datetime import datetime
from ..utils import json_response, authenticate, clean_html
import logging
logger = logging.getLogger(__name__)

class EmployeeCalendarController(http.Controller):

    @http.route('/api/calendar/events', type='http', auth='none', methods=['GET'], csrf=False)
    def get_user_events(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee.exists():
                return json_response(success=False, error='Employee not found', status=404)

            partner_id = employee.work_contact_id.id

            events = request.env['calendar.event'].sudo().search([
                '|',
                ('user_id', '=', employee.user_id.id), 
                ('attendee_ids.partner_id', '=', partner_id)
            ])       

            events_data = [self._get_event_details(event) for event in events]

            return json_response(success=True, data=events_data, status=200)

        except Exception as e:
            logger.error(e, exc_info=True)
            return json_response(success=False, error=str(e), status=500)



    @http.route('/api/calendar/event/create', type='http', auth='none', methods=['POST'], csrf=False)
    def create_event(self, **kwargs):
        try:

            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            data = request.httprequest.json

            employee = request.env['hr.employee'].sudo().browse(employee_id)
            if not employee.exists():
                return json_response(success=False, error='Employee not found', status=404)
            
            data['user_id'] = employee.user_id.id

            required_fields = ['name', 'start', 'stop', 'allday']

            for field in required_fields:
                if field not in data:
                    return json_response(success=False, error=f'Missing required field: {field}', status=400)
            
            if 'attendee_ids' in data:
                formatted_attendees = []
                for attendee in data['attendee_ids']:
                    formatted_attendees.append([0, 0, attendee])
                data['attendee_ids'] = formatted_attendees

            event = request.env['calendar.event'].sudo().create(data)

            return json_response(success=True, data={
                      'event_id': event.id,
                    'event_name': event.name
                }, status=201)

        except Exception as e:
           
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/calendar/event/<int:event_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_event(self, event_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            event = request.env['calendar.event'].sudo().browse(event_id)
            if not event.exists():
                return json_response(success=False, error='Event not found', status=404)

            event_data = self._get_event_details(event)
            return json_response(success=True, data=event_data, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    
    @http.route('/api/calendar/event/<int:event_id>/update', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_event(self, event_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            employee = request.env['hr.employee'].sudo().browse(employee_id)

            event_env = request.env['calendar.event'].with_user(employee.user_id.id).sudo()
            data = request.httprequest.json
            
            event = event_env.browse(event_id)
            if not event.exists():
                return json_response(success=False, error='Event not found', status=404)

            if 'attendee_ids' in data:
                existing_partners = event.attendee_ids.mapped('partner_id.id')
                new_attendees = [
                    attendee for attendee in data['attendee_ids']
                    if attendee['partner_id'] not in existing_partners
                ]

                data['attendee_ids'] = [
                    [0, 0, attendee] for attendee in new_attendees
                ]
            event.write(data)

            return json_response(success=True, data="Event updated successfully", status=200)

        except Exception as e:
            
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/calendar/event/<int:event_id>/attendee/<int:partner_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_attendee_state(self, event_id, partner_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            event = request.env['calendar.event'].sudo().browse(event_id)
            if not event.exists():
                return json_response(success=False, error='Event not found', status=404)

            attendee = event.attendee_ids.filtered(lambda a: a.partner_id.id == partner_id)
            if not attendee:
                return json_response(success=False, error='Attendee not found', status=404)

            data = request.httprequest.json
            new_state = data.get('state')

            if not new_state:
                return json_response(success=False, error="Missing 'state' in request", status=400)

            attendee.write({'state': new_state})

            return json_response(success=True, data=f"Attendee state updated to {new_state}", status=200)

        except Exception as e:

            return json_response(success=False, error=str(e), status=500)

        
    def _get_event_details(self, event):
        event_data = {
            'id': event.id,
            'name': event.name,
            'start': event.start.isoformat() if isinstance(event.start, datetime) else event.start,
            'stop': event.stop.isoformat() if isinstance(event.stop, datetime) else event.stop,
            'description': clean_html(event.description) if event.description else event.description,
            'allday': event.allday,
            'videocall_location': event.videocall_location,
            'course': event.course,
        }

        attendees_data = []
        for attendee in event.attendee_ids:
            partner = attendee.partner_id
            employee = request.env['hr.employee'].sudo().search([('work_contact_id', '=', partner.id)], limit=1)
            employee_name = None
            if employee:
                employee_name = f"{employee.name or ''} {employee.last_name or ''} {employee.last_name2 or ''}".strip()

            attendee_info = {
                'employee_id': employee.id if employee else None,
                'employee_name': employee_name,
                'partner_id': partner.id,
                'email': partner.email,
                'state': attendee.state
            }
            attendees_data.append(attendee_info)

        event_data['attendees'] = attendees_data
        return event_data