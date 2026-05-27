from odoo import http
from odoo.http import request
from ..utils import authenticate, json_response, format_dates, clean_html_in_dict, clean_html, process_record_data

class CourseController(http.Controller):

    @http.route('/api/course/create', type='http', auth='none', methods=['POST'], csrf=False)
    def create_course(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            data = request.httprequest.json
            
            data['course']['user_id'] = request.env['hr.employee'].sudo().search([('id', '=', data['course']['user_id'])]).user_id.id

            new_course = request.env['slide.channel'].sudo().create(data.get('course', {}))

            for section in data.get('sections', []):
                section['channel_id'] = new_course.id

                contents = section.pop('contents', [])

                new_section = request.env['slide.slide'].sudo().create(section)

                for content in contents:
                    content['channel_id'] = new_course.id
                    content['category_id'] = new_section.id
                    request.env['slide.slide'].sudo().create(content)

            return json_response(success=True, courses= new_course.id, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/employee/courses', type='http', auth='none', methods=['GET'], csrf=False)
    def get_my_courses(self, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            employee = request.env['hr.employee'].sudo().browse(employee_id)
            user = employee.user_id

            enrolled_courses = request.env['slide.channel.partner'].sudo().search([
                ('partner_id', '=', user.partner_id.id)
            ])

            course_data = [{
                'course_id': course.channel_id.id,
                'course_name': course.channel_id.name,
                'course_description': clean_html(course.channel_id.description),
                'start_date': format_dates(course.startDate) if course.startDate else None,
                'end_date': format_dates(course.endDate) if course.endDate else None,
                'completion': course.completion, 
            } for course in enrolled_courses]

            return json_response(success=True, courses=course_data, status=200)

        except Exception as e:
            return json_response(success=False, error=str(e), status=500)
        
    @http.route('/api/course/<int:course_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_course(self, course_id, **kwargs):
        try:
            employee_id = authenticate()
            if isinstance(employee_id, http.Response):
                return employee_id
            course = request.env['slide.channel'].sudo().browse(course_id)
            if not course.exists():
                return json_response(success=False, error='Course not found', status=404)

            course_data = process_record_data(course, 'slide.channel')

            course_data['sections'] = []
            for section in course.slide_category_ids:
                section_data = process_record_data(section, 'slide.slide')

                section_data['contents'] = []
                for content in course.slide_ids.filtered(lambda s: s.category_id.id == section.id):
                    content_data = process_record_data(content, 'slide.slide')
                    section_data['contents'].append(content_data)

                course_data['sections'].append(section_data)

            return json_response(success=True, courses=course_data, status=200)

        except Exception as e:
            
            return json_response(success=False, error=str(e), status=500)