import base64
from pytz import timezone
from datetime import datetime
from odoo import http
from odoo.http import request


def is_base64(data):
    try:
        if isinstance(data, str):
            # Intenta decodificar y verificar si vuelve a codificarse igual
            return base64.b64encode(base64.b64decode(data)) == data.encode()
        return False
    except Exception:
        return False


class ZkBiometricController(http.Controller):

    @http.route('/api/zk_biometric/attendance', type='http', auth='none', methods=['POST'], csrf=False)
    def create_attendance(self, **kwargs):
        try:
            data = request.httprequest.json
            device_employee_id = data.get('deviceEmployeeId')
            action = data.get('action')
            attendance_type = data.get('attendanceType')
            punching_time = data.get('punchingTime')
            work_location =data.get('workLocation')
            print('data: ',[device_employee_id, action, attendance_type, punching_time, work_location])

            if not all ([device_employee_id, action, attendance_type, punching_time, work_location]):
                return request.make_json_response(
                    {
                        'status': 417,
                        'data': [],
                        'message': 'data incomplete'
                    },status=417
                )
            try:
                local_tz = timezone('America/Mexico_City')
                local_time = datetime.strptime(punching_time, '%Y-%m-%d %H:%M:%S')
                utc_time = local_tz.localize(local_time).astimezone(timezone('UTC'))
                punching_time = utc_time.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                return request.make_json_response(
                    {
                        'status': 417,
                        'data': [],
                        'message': str(e)
                    },status=417
                )

            attendance = request.env['reclutamiento__kuale.zkteco_log'].sudo().create({
                'device_employee_id': device_employee_id,
                'action': action,
                'attendance_type': attendance_type,
                'punching_time': punching_time,
                'work_location': work_location
            })

            if attendance:
                return request.make_json_response({
                    'status': 201,
                    'data': {
                        'id': attendance.id,
                        'device_employee_id': attendance.device_employee_id,
                        'action': attendance.action,
                        'attendance_type': attendance.attendance_type,
                        'punching_time': attendance.punching_time,
                        'work_location': attendance.work_location.id,
                    },
                    'message': 'record created'},status=201
                )
            else:
                return request.make_json_response({
                    'status': 444,
                    'data': [],
                    'message': 'unable to create attendance registry'
                })

        except Exception as e:
            return request.make_json_response({
                'status': 500,
                'data':[],
                'error': str(e)
            },status=500)

    @http.route('/api/zk_biometric/biometric', type='http', auth='none', methods=['POST'], csrf=False)
    def create_biometric(self, **kwargs):
        try:
            data = request.httprequest.json
            device_employee_id = data.get('deviceEmployeeId')
            biometric_type = data.get('biometricType')
            biometric_data = data.get('biometricData')

            if not all ([device_employee_id, biometric_type, biometric_data]):
                return request.make_json_response(
                    {
                        'status': 417,
                        'data': [],
                        'message': 'data incomplete'
                    }, status=417
                )

            if isinstance(biometric_data, str) and is_base64(biometric_data):
                biometric_data = base64.b64decode(biometric_data)

            biometric  = request.env['reclutamiento__kuale.biometric_user'].sudo().create({
                'device_employee_id': device_employee_id,
                'biometric_type': biometric_type,
                'biometric_data': biometric_data
            })
            if biometric:
                return request.make_json_response({
                    'status': 201,
                    'data': {
                        'id': biometric.id,
                        'device_employee_id': biometric.device_employee_id,
                        'biometric_type': biometric.biometric_type,
                    },
                    'message': 'biometric saved'
                },status=201)
            else:
                return request.make_json_response({
                    'status': 444,
                    'data':[],
                    'message': 'unable to create biometric registry'
                },status=500)


        except Exception as e:
            return request.make_json_response({
                'status': 500,
                'data': [],
                'error': str(e)
            }, status=500)


    @http.route('/api/zk_biometric/biometric', type='http', auth='none', methods=['GET'], csrf=False)
    def get_biometrics(self, **kwargs):
        try:
            user_biometrics = request.env['reclutamiento__kuale.biometric_user'].sudo().search([])
            biometrics = []
            for user in user_biometrics:
                biometrics.append({
                    'id': user.id,
                    'device_employee_id': user.device_employee_id,
                    'employee':{
                        'name': user.employee_id.name,
                    }if user.employee_id else None,
                    'biometric_type': user.biometric_type,
                    'biometric_data': user.biometric_data.decode('utf-8') if user.biometric_data else None
                })
            return request.make_json_response({
                'status': 200,
                'data': biometrics,
                'message': 'biometrics retrieved'
            },status=200)

        except Exception as e:
            return request.make_json_response({
                'status': 500,
                'data':[],
                'error': str(e)
            },status=500)