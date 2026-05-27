from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from ..services.zk_biometric_service import ZkBiometricService
import base64

class ZkBiometricTemplate(models.Model):
    _name = 'zk.biometric.template'
    _description = 'Plantillas biométricas ZKTeco'
    _rec_name = 'display_name'
    _order = 'user_id, finger_index'

    # USUARIO
    display_name = fields.Char(string='Nombre visible',compute='_compute_display_name',store=True)
    uid = fields.Integer(string='UID')
    name = fields.Char(string='Nombre')
    privilege = fields.Char(string='Privilegio')
    password = fields.Char(string='Contraseña')
    group_id = fields.Char(string='ID del Grupo')
    user_id = fields.Char(string='ID de Usuario', required=True, index=True)
    # DEDOS
    finger_index = fields.Integer(string='Finger Index', required=True)
    template_data = fields.Binary(string='Template Data', attachment=False)
    template_size = fields.Integer(string='Template Size')
    finger_valid = fields.Integer(string='Finger Valid')
    finger_mark = fields.Binary(string='Finger Mark', attachment=False)
    # RELOJ
    source_device_ip = fields.Char(string='IP del reloj origen')
    imported_at = fields.Datetime(string='Fecha de importación', default=fields.Datetime.now)

    active = fields.Boolean(default=True)

    applicant_id = fields.Many2one(
        'hr.applicant',
        string='Postulante',
        index=True,
        ondelete='set null',
    )

    _sql_constraints = [
        (
            'unique_user_finger',
            'unique(user_id, finger_index)',
            'Ya existe una huella guardada para este User ID y Finger Index.'
        ),
    ]

    @api.depends('name', 'user_id', 'finger_index')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name or 'Sin nombre'} - {rec.user_id or ''} - Dedo {rec.finger_index}"

    @api.model
    def import_from_device(self, ip, port=4370):
        records = ZkBiometricService.fetch_from_device(ip=ip, port=port)

        created_count = 0
        skipped_count = 0

        for vals in records:
            existing = self.search([
                ('user_id', '=', vals['user_id']),
                ('finger_index', '=', vals['finger_index']),
            ], limit=1)

            if existing:
                skipped_count += 1
                continue

            self.create(vals)
            created_count += 1

        return {
            'created': created_count,
            'skipped': skipped_count,
            'total': len(records),
        }

##COMENTADO PARA PRUEBA
    # def export_to_device(self, ip, port=4370):
    #     self.ensure_one()

    #     records = self.search([
    #         ('user_id', '=', self.user_id)
    #     ], order='finger_index asc')

    #     return ZkBiometricService.push_user_biometrics(
    #         ip=ip,
    #         port=port,
    #         biometric_records=records
    #     )

    def export_to_device(self, ip, port=4370):
        self.ensure_one()

        records = self.search([
            ('user_id', '=', self.user_id)
        ], order='finger_index asc')

        source_ip = records[0].source_device_ip if records else False

        return ZkBiometricService.push_user_biometrics(
            ip=ip,
            port=port,
            biometric_records=records,
            source_ip=source_ip
        )

    def action_open_export_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Registrar biometría en reloj',
            'res_model': 'zk.biometric.export.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_biometric_id': self.id,
            }
        }

##COMENTADO PARA PRUEBA
    # @api.model
    # def export_all_to_device(self, ip, port=4370):
    #     records = self.search([], order='user_id asc, finger_index asc')

    #     return ZkBiometricService.push_all_biometrics(
    #         ip=ip,
    #         port=port,
    #         biometric_records=records
    #     )

    @api.model
    def export_all_to_device(self, ip, port=4370):
        records = self.search([], order='user_id asc, finger_index asc')

        return ZkBiometricService.push_all_biometrics(
            ip=ip,
            port=port,
            biometric_records=records
        )


class ZkBiometricImportWizard(models.TransientModel):
    _name = 'zk.biometric.import.wizard'
    _description = 'Wizard para importar biometría desde reloj'

    ip = fields.Char(string='IP del Reloj', required=True, default="192.168.1.201")
    port = fields.Integer(string='Puerto', required=True, default=4370)

    def action_import(self):
        self.ensure_one()

        result = self.env['zk.biometric.template'].import_from_device(
            ip=self.ip,
            port=self.port
        )

        message = (
            f"Importación completada.\n\n"
            f"Total encontrados: {result['total']}\n"
            f"Creados: {result['created']}\n"
            f"Omitidos: {result['skipped']}"
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Biometría importada',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }


class ZkBiometricExportWizard(models.TransientModel):
    _name = 'zk.biometric.export.wizard'
    _description = 'Wizard para registrar biometría en reloj'

    ip = fields.Char(string='IP del reloj', required=True, default="192.168.1.201")
    port = fields.Integer(string='Puerto', default=4370, required=True)
    biometric_id = fields.Many2one('zk.biometric.template', string='Registro biométrico', required=True)

    def action_export(self):
        self.ensure_one()

        result = self.biometric_id.export_to_device(ip=self.ip, port=self.port)
        message = (
            f"Registro completado.\n\n"
            f"Usuario: {result['user_id']} - {result['name']}\n"
            f"Huellas creadas: {result['created']}\n"
            f"Huellas omitidas: {result['skipped']}"
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Biometría registrada',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }


class ZkBiometricSyncAllWizard(models.TransientModel):
    _name = 'zk.biometric.sync.all.wizard'
    _description = 'Wizard para sincronizar toda la biometría a un reloj'

    ip = fields.Char(string='IP del reloj', required=True)
    port = fields.Integer(string='Puerto', default=4370, required=True)

    def action_sync_all(self):
        self.ensure_one()

        result = self.env['zk.biometric.template'].export_all_to_device(
            ip=self.ip,
            port=self.port
        )

        failed_text = ""
        if result['failed_users']:
            failed_text = "\n\nUsuarios con error:\n" + "\n".join(result['failed_users'][:10])

        message = (
            f"Sincronización completada.\n\n"
            f"Usuarios procesados: {result['processed_users']}\n"
            f"Huellas creadas: {result['created_templates']}\n"
            f"Huellas omitidas: {result['skipped_templates']}"
            f"{failed_text}"
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Biometría sincronizada',
                'message': message,
                'type': 'success' if not result['failed_users'] else 'warning',
                'sticky': True,
            }
        }


class ZkBiometricCreateUser(models.TransientModel):
    _name = 'zk.biometric.create.user.wizard'
    _description = 'Wizard para activar el reloj checador'

    ###Empleado
    uid = fields.Integer(string="UID", required=True, help="El el identificador que se coloca en el reloj para relacionar la huella con el usuario.")
    user_id = fields.Char(string="ID del Empleado", required=True, help="ID del Usuario")
    name = fields.Char(string="Nombre", required=True)
    last_name = fields.Char(string="Apellido", required=True)
    privilege = fields.Selection([
        ('0', 'Usuario'),
    ], string='Privilegio', default='0', required=True)
    password = fields.Char(string='Contraseña')
    group_id = fields.Char(string='ID del Grupo')
    ###Huellas
    finger_index = fields.Integer(string="Dedo", default=6)
    template_data = fields.Binary(string='Template Data', attachment=False)
    template_size = fields.Integer(string='Template Size')
    finger_valid = fields.Integer(string='Finger Valid')
    finger_mark = fields.Binary(string='Finger Mark', attachment=False)
    ###Reloj
    ip = fields.Char(string='IP del reloj', required=True, default="192.168.1.201")
    port = fields.Integer(string='Puerto', required=True, default=4370)

    ###Applicant
    applicant_id = fields.Many2one('hr.applicant', string='Applicant', required=False)

    ###Alerta
    display_name = fields.Char(string='Nombre visible', compute='_compute_display_name', store=True)

    already_enrolled = fields.Boolean(
        string='Ya tiene huella registrada',
        default=False,
    )

    @api.depends('name', 'user_id', 'finger_index')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name or 'Sin nombre'} - {rec.user_id or ''} - Dedo {rec.finger_index}"

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        applicant_id = self.env.context.get('default_applicant_id') or self.env.context.get('active_id')
        if applicant_id:
            res['user_id'] = str(applicant_id)

            # Verificar si ya tiene huella registrada
            template = self.env['zk.biometric.template'].search([
                ('user_id', '=', str(applicant_id))
            ], limit=1)

            print(f"[ZK ENROLL] applicant_id={applicant_id} template={template} already={bool(template)}")

            if template:
                res['already_enrolled'] = True
                res['uid']              = template.uid or 0
                res['password']         = template.password or ''

        return res

    def action_enroll(self):
        self.ensure_one()

        if self.already_enrolled:
            return {
                'type':   'ir.actions.client',
                'tag':    'zk_enrollment_error',
                'params': {'error': 'Este postulante ya tiene una huella registrada. No es necesario registrar de nuevo.'},
            }

        full_name = f"{self.name} {self.last_name}".strip()
        try:
            ZkBiometricService.start_enrollment(
                ip=self.ip,
                uid=self.uid,
                user_id=self.user_id,
                name=full_name,
                password=self.password,
                privilege=self.privilege,
                finger_index=self.finger_index,
                port=self.port
            )
        except Exception as e:
            return {
                'type':   'ir.actions.client',
                'tag':    'zk_enrollment_error',
                'params': {'error': str(e)},
            }

        return {
            'type':   'ir.actions.client',
            'tag':    'zk_start_polling',
            'params': {'record_id': self.id},
        }

    def action_verify_enrollment(self):
        self.ensure_one()
 
        verify = self.env['zk.biometric.verify.wizard'].create({
            'applicant_id': self.applicant_id.id or False,
            'user_id':      self.user_id,
            'ip':           self.ip,
            'port':         self.port,
        })
 
        return {
            'type':   'ir.actions.client',
            'tag':    'zk_start_verify_polling',
            'params': {
                'record_id':       verify.id,
                'confirm_context': {
                    'default_applicant_id': self.applicant_id.id or False,
                    'active_id':            self.applicant_id.id or False,
                },
            },
        }
    
    def action_check_enrollment(self):
        self.ensure_one()
        try:
            result = ZkBiometricService.get_enrolled_template(
                ip=self.ip,
                user_id=self.user_id,
                finger_index=self.finger_index,
                port=self.port
            )
            if not result:
                return {'done': False}

            existing = self.env['zk.biometric.template'].search([
                ('user_id',      '=', result.get('user_id')),
                ('finger_index', '=', result.get('finger_index'))
            ], limit=1)

            if not existing:
                full_name = f"{self.name} {self.last_name}".strip()
                self.env['zk.biometric.template'].create({
                    'uid':           result.get('uid'),
                    'user_id':       result.get('user_id'),
                    'name':          full_name,
                    'finger_index':  result.get('finger_index'),
                    'template_data': base64.b64encode(result.get('template_data') or b''),
                    'template_size': result.get('template_size'),
                    'finger_valid':  result.get('finger_valid'),
                    'finger_mark':   base64.b64encode(result.get('finger_mark') or b''),
                    'applicant_id':  self.applicant_id.id or False,
                    'password':      self.password or '',
                })

            return {'done': True}

        except Exception as e:
            print(f"[ZK ERROR] action_check_enrollment: {e}")
            import traceback
            traceback.print_exc()
            return {'done': False}


# ── FUERA de ZkBiometricCreateUser ───────────────────────────────────────────

class ZkBiometricVerifyWizard(models.TransientModel):
    _name        = 'zk.biometric.verify.wizard'
    _description = 'Wizard para verificar huella por asistencia'

    applicant_id = fields.Many2one('hr.applicant', string='Postulante')
    user_id      = fields.Char(string='ID del Empleado', required=True)
    ip           = fields.Char(string='IP del reloj',    required=True)
    port         = fields.Integer(string='Puerto',       required=True)
    opened_at    = fields.Char(string='Abierto en')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['opened_at'] = datetime.utcnow().isoformat()
        return res

    def action_check_verification(self):
        self.ensure_one()
        try:
            import pytz

            ts = ZkBiometricService.get_last_attendance(
                ip=self.ip,
                user_id=self.user_id,
                port=self.port,
            )

            print(f"[ZK VERIFY] ts={ts}  opened_at={self.opened_at}")

            if not ts:
                return {'done': False}

            # El reloj guarda hora local (Tamaulipas = UTC-6)
            # Comparamos contra ahora en hora local con margen de 5 minutos
            local_tz = pytz.timezone('America/Monterrey')
            now_local = datetime.now(pytz.utc).astimezone(local_tz).replace(tzinfo=None)
            diff = (now_local - ts).total_seconds()

            print(f"[ZK VERIFY] now_local={now_local}  diff={diff}s")

            if 0 <= diff <= 300:  # asistencia de los últimos 5 minutos
                return {'done': True}

            return {'done': False}

        except Exception as e:
            print(f"[ZK VERIFY ERROR] {e}")
            import traceback
            traceback.print_exc()
            return {'done': False}

    def action_open_confirm(self):
        self.ensure_one()
        return {
            'type':      'ir.actions.act_window',
            'name':      'Confirmar verificación de huella',
            'res_model': 'zk.biometric.confirm.wizard',
            'view_mode': 'form',
            'target':    'new',
            'context':   {
                'default_applicant_id': self.applicant_id.id or False,
                'active_id':            self.applicant_id.id or False,
            },
        }