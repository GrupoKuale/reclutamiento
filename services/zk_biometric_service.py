import base64
from zk import ZK, const
from odoo import _
from odoo.exceptions import UserError
import copy
import time

class ZkBiometricService:
##COMENTADO PARA PRUEBA
    # @staticmethod
    # def _to_binary(value):
    #     if not value:
    #         return False

    #     try:
    #         if isinstance(value, bytes):
    #             raw = value
    #         elif isinstance(value, bytearray):
    #             raw = bytes(value)
    #         elif isinstance(value, str):
    #             raw = value.encode('latin1', errors='ignore')
    #         else:
    #             raw = str(value).encode('latin1', errors='ignore')

    #         return base64.b64encode(raw).decode('ascii')
    #     except Exception as e:
    #         print("Error convirtiendo binario:", e)
    #         return False
    
    # @staticmethod
    # def fetch_from_device(ip, port=4370, timeout=10):
    #     zk = ZK(ip, port=port, timeout=timeout)
    #     conn = None

    #     try:
    #         conn = zk.connect()
    #         conn.disable_device()

    #         users = conn.get_users()
    #         templates = conn.get_templates()

    #         user_map = {int(u.uid): u for u in users}
    #         results = []

    #         for tpl in templates:
    #             user = user_map.get(int(tpl.uid))
    #             if not user:
    #                 continue

    #             template_bytes = getattr(tpl, 'template', b'') or b''
    #             finger_mark = getattr(tpl, 'mark', b'') or b''
    #             finger_index = getattr(tpl, 'fid', 0) or 0 
    #             finger_valid = getattr(tpl, 'valid', 1) or 1
    #             template_size = getattr(tpl, 'size', len(template_bytes)) or  len(template_bytes)

    #             results.append({
    #                 'uid': int(user.uid) if user.uid is not None else 0,
    #                 'name': user.name or 'No Disponible',
    #                 'privilege': user.privilege or 'User',
    #                 'password': user.password or '',
    #                 'group_id': user.group_id or  '',
    #                 'user_id': str(user.user_id or ''),
    #                 'finger_index': int(finger_index),
    #                 'template_data': ZkBiometricService._to_binary(template_bytes),
    #                 'template_size': int(template_size),
    #                 'finger_valid': int(finger_valid),
    #                 'finger_mark': ZkBiometricService._to_binary(finger_mark),
    #                 'source_device_ip': ip,
    #             })

    #         return results
        
    #     except Exception as e:
    #         raise UserError(_("Error al leer el reloj %s:%s -> %s") % (ip, port, str(e)))
    #     finally:
    #         if conn:
    #             try:
    #                 conn.enable_device()
    #             except Exception:
    #                 pass
    #             try:
    #                 conn.disconnect()
    #             except Exception:
    #                 pass    

    # @staticmethod
    # def _decode_binary(value):
    #     if not value:
    #         return b""

    #     try:
    #         if isinstance(value, str):
    #             return base64.b64decode(value)
    #         elif isinstance(value, bytes):
    #             return base64.b64decode(value)
    #         return b""
    #     except Exception as e:
    #         raise UserError(_("No se pudo decodificar el binario: %s") % str(e))

    # @staticmethod
    # def _get_next_uid(users):
    #     used_uids = [int(u.uid) for u in users if u.uid is not None]
    #     return max(used_uids) + 1 if used_uids else 1
    
    # @staticmethod
    # def push_user_biometrics(ip, biometric_records, port=4370, timeout=10):
    #     zk = ZK(ip, port=port, timeout=timeout)
    #     connection = None

    #     try:
    #         connection = zk.connect()
    #         connection.disable_device()

    #         if not biometric_records:
    #             raise UserError(_("No se logran recibir los datos biométricos para enviar al reloj."))

    #         #Crear Usuario
    #         first = biometric_records[0]
    #         users = connection.get_users()
    #         target_user = next((u for u in users if str(u.user_id) == str(first.user_id)), None)

    #         if not target_user:
    #             new_uid = ZkBiometricService._get_next_uid(users)

    #             connection.set_user(
    #                 uid=new_uid,
    #                 name=first.name or f"Usuario {first.user_id}",
    #                 privilege=first.privilege if first.privilege is not None else const.USER_DEFAULT,
    #                 password=first.password or "",
    #                 group_id=first.group_id or "",
    #                 user_id=str(first.user_id)
    #             )

    #             # recargar usuarios para obtener el objeto real del reloj
    #             users = connection.get_users()
    #             target_user = next((u for u in users if str(u.user_id) == str(first.user_id)), None)

    #         if not target_user:
    #             raise UserError(_("No se pudo crear ni encontrar el usuario destino en el reloj."))

    #         templates = connection.get_templates()

    #         if not templates:
    #             raise UserError(_("El reloj no cuenta con registros, minimo debe tener un registro para ejecutar esta acción."))

    #         base_finger = templates[0]

    #         # Huellas existentes del usuario
    #         existing_fids = {
    #             int(t.fid) for t in templates
    #             if int(t.uid) == int(target_user.uid)
    #         }

    #         created = 0
    #         skipped = 0

    #        #Enviar Huellas 
    #         for rec in biometric_records:
    #             if int(rec.finger_index) in existing_fids:
    #                 skipped += 1
    #                 continue

    #             template_bytes = ZkBiometricService._decode_binary(rec.template_data)
    #             finger_mark = ZkBiometricService._decode_binary(rec.finger_mark) if rec.finger_mark else b""

    #             new_finger = copy.copy(base_finger)

    #             new_finger.uid = target_user.uid
    #             new_finger.fid = int(rec.finger_index)
    #             new_finger.valid = int(rec.finger_valid or 1)
    #             new_finger.template = template_bytes
    #             new_finger.size = int(rec.template_size or len(template_bytes))

    #             if hasattr(new_finger, "mark"):
    #                 new_finger.mark = finger_mark

    #             if hasattr(new_finger, "repack"):
    #                 try:
    #                     new_finger.repack()
    #                 except Exception as e:
    #                     raise UserError(_("No se pudo ejecutar re-empaquetado para el dedo %s: %s") % (
    #                         rec.finger_index, str(e)
    #                     ))

    #             connection.save_user_template(target_user, [new_finger])
    #             created += 1

    #         return {
    #             'user_id': target_user.user_id,
    #             'name': target_user.name,
    #             'created': created,
    #             'skipped': skipped,
    #         }

    #     except Exception as e:
    #         raise UserError(_("Error al registrar la huella en el reloj %s:%s -> %s") % (ip, port, str(e)))

    #     finally:
    #         if connection:
    #             try:
    #                 connection.enable_device()
    #             except Exception:
    #                 pass
    #             try:
    #                 connection.disconnect()
    #             except Exception:
    #                 pass

    # @staticmethod
    # def push_all_biometrics(ip, biometric_records, port=4370, timeout=10):
    #     if not biometric_records:
    #         raise UserError(_("No hay registros biométricos para enviar al reloj."))

    #     grouped = {}
    #     for rec in biometric_records:
    #         grouped.setdefault(rec.user_id, []).append(rec)

    #     total_users = 0
    #     total_templates_created = 0
    #     total_templates_skipped = 0
    #     failed_users = []

    #     for user_id, records in grouped.items():
    #         try:
    #             result = ZkBiometricService.push_user_biometrics(
    #                 ip=ip,
    #                 port=port,
    #                 biometric_records=records,
    #                 timeout=timeout
    #             )
    #             total_users += 1
    #             total_templates_created += result.get('created', 0)
    #             total_templates_skipped += result.get('skipped', 0)

    #         except Exception as e:
    #             failed_users.append(f"{user_id}: {str(e)}")

    #     return {
    #         'processed_users': total_users,
    #         'created_templates': total_templates_created,
    #         'skipped_templates': total_templates_skipped,
    #         'failed_users': failed_users,
    #     }

    @staticmethod
    def _to_binary(value):
        if not value:
            return False

        try:
            if isinstance(value, bytes):
                raw = value
            elif isinstance(value, bytearray):
                raw = bytes(value)
            elif isinstance(value, str):
                raw = value.encode('latin1', errors='ignore')
            else:
                raw = str(value).encode('latin1', errors='ignore')

            return base64.b64encode(raw).decode('ascii')
        except Exception as e:
            print("Error convirtiendo binario:", e)
            return False

    @staticmethod
    def _decode_binary(value):
        if not value:
            return b""

        try:
            if isinstance(value, str):
                return base64.b64decode(value)
            elif isinstance(value, bytes):
                return base64.b64decode(value)
            return b""
        except Exception as e:
            raise UserError(_("No se pudo decodificar el binario: %s") % str(e))

    @staticmethod
    def _get_next_uid(users):
        used_uids = [int(u.uid) for u in users if u.uid is not None]
        return max(used_uids) + 1 if used_uids else 1

    @staticmethod
    def fetch_from_device(ip, port=4370, timeout=10):
        zk = ZK(ip, port=port, timeout=timeout)
        conn = None

        try:
            conn = zk.connect()
            conn.disable_device()

            users = conn.get_users()
            templates = conn.get_templates()

            user_map = {int(u.uid): u for u in users}
            results = []

            for tpl in templates:
                user = user_map.get(int(tpl.uid))
                if not user:
                    continue

                template_bytes = getattr(tpl, 'template', b'') or b''
                finger_mark = getattr(tpl, 'mark', b'') or b''
                finger_index = getattr(tpl, 'fid', 0) or 0
                finger_valid = getattr(tpl, 'valid', 1) or 1
                template_size = getattr(tpl, 'size', len(template_bytes)) or len(template_bytes)

                results.append({
                    'uid': int(user.uid) if user.uid is not None else 0,
                    'name': user.name or 'No Disponible',
                    'privilege': user.privilege or const.USER_DEFAULT,
                    'password': user.password or '',
                    'group_id': user.group_id or '',
                    'user_id': str(user.user_id or ''),
                    'finger_index': int(finger_index),
                    'template_data': ZkBiometricService._to_binary(template_bytes),
                    'template_size': int(template_size),
                    'finger_valid': int(finger_valid),
                    'finger_mark': ZkBiometricService._to_binary(finger_mark),
                    'source_device_ip': ip,
                })

            return results

        except Exception as e:
            raise UserError(_("Error al leer el reloj %s:%s -> %s") % (ip, port, str(e)))
        finally:
            if conn:
                try:
                    conn.enable_device()
                except Exception:
                    pass
                try:
                    conn.disconnect()
                except Exception:
                    pass

    @staticmethod
    def _get_base_template_from_source(source_ip, port=4370, timeout=10):
        """
        Intenta obtener una huella real desde el reloj origen para usarla
        como plantilla base cuando el reloj destino está vacío.
        """
        if not source_ip:
            return None

        zk = ZK(source_ip, port=port, timeout=timeout)
        conn = None

        try:
            conn = zk.connect()
            conn.disable_device()

            templates = conn.get_templates()
            if templates:
                return copy.copy(templates[0])

            return None

        except Exception:
            return None

        finally:
            if conn:
                try:
                    conn.enable_device()
                except Exception:
                    pass
                try:
                    conn.disconnect()
                except Exception:
                    pass

    @staticmethod
    def push_user_biometrics(ip, biometric_records, port=4370, timeout=10, source_ip=None):
        zk = ZK(ip, port=port, timeout=timeout)
        connection = None

        try:
            connection = zk.connect()
            connection.disable_device()

            if not biometric_records:
                raise UserError(_("No se logran recibir los datos biométricos para enviar al reloj."))

            first = biometric_records[0]

            # Si no viene source_ip por parámetro, tomarlo del primer registro
            if not source_ip:
                source_ip = getattr(first, 'source_device_ip', False)

            # Crear o localizar usuario destino
            users = connection.get_users()
            target_user = next((u for u in users if str(u.user_id) == str(first.user_id)), None)

            if not target_user:
                new_uid = ZkBiometricService._get_next_uid(users)

                connection.set_user(
                    uid=new_uid,
                    name=first.name or f"Usuario {first.user_id}",
                    privilege=first.privilege if first.privilege is not None else const.USER_DEFAULT,
                    password=first.password or "",
                    group_id=first.group_id or "",
                    user_id=str(first.user_id)
                )

                users = connection.get_users()
                target_user = next((u for u in users if str(u.user_id) == str(first.user_id)), None)

            if not target_user:
                raise UserError(_("No se pudo crear ni encontrar el usuario destino en el reloj."))

            # 2) Obtener templates del destino
            templates = connection.get_templates()

            # Si el reloj destino tiene huellas, usamos una de ahí
            if templates:
                base_finger = copy.copy(templates[0])
            else:
                # Si está vacío, intentamos tomar una huella base del reloj origen
                base_finger = ZkBiometricService._get_base_template_from_source(
                    source_ip=source_ip,
                    port=port,
                    timeout=timeout
                )

            if not base_finger:
                raise UserError(_(
                    "No se pudo obtener una huella base para construir la biometría.\n"
                    "El reloj destino está vacío y tampoco se pudo leer una huella base desde el reloj origen (%s)."
                ) % (source_ip or "Sin IP origen"))

            # Huellas ya existentes del usuario en destino
            existing_fids = {
                int(t.fid) for t in templates
                if int(t.uid) == int(target_user.uid)
            }

            created = 0
            skipped = 0

            # Enviar huellas
            for rec in biometric_records:
                if int(rec.finger_index) in existing_fids:
                    skipped += 1
                    continue

                template_bytes = ZkBiometricService._decode_binary(rec.template_data)
                finger_mark = ZkBiometricService._decode_binary(rec.finger_mark) if rec.finger_mark else b""

                new_finger = copy.copy(base_finger)

                new_finger.uid = target_user.uid
                new_finger.fid = int(rec.finger_index)
                new_finger.valid = int(rec.finger_valid or 1)
                new_finger.template = template_bytes
                new_finger.size = int(rec.template_size or len(template_bytes))

                if hasattr(new_finger, "mark"):
                    new_finger.mark = finger_mark

                if hasattr(new_finger, "repack"):
                    try:
                        new_finger.repack()
                    except Exception as e:
                        raise UserError(_("No se pudo ejecutar re-empaquetado para el dedo %s: %s") % (
                            rec.finger_index, str(e)
                        ))

                connection.save_user_template(target_user, [new_finger])
                created += 1

            return {
                'user_id': target_user.user_id,
                'name': target_user.name,
                'created': created,
                'skipped': skipped,
            }

        except Exception as e:
            raise UserError(_("Error al registrar la huella en el reloj %s:%s -> %s") % (ip, port, str(e)))

        finally:
            if connection:
                try:
                    connection.enable_device()
                except Exception:
                    pass
                try:
                    connection.disconnect()
                except Exception:
                    pass

    @staticmethod
    def push_all_biometrics(ip, biometric_records, port=4370, timeout=10):
        if not biometric_records:
            raise UserError(_("No hay registros biométricos para enviar al reloj."))

        grouped = {}
        for rec in biometric_records:
            grouped.setdefault(rec.user_id, []).append(rec)

        total_users = 0
        total_templates_created = 0
        total_templates_skipped = 0
        failed_users = []

        for user_id, records in grouped.items():
            try:
                source_ip = records[0].source_device_ip if records else False

                result = ZkBiometricService.push_user_biometrics(
                    ip=ip,
                    port=port,
                    biometric_records=records,
                    timeout=timeout,
                    source_ip=source_ip
                )

                total_users += 1
                total_templates_created += result.get('created', 0)
                total_templates_skipped += result.get('skipped', 0)

            except Exception as e:
                failed_users.append(f"{user_id}: {str(e)}")

        return {
            'processed_users': total_users,
            'created_templates': total_templates_created,
            'skipped_templates': total_templates_skipped,
            'failed_users': failed_users,
        }
##################### ESTO AUN ESTA A PRUEBA 
    @staticmethod
    def enroll_user_biometrics(ip, uid, user_id, name, password, privilege, finger_index=0, port=4370, timeout=10):
        zk = ZK(ip, port=port, timeout=timeout)
        connection = None

        try:
            connection = zk.connect()
            connection.disable_device()

            if not user_id:
                raise UserError(_("El user_id es requerido para registrar la huella."))

            # Obtener usuarios del reloj
            users = connection.get_users()
            target_user = next((u for u in users if str(u.user_id) == str(user_id)),None)

            # Crear usuario si no existe
            if not target_user:
                connection.set_user(
                    uid=uid,
                    name=name or f"Usuario {user_id}",
                    privilege=privilege,
                    password=password,
                    group_id="",
                    user_id=str(user_id)
                )

                users = connection.get_users()
                target_user = next((u for u in users if str(u.user_id) == str(user_id)),None)

            if not target_user:
                raise UserError(_("No se pudo crear ni encontrar el usuario en el reloj."))

            # Activación de dispositivo
            connection.enable_device()
            time.sleep(2)

            # Activa el registro de Huellas
            connection.enroll_user(
                uid=target_user.uid,
                temp_id=int(finger_index),
                user_id=str(user_id)
            )

            #Aquí el usuario va al reloj y pone el dedo
            time.sleep(30)

            #Leer templates
            templates = connection.get_templates()

            #Buscar template recién capturado
            # Crear mapa uid -> user_id
            user_map = {u.uid: u.user_id for u in users}

            target_template = next(
                (
                    t for t in templates
                    if str(user_map.get(t.uid)) == str(user_id)
                    and int(t.fid) == int(finger_index)
                ),
                None
            )

            if not target_template:
                raise UserError(_(
                    "No se detectó la huella capturada.\n"
                    "Asegúrate de haber colocado el dedo correctamente en el reloj."
                ))

            return {
                'uid': target_template.uid,
                'user_id': user_map.get(target_template.uid),
                'name': name,
                'finger_index': target_template.fid,
                'template_data': target_template.template,
                'template_size': len(target_template.template),
                'finger_valid': getattr(target_template, 'valid', 1),
                'finger_mark': getattr(target_template, 'mark', b""),
            }

        except Exception as e:
            raise UserError(_(
                "Error al registrar huella en el reloj %s:%s -> %s"
            ) % (ip, port, str(e)))

        finally:
            if connection:
                try:
                    connection.enable_device()
                except Exception:
                    pass
                try:
                    connection.disconnect()
                except Exception:
                    pass
    
    def check_fingerprint_registered(ip, user_id, finger_index, port=4370, timeout=5):
        zk = ZK(ip, port=port, timeout=timeout)
        conn = None

        try:
            conn = zk.connect()

            users = conn.get_users()
            user_map = {u.uid: u.user_id for u in users}

            templates = conn.get_templates()

            for t in templates:
                if str(user_map.get(t.uid)) == str(user_id) and int(t.fid) == int(finger_index):
                    return True

            return False

        except Exception:
            return False

        finally:
            if conn:
                try:
                    conn.disconnect()
                except:
                    pass

###########################################ESTO SE USA ACTUALMENTE
    @staticmethod
    def start_enrollment(ip, uid, user_id, name, password, privilege, finger_index, port=4370):
        try:
            zk   = ZK(ip, port=port, timeout=10)
            conn = zk.connect()
        except Exception as e:
            raise UserError(_(
                "No se pudo conectar al reloj %s:%s.\n"
                "Verifica que esté encendido y en la red.\n\nDetalle: %s"
            ) % (ip, port, str(e)))

        try:
            users = conn.get_users()
            target_user = next((u for u in users if str(u.user_id) == str(user_id)), None)

            # Verificar si ya tiene huella en ese dedo
            if target_user:
                templates    = conn.get_templates()
                user_map     = {u.uid: u.user_id for u in users}
                already      = next(
                    (t for t in templates
                     if str(user_map.get(t.uid)) == str(user_id)
                     and int(t.fid) == int(finger_index)),
                    None
                )
                if already:
                    raise UserError(_(
                        "El usuario %s ya tiene una huella registrada en el dedo %s.\n"
                        "Elimina la huella existente antes de registrar una nueva."
                    ) % (user_id, finger_index))

            # Crear usuario si no existe
            if not target_user:
                # Verificar que el UID no esté ocupado por otro user_id
                uid_conflict = next((u for u in users if int(u.uid) == int(uid)
                                     and str(u.user_id) != str(user_id)), None)
                if uid_conflict:
                    raise UserError(_(
                        "El UID %s ya está en uso por otro usuario (%s).\n"
                        "Utiliza un UID diferente."
                    ) % (uid, uid_conflict.user_id))

                conn.set_user(
                    uid=uid,
                    name=name,
                    privilege=privilege,
                    password=password,
                    group_id="",
                    user_id=str(user_id)
                )
                users       = conn.get_users()
                target_user = next((u for u in users if str(u.user_id) == str(user_id)), None)

            if not target_user:
                raise UserError(_("No se pudo crear ni encontrar el usuario en el reloj."))

            conn.enable_device()
            try:
                conn.enroll_user(
                    uid=target_user.uid,
                    temp_id=int(finger_index),
                    user_id=str(user_id)
                )
            except TimeoutError:
                pass  # Normal — el reloj queda esperando el dedo
            except Exception as e:
                raise UserError(_("Error iniciando enrolamiento: %s") % str(e))

        finally:
            try:
                conn.disconnect()
            except Exception:
                pass

    @staticmethod
    def get_enrolled_template(ip, user_id, finger_index, port=4370):
        try:
            zk   = ZK(ip, port=port, timeout=5)
            conn = zk.connect()
        except Exception:
            return None  # Reloj no disponible — el polling sigue intentando

        try:
            users    = conn.get_users()
            user_map = {u.uid: u.user_id for u in users}
            templates = conn.get_templates()

            for t in templates:
                if (str(user_map.get(t.uid)) == str(user_id)
                        and int(t.fid) == int(finger_index)):
                    return {
                        'uid':           t.uid,
                        'user_id':       user_map.get(t.uid),
                        'finger_index':  t.fid,
                        'template_data': t.template,
                        'template_size': len(t.template),
                        'finger_valid':  getattr(t, 'valid', 1),
                        'finger_mark':   getattr(t, 'mark', b""),
                    }
            return None

        except Exception:
            return None

        finally:
            try:
                conn.disconnect()
            except Exception:
                pass
    
    @staticmethod
    def get_last_attendance(ip, user_id, port=4370, timeout=5):
        try:
            zk   = ZK(ip, port=port, timeout=timeout)
            conn = zk.connect()
        except Exception:
            return None

        try:
            attendances = conn.get_attendance()

            print(f"[ZK ATT] Total asistencias: {len(attendances)}")

            # Imprimir todas para ver qué campo trae user_id
            for a in attendances[-5:]:  # últimas 5
                print(f"[ZK ATT] a.user_id={a.user_id} timestamp={a.timestamp}")

            # Filtrar directamente por user_id string
            matches = [
                a for a in attendances
                if str(a.user_id) == str(user_id)
            ]

            print(f"[ZK ATT] Matches para user_id={user_id}: {len(matches)}")

            if not matches:
                return None

            latest = max(matches, key=lambda a: a.timestamp)
            return latest.timestamp

        except Exception as e:
            print(f"[ZK ATT ERROR] {e}")
            return None
        finally:
            try:
                conn.disconnect()
            except Exception:
                pass