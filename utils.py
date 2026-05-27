import json, re
from odoo.http import request
from datetime import date, datetime
import base64
from odoo import fields


def json_response(success=True, error=None, status=200, **kwargs):
    response = {'success': success}
    
    if error:
        response['error'] = error
    
    for key, value in kwargs.items():
        if value is not None:
            response[key] = value
    
    return request.make_response(json.dumps(response), headers={'Content-Type': 'application/json'}, status=status)

def authenticate():
    employee_id = request.session.get('employee_id')
    if not employee_id:
        return json_response(success=False, error='Not authenticated', status=401)
    
    employee = request.env['hr.employee'].sudo().browse(employee_id)

    if not employee.user_id or len(employee.user_id) != 1:
        return json_response(success=False, error='Debe haber exactamente un usuario asociado con este empleado', status=400)

    user = employee.user_id

    if not request.env.user or not request.env.user.id:
        request.env = request.env(user=user)

    return employee_id

def format_dates(data):
    if isinstance(data, dict):
        return {k: format_dates(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [format_dates(item) for item in data]
    elif isinstance(data, (datetime, date)):
        return data.isoformat()  
    return data

def clean_html(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def clean_html_in_dict(data):
    if isinstance(data, dict):
        return {key: clean_html_in_dict(value) if isinstance(value, (dict, list)) else clean_html(value) if isinstance(value, str) else value for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_html_in_dict(item) if isinstance(item, (dict, list)) else clean_html(item) if isinstance(item, str) else item for item in data]
    else:
        return data
    
def generate_public_url( model, record_id, field_name):
    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    return f"{base_url}/web/image/{model}/{record_id}/{field_name}"

def get_image_fields( model_name):
    model = request.env[model_name]
    return [field_name for field_name, field in model._fields.items() if isinstance(field, fields.Binary)]

def process_record_data( record, model_name):
    record_data = record.read()[0]
    record_data = format_dates(record_data)
    image_fields = get_image_fields(model_name)

    for field_name in image_fields:
        if record_data.get(field_name):
            record_data[field_name] = generate_public_url(model_name, record.id, field_name)

    return record_data