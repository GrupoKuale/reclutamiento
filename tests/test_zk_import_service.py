from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase


class FakeUser:
    def __init__(self, user_id, uid, name="Test User"):
        self.user_id = user_id
        self.uid = uid
        self.name = name


class FakeTemplate:
    def __init__(self, uid, finger_id, template=b"\x00\x01\x02", valid=1):
        self.uid = uid
        self.finger_id = finger_id
        self.template = template
        self.valid = valid


class TestZkImportService(TransactionCase):

    def setUp(self):
        super().setUp()
        # Crear datos mínimos en la BD de prueba
        self.device = self.env["zk.device"].create({
            "name": "Reloj Test",
            "ip": "192.168.1.100",
            "port": 4370,
        })
        self.employee = self.env["hr.employee"].create({
            "name": "Juan Pérez",
            "device_id_num": 1001,
        })

    @patch("zk_sync.services.zk_import_service.ZK")
    def test_import_crea_template(self, MockZK):
        """Si el reloj devuelve un usuario con template, debe crearse en Odoo."""
        # Configura el mock del reloj
        conn = MagicMock()
        conn.get_users.return_value = [FakeUser(user_id=1001, uid=5)]
        conn.get_templates.return_value = [FakeTemplate(uid=5, finger_id=0)]
        MockZK.return_value.connect.return_value = conn

        from odoo.addons.reclutamiento__kuale.services.zk_export_service import ZkImportService
        svc = ZkImportService(self.env)
        svc.import_from_device(self.device)

        template = self.env["zk.biometric.template"].search([
            ("employee_id", "=", self.employee.id),
            ("finger_index", "=", 0),
        ])
        self.assertEqual(len(template), 1)
        self.assertEqual(template.source_device_id.id, self.device.id)

    @patch("zk_sync.services.zk_import_service.ZK")
    def test_import_no_duplica_template(self, MockZK):
        """Si el template ya existe, debe actualizarse, no duplicarse."""
        conn = MagicMock()
        conn.get_users.return_value = [FakeUser(user_id=1001, uid=5)]
        conn.get_templates.return_value = [FakeTemplate(uid=5, finger_id=0, template=b"\xFF")]
        MockZK.return_value.connect.return_value = conn

        from odoo.addons.reclutamiento__kuale.services.zk_export_service import ZkImportService
        svc = ZkImportService(self.env)
        svc.import_from_device(self.device)
        svc.import_from_device(self.device)  # Segunda vez

        templates = self.env["zk.biometric.template"].search([
            ("employee_id", "=", self.employee.id),
        ])
        self.assertEqual(len(templates), 1, "No debe haber duplicados")

    @patch("zk_sync.services.zk_import_service.ZK")
    def test_import_omite_usuario_sin_empleado(self, MockZK):
        """Si el user_id del reloj no tiene empleado en Odoo, debe omitirse sin error."""
        conn = MagicMock()
        conn.get_users.return_value = [FakeUser(user_id=9999, uid=99)]  # No existe
        conn.get_templates.return_value = []
        MockZK.return_value.connect.return_value = conn

        from odoo.addons.reclutamiento__kuale.services.zk_export_service import ZkImportService
        svc = ZkImportService(self.env)
        svc.import_from_device(self.device)  # No debe lanzar excepción

        templates = self.env["zk.biometric.template"].search([])
        self.assertEqual(len(templates), 0)

    @patch("zk_sync.services.zk_import_service.ZK")
    def test_import_error_de_red_actualiza_estado(self, MockZK):
        """Si el reloj no responde, el estado del device debe quedar en 'error'."""
        MockZK.return_value.connect.side_effect = Exception("Connection refused")

        from odoo.addons.reclutamiento__kuale.services.zk_export_service import ZkImportService
        svc = ZkImportService(self.env)

        with self.assertRaises(Exception):
            svc.import_from_device(self.device)

        self.assertEqual(self.device.state, "error")