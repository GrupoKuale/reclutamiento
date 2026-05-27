from unittest.mock import MagicMock, patch, call
import base64
from odoo.tests.common import TransactionCase


class TestZkExportService(TransactionCase):

    def setUp(self):
        super().setUp()
        self.device = self.env["zk.device"].create({
            "name": "Reloj Destino",
            "ip": "10.0.0.5",
            "port": 4370,
        })
        self.employee = self.env["hr.employee"].create({
            "name": "Ana García",
            "device_id_num": 2001,
        })
        # Template ficticio ya en Odoo
        self.env["zk.biometric.template"].create({
            "employee_id": self.employee.id,
            "device_employee_id": 2001,
            "uid": 10,
            "finger_index": 0,
            "biometric_type": "finger",
            "valid": True,
            "template_data": base64.b64encode(b"\xAA\xBB\xCC"),
        })

    @patch("zk_sync.services.zk_export_service.ZK")
    def test_export_crea_usuario_y_sube_template(self, MockZK):
        """Debe llamar a set_user() y save_user_template() en el reloj destino."""
        conn = MagicMock()
        # El reloj no tiene al empleado aún
        conn.get_users.return_value = []
        # Después de set_user, simula que el reloj asignó uid=7
        conn.get_users.side_effect = [
            [],                                  # Primera llamada: reloj vacío
            [FakeUser(user_id=2001, uid=7)],     # Segunda llamada: después de crear
        ]
        MockZK.return_value.connect.return_value = conn

        from odoo.addons.reclutamiento__kuale.services.zk_export_service import ZkExportService
        svc = ZkExportService(self.env)
        svc.export_employee_to_device(self.employee, self.device)

        conn.set_user.assert_called_once()
        conn.save_user_template.assert_called_once()

        sync = self.env["zk.sync.status"].search([
            ("employee_id", "=", self.employee.id),
            ("device_id", "=", self.device.id),
        ])
        self.assertEqual(sync.state, "done")

    @patch("zk_sync.services.zk_export_service.ZK")
    def test_export_no_duplica_usuario_existente(self, MockZK):
        """Si el usuario ya existe en el reloj, no debe llamar set_user()."""
        conn = MagicMock()
        conn.get_users.return_value = [FakeUser(user_id=2001, uid=7)]
        MockZK.return_value.connect.return_value = conn

        from odoo.addons.reclutamiento__kuale.services.zk_export_service import ZkExportService
        svc = ZkExportService(self.env)
        svc.export_employee_to_device(self.employee, self.device)

        conn.set_user.assert_not_called()
        conn.save_user_template.assert_called_once()

    @patch("zk_sync.services.zk_export_service.ZK")
    def test_export_error_marca_sync_error(self, MockZK):
        """Si falla la exportación, sync.status debe quedar en 'error'."""
        conn = MagicMock()
        conn.get_users.side_effect = Exception("Timeout")
        MockZK.return_value.connect.return_value = conn

        from odoo.addons.reclutamiento__kuale.services.zk_export_service import ZkExportService
        svc = ZkExportService(self.env)

        with self.assertRaises(Exception):
            svc.export_employee_to_device(self.employee, self.device)

        sync = self.env["zk.sync.status"].search([
            ("employee_id", "=", self.employee.id),
        ])
        self.assertEqual(sync.state, "error")
        self.assertEqual(sync.retry_count, 1)


class FakeUser:
    def __init__(self, user_id, uid):
        self.user_id = user_id
        self.uid = uid
        self.name = "Test"
        self.privilege = 0
        self.password = ""
        self.group_id = ""