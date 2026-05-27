from odoo import http
from odoo.http import request
import json
from ..utils import authenticate, json_response, clean_html
from pytz import timezone

class DiscussChannelController(http.Controller):

    @http.route('/api/channel', type='http', auth='none', methods=['POST'], csrf=False)
    def create_channel(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            partner_id = employee.work_contact_id.id
            
            channel_data = request.httprequest.json
            channel_partner_ids = channel_data.get('channel_partner_ids')
            channel_partner_ids.append(partner_id)

            if not channel_partner_ids or len(channel_partner_ids) < 2:
                return json_response(success=False, error='Invalid partners. Must have at least 2 partners.', status=400)
            
            if not channel_data.get('channel_type'):
                channel_data['channel_type'] = 'chat' if len(channel_partner_ids) == 2 else 'group'
            else:
                if channel_data['channel_type'] not in ['chat', 'group', 'channel']:
                    return json_response(success=False, error='Invalid channel type.', status=400)
                
                channel_data['channel_type'] = 'chat' if len(channel_partner_ids) == 2 else channel_data['channel_type']
            
            if 'channel_partner_ids' in channel_data:
                formatted_attendees = []
                for attendee in channel_data['channel_partner_ids']:
                    formatted_attendees.append([6, 0, attendee])
                channel_data['channel_partner_ids'] = formatted_attendees

            new_channel = request.env['discuss.channel'].sudo().create(channel_data)

            return json_response(success=True, data=new_channel.id, status=201)
        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/channel/list', type='http', auth='none', methods=['GET'], csrf=False)
    def list_user_channels(self, **kwargs):
        try:
           
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            partner_id = employee.work_contact_id.id

            user_channels = request.env['discuss.channel'].sudo().search([
                ('channel_partner_ids', 'in', [partner_id])
            ])

            channels_data = [{
                'id': channel.id,
                'name': channel.name,
                'channel_type': channel.channel_type,  
                'members': [{'id': partner.id, 'name': partner.name} for partner in channel.channel_partner_ids]
            } for channel in user_channels]

            return json_response(success=True, data=channels_data, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    
    @http.route('/api/channel/<int:channel_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_channel_messages(self, channel_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            partner_id = employee.work_contact_id.id 

            channel = request.env['discuss.channel'].sudo().browse(channel_id)
            if not channel.exists():
                return json_response(success=False, error='Channel not found', status=404)

            messages = request.env['mail.message'].sudo().search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', channel_id)
            ], order='date asc')
            user_tz = timezone(request.env.user.tz or 'UTC')

            messages_data = [{
                'id': message.id,
                'body': clean_html(message.body),
                'date': message.date.astimezone(user_tz).isoformat() if message.date else None,
                'author_id': message.author_id.id,
                'author_name': message.author_id.name,
                'is_mine': message.author_id.id == partner_id  
            } for message in messages]

            channel_data = {
                'id': channel.id,
                'name': channel.name,
                'channel_type': channel.channel_type,
                'members': [{'id': partner.id, 'name': partner.name} for partner in channel.channel_partner_ids],
                'messages': messages_data
            }

            return json_response(success=True, data=channel_data, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
    
    @http.route('/api/channel/<int:channel_id>/message', type='http', auth='none', methods=['POST'], csrf=False)
    def send_message(self, channel_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            data = request.httprequest.json
            message_body = data.get('message')
            if not data.get('message'):
                return json_response(success=False, error='Message content is required.', status=400)

            channel = request.env['discuss.channel'].sudo().browse(channel_id)
            if not channel.exists():
                return json_response(success=False, error='Channel not found.', status=404)

            employee = request.env['hr.employee'].sudo().browse(employee_id)
            partner_id = employee.work_contact_id.id

            partner_ids = channel.channel_partner_ids.ids

            channel.message_post(
                body=clean_html(message_body), 
                message_type='comment', 
                subtype_xmlid='mail.mt_comment',  
                author_id=partner_id, 
                partner_ids=partner_ids
            )

            return json_response(success=True, message='Message sent successfully.', status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/channel/<int:channel_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_channel(self, channel_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            channel = request.env['discuss.channel'].sudo().browse(channel_id)
            if not channel.exists():
                return json_response(success=False, error='Channel not found.', status=404)

            channel.unlink()

            return json_response(success=True, message='Channel deleted successfully.', status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)

 