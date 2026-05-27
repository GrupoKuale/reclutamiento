# -*- coding: utf-8 -*-
import base64
import logging
import os
import platform
import subprocess
import tempfile

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

SCAN_DPI    = 300
IS_WINDOWS  = platform.system() == 'Windows'
WIA_FLATBED = 1
SCAN_ROTATE = 0

# Carta a 300 DPI: 8.5 x 11 in = 2550 x 3300 px
CARTA_W_PX = int(8.5  * SCAN_DPI)   # 2550
CARTA_H_PX = int(11.0 * SCAN_DPI)   # 3300


def _coinit():
    try:
        import pythoncom
        pythoncom.CoInitialize()
        return True
    except Exception:
        return False


def _couninit():
    try:
        import pythoncom
        pythoncom.CoUninitialize()
    except Exception:
        pass


class ScannerController(http.Controller):

    # ──────────────────────────────────────────────────────────────────────────
    # Rutas HTTP
    # ──────────────────────────────────────────────────────────────────────────

    @http.route('/kuale/scan/status', type='json', auth='user', methods=['GET', 'POST'], csrf=False)
    def scanner_status(self, **kwargs):
        if IS_WINDOWS:
            available, device = self._check_wia()
        else:
            device    = self._detect_sane()
            available = bool(device)
            if not available:
                device = self._sane_diagnostics()
        return {'available': available, 'device': device, 'platform': platform.system()}

    # ── hr.applicant.documentation ────────────────────────────────────────────

    @http.route('/kuale/scan/<int:doc_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def trigger_scan(self, doc_id, **kwargs):
        """Escanea directamente y guarda (ruta legacy)."""
        doc = request.env['hr.applicant.documentation'].sudo().browse(doc_id)
        if not doc.exists():
            return {'success': False, 'error': f'Documento {doc_id} no encontrado.'}
        try:
            if IS_WINDOWS:
                pdf_b64, filename = self._scan_windows(doc.doc_type)
            else:
                device = self._detect_sane()
                if not device:
                    return {'success': False, 'error': 'Escáner no detectado.'}
                pdf_b64, filename = self._scan_linux(device, doc.doc_type)
        except Exception as e:
            _logger.error('Error escaneo: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
        try:
            att_id = doc.save_scanned_file(pdf_b64, filename)
        except Exception as e:
            _logger.error('Error guardando: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
        return {
            'success': True, 'attachment_id': att_id,
            'preview_url': f'/web/content/{att_id}?download=false',
            'filename': filename, 'doc_id': doc_id, 'state': 'scanned',
        }

    @http.route('/kuale/scan/page/<int:doc_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def scan_additional_page(self, doc_id, **kwargs):
        doc = request.env['hr.applicant.documentation'].sudo().browse(doc_id)
        if not doc.exists():
            return {'success': False, 'error': f'Documento {doc_id} no encontrado.'}
        try:
            if IS_WINDOWS:
                pdf_b64, _ = self._scan_windows(doc.doc_type)
            else:
                device = self._detect_sane()
                if not device:
                    return {'success': False, 'error': 'Escaner no detectado.'}
                pdf_b64, _ = self._scan_linux(device, doc.doc_type)
        except Exception as e:
            _logger.error('Error escaneando pagina: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
        Buffer     = request.env['hr.scan.page.buffer'].sudo()
        page_count = Buffer.search_count([('doc_id', '=', doc_id)])
        Buffer.create({'doc_id': doc_id, 'page_data': pdf_b64, 'sequence': page_count + 1})
        total = page_count + 1
        _logger.info('Pagina %d guardada en buffer para doc_id=%d', total, doc_id)
        return {'success': True, 'page_count': total, 'doc_id': doc_id}

    @http.route('/kuale/scan/merge/<int:doc_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def merge_and_save(self, doc_id, **kwargs):
        doc = request.env['hr.applicant.documentation'].sudo().browse(doc_id)
        if not doc.exists():
            return {'success': False, 'error': f'Documento {doc_id} no encontrado.'}
        Buffer = request.env['hr.scan.page.buffer'].sudo()
        pages  = Buffer.search([('doc_id', '=', doc_id)], order='sequence asc')
        if not pages:
            return {'success': False, 'error': 'No hay paginas escaneadas.'}
        try:
            import datetime
            filename      = f'scan_{doc.doc_type}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            pages_b64     = [p.page_data for p in pages]
            final_pdf_b64 = pages_b64[0] if len(pages_b64) == 1 else self._merge_pdfs(pages_b64)
            att_id        = doc.save_scanned_file(final_pdf_b64, filename)
            pages.unlink()
            _logger.info('PDF final guardado: %s (%d paginas)', filename, len(pages_b64))
            return {
                'success': True, 'attachment_id': att_id,
                'preview_url': f'/web/content/{att_id}?download=false',
                'filename': filename, 'doc_id': doc_id, 'state': 'scanned',
            }
        except Exception as e:
            _logger.error('Error uniendo PDFs: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    # ── formatos_wizard_line ──────────────────────────────────────────────────

    @http.route('/kuale/scan/formato/page/<int:line_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def scan_formato_page(self, line_id, **kwargs):
        line = request.env['reclutamiento__kuale.formatos_wizard_line'].sudo().browse(line_id)
        if not line.exists():
            return {'success': False, 'error': f'Línea {line_id} no encontrada.'}
        try:
            if IS_WINDOWS:
                pdf_b64, _ = self._scan_windows(f'formato_{line_id}')
            else:
                device = self._detect_sane()
                if not device:
                    return {'success': False, 'error': 'Escáner no detectado.'}
                pdf_b64, _ = self._scan_linux(device, f'formato_{line_id}')
        except Exception as e:
            _logger.error('Error escaneando página formato: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
        # doc_id negativo para no colisionar con hr.applicant.documentation
        buffer_key = -line_id
        Buffer     = request.env['hr.scan.page.buffer'].sudo()
        page_count = Buffer.search_count([('doc_id', '=', buffer_key)])
        Buffer.create({'doc_id': buffer_key, 'page_data': pdf_b64, 'sequence': page_count + 1})
        total = page_count + 1
        _logger.info('Página %d en buffer para formato line_id=%d', total, line_id)
        return {'success': True, 'page_count': total, 'line_id': line_id}

    @http.route('/kuale/scan/formato/merge/<int:line_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def merge_formato_and_save(self, line_id, **kwargs):
        line = request.env['reclutamiento__kuale.formatos_wizard_line'].sudo().browse(line_id)
        if not line.exists():
            return {'success': False, 'error': f'Línea {line_id} no encontrada.'}
        buffer_key = -line_id
        Buffer     = request.env['hr.scan.page.buffer'].sudo()
        pages      = Buffer.search([('doc_id', '=', buffer_key)], order='sequence asc')
        if not pages:
            return {'success': False, 'error': 'No hay páginas escaneadas.'}
        try:
            import datetime
            filename      = f'scan_formato_{line_id}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            pages_b64     = [p.page_data for p in pages]
            final_pdf_b64 = pages_b64[0] if len(pages_b64) == 1 else self._merge_pdfs(pages_b64)
            # Solo guarda en memoria temporal; el usuario debe pulsar "Confirmar"
            # para que action_confirm_line persista en hr.applicant
            line.sudo().write({
                'attachment_datas':        final_pdf_b64,
                'attachment_display_name': filename,
            })
            pages.unlink()
            _logger.info('PDF formato guardado en buffer temporal: %s (%d páginas)', filename, len(pages_b64))
            return {'success': True, 'filename': filename, 'line_id': line_id}
        except Exception as e:
            _logger.error('Error uniendo PDFs formato: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    # ── formatos_wizard (contrato) ────────────────────────────────────────────

    @http.route('/kuale/scan/contrato/page/<int:wizard_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def scan_contrato_page(self, wizard_id, **kwargs):
        wizard = request.env['reclutamiento__kuale.formatos_wizard'].sudo().browse(wizard_id)
        if not wizard.exists():
            return {'success': False, 'error': f'Wizard {wizard_id} no encontrado.'}
        try:
            if IS_WINDOWS:
                pdf_b64, _ = self._scan_windows(f'contrato_{wizard_id}')
            else:
                device = self._detect_sane()
                if not device:
                    return {'success': False, 'error': 'Escáner no detectado.'}
                pdf_b64, _ = self._scan_linux(device, f'contrato_{wizard_id}')
        except Exception as e:
            _logger.error('Error escaneando contrato: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
        # offset 1_000_000 para no colisionar con docs ni formatos
        buffer_key = 1000000 + wizard_id
        Buffer     = request.env['hr.scan.page.buffer'].sudo()
        page_count = Buffer.search_count([('doc_id', '=', buffer_key)])
        Buffer.create({'doc_id': buffer_key, 'page_data': pdf_b64, 'sequence': page_count + 1})
        total = page_count + 1
        _logger.info('Página %d en buffer para contrato wizard_id=%d', total, wizard_id)
        return {'success': True, 'page_count': total, 'wizard_id': wizard_id}

    @http.route('/kuale/scan/contrato/merge/<int:wizard_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def merge_contrato_and_save(self, wizard_id, **kwargs):
        wizard = request.env['reclutamiento__kuale.formatos_wizard'].sudo().browse(wizard_id)
        if not wizard.exists():
            return {'success': False, 'error': f'Wizard {wizard_id} no encontrado.'}
        buffer_key = 1000000 + wizard_id
        Buffer     = request.env['hr.scan.page.buffer'].sudo()
        pages      = Buffer.search([('doc_id', '=', buffer_key)], order='sequence asc')
        if not pages:
            return {'success': False, 'error': 'No hay páginas escaneadas.'}
        try:
            import datetime
            filename      = f'scan_contrato_{wizard_id}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            pages_b64     = [p.page_data for p in pages]
            final_pdf_b64 = pages_b64[0] if len(pages_b64) == 1 else self._merge_pdfs(pages_b64)
            # ── CORREGIDO: persistir inmediatamente en hr.applicant ───────────
            wizard._save_contract_attachment(final_pdf_b64, filename)
            pages.unlink()
            _logger.info('PDF contrato guardado y persistido: %s (%d páginas)', filename, len(pages_b64))
            return {'success': True, 'filename': filename, 'wizard_id': wizard_id}
        except Exception as e:
            _logger.error('Error uniendo PDFs contrato: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    # ── formatos_wizard (formato contratación GK) ─────────────────────────────

    @http.route('/kuale/scan/formato_contratacion/page/<int:wizard_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def scan_formato_contratacion_page(self, wizard_id, **kwargs):
        wizard = request.env['reclutamiento__kuale.formatos_wizard'].sudo().browse(wizard_id)
        if not wizard.exists():
            return {'success': False, 'error': f'Wizard {wizard_id} no encontrado.'}
        try:
            if IS_WINDOWS:
                pdf_b64, _ = self._scan_windows(f'fmt_contratacion_{wizard_id}')
            else:
                device = self._detect_sane()
                if not device:
                    return {'success': False, 'error': 'Escáner no detectado.'}
                pdf_b64, _ = self._scan_linux(device, f'fmt_contratacion_{wizard_id}')
        except Exception as e:
            _logger.error('Error escaneando formato contratacion: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}
        # offset 2_000_000 para no colisionar con contrato (1_000_000) ni docs ni formatos
        buffer_key = 2000000 + wizard_id
        Buffer     = request.env['hr.scan.page.buffer'].sudo()
        page_count = Buffer.search_count([('doc_id', '=', buffer_key)])
        Buffer.create({'doc_id': buffer_key, 'page_data': pdf_b64, 'sequence': page_count + 1})
        total = page_count + 1
        _logger.info('Página %d en buffer para formato_contratacion wizard_id=%d', total, wizard_id)
        return {'success': True, 'page_count': total, 'wizard_id': wizard_id}

    @http.route('/kuale/scan/formato_contratacion/merge/<int:wizard_id>', type='json', auth='user', methods=['POST'], csrf=False)
    def merge_formato_contratacion_and_save(self, wizard_id, **kwargs):
        wizard = request.env['reclutamiento__kuale.formatos_wizard'].sudo().browse(wizard_id)
        if not wizard.exists():
            return {'success': False, 'error': f'Wizard {wizard_id} no encontrado.'}
        buffer_key = 2000000 + wizard_id
        Buffer     = request.env['hr.scan.page.buffer'].sudo()
        pages      = Buffer.search([('doc_id', '=', buffer_key)], order='sequence asc')
        if not pages:
            return {'success': False, 'error': 'No hay páginas escaneadas.'}
        try:
            import datetime
            filename      = f'scan_fmt_contratacion_{wizard_id}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            pages_b64     = [p.page_data for p in pages]
            final_pdf_b64 = pages_b64[0] if len(pages_b64) == 1 else self._merge_pdfs(pages_b64)
            # ── Persistir inmediatamente en hr.applicant ──────────────────────
            wizard._save_formato_contratacion_attachment(final_pdf_b64, filename)
            pages.unlink()
            _logger.info('PDF formato_contratacion guardado y persistido: %s (%d páginas)', filename, len(pages_b64))
            return {'success': True, 'filename': filename, 'wizard_id': wizard_id}
        except Exception as e:
            _logger.error('Error uniendo PDFs formato_contratacion: %s', e, exc_info=True)
            return {'success': False, 'error': str(e)}

    # ──────────────────────────────────────────────────────────────────────────
    # Unión de PDFs
    # ──────────────────────────────────────────────────────────────────────────

    def _merge_pdfs(self, pages_b64):
        """Une lista de PDFs en base64 en un solo PDF. Usa pypdf o Pillow como fallback."""
        try:
            from pypdf import PdfWriter, PdfReader
            import io

            writer = PdfWriter()
            for page_b64 in pages_b64:
                reader = PdfReader(io.BytesIO(base64.b64decode(page_b64)))
                for page in reader.pages:
                    writer.add_page(page)

            output = io.BytesIO()
            writer.write(output)
            _logger.info('PDFs unidos con pypdf (%d páginas)', len(pages_b64))
            return base64.b64encode(output.getvalue()).decode()

        except ImportError:
            _logger.warning('pypdf no instalado, usando Pillow como fallback. pip install pypdf')
            return self._merge_pdfs_pillow(pages_b64)
        except Exception as e:
            _logger.error('Error con pypdf: %s — intentando Pillow', e)
            return self._merge_pdfs_pillow(pages_b64)

    def _merge_pdfs_pillow(self, pages_b64):
        """Fallback: convierte cada PDF a imagen RGB y los une en un solo PDF."""
        from PIL import Image
        import io

        images = []
        for page_b64 in pages_b64:
            img = Image.open(io.BytesIO(base64.b64decode(page_b64))).convert('RGB')
            images.append(img)

        output = io.BytesIO()
        images[0].save(
            output, 'PDF', resolution=SCAN_DPI,
            save_all=True, append_images=images[1:]
        )
        _logger.info('PDFs unidos con Pillow (%d páginas)', len(pages_b64))
        return base64.b64encode(output.getvalue()).decode()

    # ──────────────────────────────────────────────────────────────────────────
    # Utilidades compartidas
    # ──────────────────────────────────────────────────────────────────────────

    def _crop_to_letter(self, img_path, tmp):
        """Recorta la imagen a tamaño carta (2550x3300 px @ 300 DPI)."""
        try:
            from PIL import Image
            with Image.open(img_path) as im:
                iw, ih    = im.size
                crop_w    = min(iw, CARTA_W_PX)
                crop_h    = min(ih, CARTA_H_PX)

                _logger.info('Imagen: %dx%d recorte: %dx%d px', iw, ih, crop_w, crop_h)

                if crop_w == iw and crop_h == ih:
                    return img_path

                crop_path = os.path.join(tmp, 'scan_crop.jpg')
                im.crop((0, 0, crop_w, crop_h)).save(crop_path, 'JPEG', quality=95)
                return crop_path

        except ImportError:
            _logger.warning('Pillow no instalado — sin recorte.')
        except Exception as e:
            _logger.warning('No se pudo recortar: %s', e)
        return img_path

    def _img_to_pdf(self, img_path, pdf_path):
        """Convierte imagen a PDF. Intenta ImageMagick → Pillow → img2pdf → reportlab."""
        # ImageMagick (Linux)
        if self._cmd_exists('convert'):
            try:
                r = subprocess.run(
                    ['convert', '-density', str(SCAN_DPI),
                     img_path, '-compress', 'jpeg', '-quality', '85', pdf_path],
                    capture_output=True, text=True, timeout=60
                )
                if r.returncode == 0 and os.path.getsize(pdf_path) > 0:
                    _logger.info('PDF con ImageMagick')
                    return pdf_path
            except Exception:
                pass

        # Pillow
        try:
            from PIL import Image
            Image.open(img_path).convert('RGB').save(pdf_path, 'PDF', resolution=SCAN_DPI)
            if os.path.getsize(pdf_path) > 0:
                _logger.info('PDF con Pillow')
                return pdf_path
        except Exception as e:
            _logger.warning('Pillow falló: %s', e)

        # img2pdf
        try:
            import img2pdf
            data = img2pdf.convert(img_path)
            with open(pdf_path, 'wb') as f:
                f.write(data)
            if os.path.getsize(pdf_path) > 0:
                _logger.info('PDF con img2pdf')
                return pdf_path
        except Exception as e:
            _logger.warning('img2pdf falló: %s', e)

        # reportlab
        try:
            from reportlab.lib.pagesizes import LETTER
            from reportlab.platypus import SimpleDocTemplate, Image as RLImage
            pw, ph = LETTER
            m      = 10
            SimpleDocTemplate(pdf_path, pagesize=LETTER,
                              leftMargin=m, rightMargin=m,
                              topMargin=m, bottomMargin=m
                              ).build([RLImage(img_path, width=pw - m*2, height=ph - m*2)])
            if os.path.getsize(pdf_path) > 0:
                _logger.info('PDF con reportlab')
                return pdf_path
        except Exception as e:
            _logger.warning('reportlab falló: %s', e)

        raise RuntimeError('No se pudo generar el PDF. Instale: pip install Pillow')

    def _cmd_exists(self, cmd):
        import shutil
        return shutil.which(cmd) is not None

    # ──────────────────────────────────────────────────────────────────────────
    # WINDOWS — WIA
    # ──────────────────────────────────────────────────────────────────────────

    def _check_wia(self):
        coinit_done = _coinit()
        try:
            import win32com.client
            wia      = win32com.client.Dispatch('WIA.DeviceManager')
            devices  = wia.DeviceInfos
            scan_kw  = ('epson', 'es-500', 'scan', 'seiko')
            first_kw = first_any = None
            for i in range(1, devices.Count + 1):
                try:
                    dev  = devices.Item(i)
                    name = dev.Properties('Name').Value
                    if first_any is None:
                        first_any = name
                    if any(kw in name.lower() for kw in scan_kw) and first_kw is None:
                        first_kw = name
                except Exception:
                    pass
            chosen = first_kw or first_any
            return (True, chosen) if chosen else (False, None)
        except ImportError:
            return False, 'pywin32 no instalado'
        except Exception as e:
            return False, str(e)
        finally:
            if coinit_done:
                _couninit()

    def _wia_set_prop_by_name(self, item, name, value):
        try:
            item.Properties(name).Value = value
            _logger.info('WIA "%s" = %s  OK', name, value)
        except Exception as e:
            _logger.warning('WIA "%s" no disponible: %s', name, e)

    def _scan_windows(self, doc_type):
        import datetime
        import win32com.client

        ts       = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'scan_{doc_type}_{ts}.pdf'

        coinit_done = _coinit()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                img_path = os.path.join(tmp, 'scan.jpg')
                pdf_path = os.path.join(tmp, 'scan.pdf')

                # Conectar al escáner
                wia          = win32com.client.Dispatch('WIA.DeviceManager')
                devices      = wia.DeviceInfos
                scanner      = None
                scanner_name = None
                scan_kw      = ('epson', 'es-500', 'scan', 'seiko')

                for i in range(1, devices.Count + 1):
                    try:
                        dev  = devices.Item(i)
                        name = dev.Properties('Name').Value
                        if any(kw in name.lower() for kw in scan_kw):
                            scanner      = dev.Connect()
                            scanner_name = name
                            break
                    except Exception:
                        pass

                if scanner is None:
                    for i in range(1, devices.Count + 1):
                        try:
                            dev          = devices.Item(i)
                            scanner      = dev.Connect()
                            scanner_name = dev.Properties('Name').Value
                            break
                        except Exception:
                            pass

                if scanner is None:
                    raise RuntimeError('No se encontró ningún escáner WIA.')
                _logger.info('WIA: conectado a "%s"', scanner_name)

                item = scanner.Items(1)
                self._wia_set_prop_by_name(item, 'Horizontal Resolution', SCAN_DPI)
                self._wia_set_prop_by_name(item, 'Vertical Resolution',   SCAN_DPI)

                image = item.Transfer('{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}')
                image.SaveFile(img_path)
                _logger.info('Imagen guardada: %s', img_path)

                img_path = self._crop_to_letter(img_path, tmp)
                pdf_path = self._img_to_pdf(img_path, pdf_path)

                with open(pdf_path, 'rb') as f:
                    return base64.b64encode(f.read()).decode(), filename

        finally:
            if coinit_done:
                _couninit()

    # ──────────────────────────────────────────────────────────────────────────
    # LINUX — SANE
    # ──────────────────────────────────────────────────────────────────────────

    def _sane_diagnostics(self):
        import shutil
        if not shutil.which('scanimage'):
            return (
                'scanimage no encontrado. '
                'Instale: sudo apt-get install sane sane-utils libsane-epson2 imagemagick'
            )
        try:
            import grp, pwd
            user = pwd.getpwuid(os.getuid()).pw_name
            if user not in grp.getgrnam('scanner').gr_mem:
                return (
                    f'Usuario "{user}" sin permisos. '
                    f'Ejecute: sudo usermod -aG scanner {user} && sudo systemctl restart odoo'
                )
        except Exception:
            pass
        return 'Escáner no detectado. Verifique la conexión USB.'

    def _detect_sane(self):
        try:
            r      = subprocess.run(['scanimage', '-L'],
                                    capture_output=True, text=True, timeout=15)
            output = r.stdout + r.stderr
            _logger.info('scanimage -L: %s', output.strip())

            for line in output.splitlines():
                low = line.lower()
                if 'device' in low and ('epson' in low or 'es-500' in low or 'seiko' in low):
                    dev = self._parse_device_name(line)
                    if dev:
                        return dev

            for line in output.splitlines():
                if line.strip().lower().startswith('device'):
                    dev = self._parse_device_name(line)
                    if dev:
                        return dev

        except FileNotFoundError:
            _logger.warning('scanimage no instalado')
        except subprocess.TimeoutExpired:
            _logger.warning('Timeout en scanimage -L')
        except Exception as e:
            _logger.error('Error detectando SANE: %s', e)
        return None

    def _parse_device_name(self, line):
        s = line.find('`')
        e = line.find("'", s + 1)
        return line[s + 1:e] if s != -1 and e != -1 else None

    def _scan_linux(self, device, doc_type):
        import datetime
        ts       = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'scan_{doc_type}_{ts}.pdf'

        with tempfile.TemporaryDirectory() as tmp:
            tiff     = os.path.join(tmp, 'out.tiff')
            pdf_path = os.path.join(tmp, 'out.pdf')

            scan_cmd = [
                'scanimage',
                f'--device-name={device}',
                f'--resolution={SCAN_DPI}',
                '--mode=Color',
                '--format=tiff',
                f'--output-file={tiff}',
            ]

            try:
                test     = subprocess.run(
                    ['scanimage', f'--device-name={device}', '--help'],
                    capture_output=True, text=True, timeout=10
                )
                help_out = test.stdout + test.stderr
                if '-l ' in help_out or '--left-margin' in help_out:
                    scan_cmd += ['-l', '0', '-t', '0', '-x', '215.9', '-y', '279.4']
                    _logger.info('SANE: área carta configurada (-x 215.9 -y 279.4)')
            except Exception:
                pass

            r = subprocess.run(scan_cmd, capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                raise RuntimeError(f'scanimage error: {r.stderr}')
            if not os.path.exists(tiff) or os.path.getsize(tiff) == 0:
                raise RuntimeError('scanimage no generó TIFF.')

            img_path = self._crop_to_letter(tiff, tmp)
            pdf_path = self._img_to_pdf(img_path, pdf_path)

            with open(pdf_path, 'rb') as f:
                return base64.b64encode(f.read()).decode(), filename