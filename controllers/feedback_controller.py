from odoo import http
from odoo.http import request
import json
from ..utils import json_response, authenticate, format_dates, clean_html

class EmployeeFeedbackController(http.Controller):

    @http.route('/api/feedback/create', type='http', auth='none', methods=['POST'], csrf=False)
    def create_feedback(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            data = request.httprequest.json
            feedback_type = data.get('feedbackType')
            feedback = data.get('feedback')
            subject = data.get('subject')

            if not feedback_type or not feedback or not subject:
                return json_response(success=False, error='Missing required fields', status=400)

            new_feedback = request.env['reclutamiento__kuale.employee.feedback'].sudo().create({
                'feedbackType': feedback_type,
                'feedback': feedback,
                'subject': subject,
                'feedbackBy': employee_id,
            })

            return json_response(success=True, feedback={'id': new_feedback.id, 'folio': new_feedback.folio}, status=201)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/feedback', type='http', auth='none', methods=['GET'], csrf=False)
    def get_feedbacks(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            feedbacks = request.env['reclutamiento__kuale.employee.feedback'].sudo().search([])

            feedback_data = [{
                'id': feedback.id,
                'folio': feedback.folio,
                'feedbackType': feedback.feedbackType,
                'feedback': feedback.feedback,
                'subject': feedback.subject,
                'status': feedback.status,
                'feedbackBy': feedback.feedbackBy.name,
                'feedbackBy_id': feedback.feedbackBy.id,
                'company': feedback.feedbackBy.company_id.name,
                'create_date': format_dates(feedback.create_date),
                'comments': [{
                    'body': clean_html(message.body),
                    'author': message.author_id.name,
                    'date': format_dates(message.date)
                } for message in feedback.message_ids],
            } for feedback in feedbacks]

            return json_response(success=True, feedback=feedback_data, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/feedback/<int:feedback_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_feedback(self, feedback_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            feedback = request.env['reclutamiento__kuale.employee.feedback'].sudo().browse(feedback_id)
            if not feedback.exists():
                return json_response(success=False, error='Feedback not found', status=404)

            feedback_data = {
                'id': feedback.id,
                'folio': feedback.folio,
                'feedbackType': feedback.feedbackType,
                'feedback': feedback.feedback,
                'subject': feedback.subject,
                'status': feedback.status,
                'feedbackBy': feedback.feedbackBy.name,
                'create_date': format_dates(feedback.create_date), 
                'comments': [{
                    'body': clean_html(message.body),
                    'author': message.author_id.name,
                    'date': format_dates(message.date)  
                } for message in feedback.message_ids],
            }

            return json_response(success=True, feedback=feedback_data, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/feedback/<int:feedback_id>/comment', type='http', auth='none', methods=['POST'], csrf=False)
    def add_comment(self, feedback_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            data = request.httprequest.json
            comment = data.get('comment')

            if not comment:
                return json_response(success=False, error='Missing required fields', status=400)

            feedback = request.env['reclutamiento__kuale.employee.feedback'].sudo().browse(feedback_id)
            if not feedback.exists():
                return json_response(success=False, error='Feedback not found', status=404)
            
            feedback.message_post(
                body=comment,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=request.env.user.partner_id.id
            )

            return json_response(success=True, status=201)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/feedback/<int:feedback_id>/status', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_status(self, feedback_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id

            data = request.httprequest.json
            status = data.get('status')

            if not status:
                return json_response(success=False, error='Missing required fields', status=400)

            feedback = request.env['reclutamiento__kuale.employee.feedback'].sudo().browse(feedback_id)
            if not feedback.exists():
                return json_response(success=False, error='Feedback not found', status=404)

            feedback.write({'status': status})

            return json_response(success=True, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
   
    @http.route('/api/employee/feedback', type='http', auth='none', methods=['GET'], csrf=False)
    def get_feedbacks_employee(self,**kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            
            feedbacks = request.env['reclutamiento__kuale.employee.feedback'].sudo().search([('feedbackBy', '=', employee_id)])

            feedback_data = [{
                'id': feedback.id,
                'folio': feedback.folio,
                'feedbackType': feedback.feedbackType,
                'feedback': feedback.feedback,
                'subject': feedback.subject,
                'status': feedback.status,
                'feedbackBy': feedback.feedbackBy.name,
                'feedbackBy_id': feedback.feedbackBy.id,
                'company': feedback.feedbackBy.company_id.name,
                'create_date': format_dates(feedback.create_date),
                'comments': [{
                    'body': clean_html(message.body),
                    'author': message.author_id.name,
                    'date': format_dates(message.date)
                } for message in feedback.message_ids],
            } for feedback in feedbacks]

            return json_response(success=True, feedback=feedback_data, status=200)
        
        except Exception as e:
            return json_response(success=False, error=str(e), status=500)

