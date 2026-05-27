import re
import csv
import requests
from zk import ZK, const
import time
import ast
import copy
import io

from datetime import datetime

IP = "192.168.1.201"
PORT = 4370
ENDPOINT = "http://localhost:8069/api/zk_biometric/attendance"

def send_to_odoo(data):
    try:
        response = requests.post(ENDPOINT, json=data)
        if response.status_code == 201:
            print("Registro enviado correctamente:", response.json())
        else:
            print(
                f"Error al enviar datos (status {response.status_code}):",
                response.json(),
            )
    except Exception as e:
        print("Error al enviar al endpoint de Odoo:", e)

def parse_attendance(attendance):
    pattern = r"<Attendance>: (\d+) : ([\d\-:\s]+) \((\d+), (\d+)\)"
    match = re.match(pattern, attendance)
    if match:
        return {
            "deviceEmployeeId": match.group(1),
            "action": match.group(4),
            "attendanceType": match.group(3),
            "punchingTime": match.group(2).strip(),
            "workLocation": "1",
        }
    return None

def test():
    test_str = "<Attendance>: 1 : 2024-11-30 12:30:53 (15, 0)"
    attendance = parse_attendance(str(test_str))
    if attendance:
        send_to_odoo(attendance)
        print("test success")
    else:
        print("unable to process attendance")

def livestream_capture():
    zk = ZK(IP, PORT)
    connection = None
    try:
        connection = zk.connect()
        print('Ya estoy conectado al ZK')
        for attendance in connection.live_capture():
            if attendance is None:
                continue
            else:
                attendance = parse_attendance(str(attendance))
                if attendance:
                    send_to_odoo(attendance)
                else:
                    print("unable to process attendance")

    except KeyboardInterrupt:
        print("livestream capture stopped")
    except Exception as e:
        print("error detected: ", e)
    finally:
        if connection:
            connection.disconnect()
            print("disconnected")

def save_users_csv():
    zk = ZK(IP, PORT)
    connection = None
    try:
        connection = zk.connect()
        connection.disable_device()
        print("device disable")
        users = connection.get_users()
        fingers = connection.get_templates()
        with open("users_data.csv", "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "UID",
                "Name",
                "Privilege",
                "Password",
                "Group ID",
                "User ID",
                "Finger Index",
                "Template Data",
                "Template Size",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for user in users:
                privilege = "Admin" if user.privilege == const.USER_ADMIN else "User"
                user_fingers = [f for f in fingers if f.uid == user.uid]

                if user_fingers:
                    print("user fingers found")
                    for finger in user_fingers:
                        writer.writerow(
                                {
                                    "UID": user.uid,
                                    "Name": user.name or "N/A",
                                    "Privilege": privilege,
                                    "Password": user.password or "N/A",
                                    "Group ID": user.group_id or "N/A",
                                    "User ID": user.user_id or "N/A",
                                    "Finger Index": finger.fid,
                                    "Template Data": finger.data,
                                    "Template Size": len(finger.data),
                                }
                            )
                else:
                    print("error finger not found")
                    writer.writerow(
                        {
                            "UID": user.uid,
                            "Name": user.name or "N/A",
                            "Privilege": privilege,
                            "Password": user.password or "N/A",
                            "Group ID": user.group_id or "N/A",
                            "User ID": user.user_id or "N/A",
                            "Finger Index": "N/A",
                            "Template Size": "N/A",
                        }
                    )
    except Exception as e:
        print("error detected: ", e)
    finally:
        if connection:
            connection.enable_device()
            connection.disconnect()
            print("disconnected")

def save_users_csv_template():
    zk = ZK(IP, PORT)
    connection = None

    try:
        connection = zk.connect()
        connection.disable_device()
        print("device disable")

        users = connection.get_users()
        fingers = connection.get_templates()

        with open("users_data_template.csv", "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "UID",
                "Name",
                "Privilege",
                "Password",
                "Group ID",
                "User ID",
                "Finger Index",
                "Template Data",
                "Template Size",
                "Finger Valid",
                "Finger Mark",
            ]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for user in users:
                privilege = "Admin" if user.privilege == const.USER_ADMIN else "User"
                user_fingers = [f for f in fingers if f.uid == user.uid]

                if user_fingers:
                    print(f"user fingers found -> {user.name} ({user.user_id})")

                    for finger in user_fingers:
                        writer.writerow(
                            {
                                "UID": user.uid,
                                "Name": user.name or "",
                                "Privilege": privilege,
                                "Password": user.password or "",
                                "Group ID": user.group_id or "",
                                "User ID": user.user_id or "",
                                "Finger Index": finger.fid,
                                "Template Data": repr(finger.template),
                                "Template Size": finger.size,
                                "Finger Valid": getattr(finger, "valid", ""),
                                "Finger Mark": repr(getattr(finger, "mark", b"")),
                            }
                        )
                else:
                    print(f"error finger not found -> {user.name} ({user.user_id})")
                    writer.writerow(
                        {
                            "UID": user.uid,
                            "Name": user.name or "",
                            "Privilege": privilege,
                            "Password": user.password or "",
                            "Group ID": user.group_id or "",
                            "User ID": user.user_id or "",
                            "Finger Index": "",
                            "Template Data": "",
                            "Template Size": "",
                            "Finger Valid": "",
                            "Finger Mark": "",
                        }
                    )

        print("CSV generado correctamente")

    except Exception as e:
        print("error detected:", e)

    finally:
        if connection:
            connection.enable_device()
            connection.disconnect()
            print("disconnected")

def save_users_and_templates_to_csv():
    zk = ZK(IP, PORT)
    connection = None
    try:
        connection = zk.connect()
        connection.disable_device()
        print("Dispositivo conectado y deshabilitado para operaciones seguras.")

        users = connection.get_users()
        templates = connection.get_templates()

        with open(
            "users_data_with_template.csv", mode="w", newline="", encoding="utf-8"
        ) as csvfile:
            fieldnames = [
                "User ID",
                "Password",
                "UID (User)",
                "Template UID",
                "Template Mark",
                "Template Data(json)",
                "Template Data",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for user in users:
                user_templates = [t for t in templates if t.uid == user.uid]
                if user_templates:
                    for template in user_templates:
                        writer.writerow(
                            {
                                "User ID": user.user_id or "N/A",
                                "Password": user.password or "N/A",
                                "UID (User)": user.uid,
                                "Template UID": template.uid,
                                "Template Mark": template.mark,
                                "Template Data(json)": template.json_pack(),
                                "Template Data": template.data,
                            }
                        )
                else:
                    # Si el usuario no tiene huellas digitales, se guarda con datos básicos
                    writer.writerow(
                        {
                            "User ID": user.user_id or "N/A",
                            "Password": user.password or "N/A",
                            "UID (User)": user.uid,
                            "Template UID": "N/A",
                            "Template Mark": "N/A",
                            "Template Data(json)": "N/A",
                            "Template Data": "N/A",
                        }
                    )

        print(f"Usuarios y plantillas de huellas guardados.")

    except Exception as e:
        print("Error al guardar usuarios y plantillas de huellas:", e)
    finally:
        if connection:
            connection.enable_device()
            connection.disconnect()
            print("Dispositivo habilitado y desconectado.")

def clone_fingerprint_from_ivan():
    zk = ZK(IP, PORT)
    connection = None

    try:
        print("Conectando al dispositivo...")
        connection = zk.connect()
        connection.disable_device()
        print("Dispositivo deshabilitado")

        uid = 999
        user_id = "999"
        name = "Prueba Ivan Clone"

        connection.set_user(
            uid=uid,
            name=name,
            privilege=const.USER_DEFAULT,
            password="",
            group_id="",
            user_id=user_id
        )

        print(f"Usuario creado: {user_id}")

        users = connection.get_users()

        target_user = next((u for u in users if str(u.user_id) == user_id), None)
        source_user = next((u for u in users if u.name.strip().lower() == "ivan"), None)

        if not target_user:
            print("No se encontró el usuario destino")
            return

        if not source_user:
            print("No se encontró a Ivan en el reloj")
            return

        print(f"Usuario destino: {target_user.user_id} (UID={target_user.uid})")
        print(f"Usuario origen: {source_user.name} (UID={source_user.uid})")

        templates = connection.get_templates()
        ivan_fingers = [f for f in templates if f.uid == source_user.uid]

        if not ivan_fingers:
            print("Ivan no tiene huellas")
            return

        print(f"Ivan tiene {len(ivan_fingers)} huella(s)")

        for f in ivan_fingers:
            print(f"   -> FID: {f.fid}, SIZE: {f.size}")

        # ==========================
        # 4) CLONAR HUELLA
        # ==========================
        source_finger = ivan_fingers[0]

        new_finger = copy.copy(source_finger)
        new_finger.uid = target_user.uid

        print("Clonando huella...")
        print(f"   UID origen: {source_finger.uid}")
        print(f"   UID destino: {new_finger.uid}")
        print(f"   FID: {new_finger.fid}")

        # ==========================
        # 5) GUARDAR HUELLA
        # ==========================
        connection.save_user_template(target_user, [new_finger])

        print("HUELLA CLONADA CORRECTAMENTE")

    except Exception as e:
        print("Error:", e)

    finally:
        if connection:
            try:
                connection.enable_device()
            except:
                pass
            connection.disconnect()
            print("🔌 Desconectado")

def clone_from_csv(source_name="Ivan"):
    zk = ZK(IP, PORT)
    connection = None

    try:
        print("Conectando al dispositivo...")
        connection = zk.connect()
        connection.disable_device()
        print("Dispositivo deshabilitado")

        new_uid = 999
        new_user_id = "999"
        new_name = "Prueba Ivan Clone"

        connection.set_user(
            uid=new_uid,
            name=new_name,
            privilege=const.USER_DEFAULT,
            password="1234",
            group_id="",
            user_id=new_user_id
        )

        print(f"Usuario creado: {new_user_id}")

        # Obtener usuario real del reloj
        users = connection.get_users()
        target_user = next((u for u in users if str(u.user_id) == str(new_user_id)), None)

        if not target_user:
            print("No se encontró el usuario nuevo en el reloj")
            return

        print(f"Usuario destino encontrado: {target_user.user_id} ({target_user.name})")

        source_row = None

        with open("users_data_template.csv", "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                if row["Name"].strip().lower() == source_name.strip().lower() and row["Template Data"]:
                    source_row = row
                    break

        if not source_row:
            print(f"No se encontró huella de {source_name} en el CSV")
            return

        print(f"Huella encontrada en CSV para {source_name}")

        template_bytes = ast.literal_eval(source_row["Template Data"])
        finger_mark = ast.literal_eval(source_row["Finger Mark"]) if source_row["Finger Mark"] else b""

        fid = int(source_row["Finger Index"])
        valid = int(source_row["Finger Valid"]) if source_row["Finger Valid"] else 1
        size = int(source_row["Template Size"])

        print(" Datos reconstruidos:")
        print(f"   FID: {fid}")
        print(f"   VALID: {valid}")
        print(f"   SIZE: {size}")
        print(f"   TEMPLATE BYTES: {len(template_bytes)}")
        print(f"   MARK BYTES: {len(finger_mark)}")

        templates = connection.get_templates()

        if not templates:
            print("No hay templates base en el reloj")
            return

        base_finger = templates[0]
        new_finger = copy.copy(base_finger)

        new_finger.uid = target_user.uid
        new_finger.fid = fid
        new_finger.valid = valid
        new_finger.template = template_bytes
        new_finger.size = size

        if hasattr(new_finger, "mark"):
            new_finger.mark = finger_mark

        if hasattr(new_finger, "repack"):
            try:
                new_finger.repack()
                print("repack ejecutado")
            except Exception as e:
                print("⚠No se pudo ejecutar repack:", e)

        print(f"Guardando huella en usuario {target_user.user_id}, fid={fid}...")
        connection.save_user_template(target_user, [new_finger])

        print("HUELLA CLONADA DESDE CSV")

    except Exception as e:
        print("Error al crear usuario:", e)

    finally:
        if connection:
            connection.enable_device()
            connection.disconnect()
            print("🔌 Disconnected")

###TEST ACTIVAR REGISTRO DE USUARIO EN RELOJ
def test_enroll():
    zk = ZK(IP, port=PORT, timeout=10)
    conn = None

    try:
        print("Conectando al reloj...")
        conn = zk.connect()
        print("Conectado correctamente")

        print("Deshabilitando dispositivo...")
        conn.disable_device()

        # Datos del nuevo usuario de prueba
        new_uid = 888
        new_user_id = "88"
        new_name = "Prueba Activación"

        print("Creando usuario de prueba...")
        conn.set_user(
            uid=new_uid,
            name=new_name,
            privilege=const.USER_DEFAULT,
            password="",
            group_id="",
            user_id=new_user_id,
            card=0
        )

        print("Usuario creado correctamente")

        print("Habilitando dispositivo para permitir interacción...")
        conn.enable_device()

        time.sleep(2)

        print("Lanzando modo de enrolamiento de huella...")
        result = conn.enroll_user(
            uid=new_uid,
            temp_id=0,      
            user_id=new_user_id
        )

        print(f"Resultado enroll_user: {result}")
        print("Ahora revisa el reloj físicamente.")
        print("Debería pedir colocar el dedo para registrar huella.")

        input("Presiona ENTER cuando termines la prueba...")

    except Exception as e:
        print(f"ERROR: {e}")

    finally:
        try:
            if conn:
                print("Cancelando captura si sigue activa...")
                try:
                    conn.cancel_capture()
                except:
                    pass

                print("Habilitando dispositivo al salir...")
                try:
                    conn.enable_device()
                except:
                    pass

                print("Desconectando...")
                conn.disconnect()
        except Exception as e:
            print(f"Error al cerrar conexión: {e}")

if __name__ == "__main__":
    #livestream_capture()
    #test()
    #save_users_csv()
    #save_users_csv_template()
    test_enroll()