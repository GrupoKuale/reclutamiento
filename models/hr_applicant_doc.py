from odoo.exceptions import ValidationError
from odoo import models, fields, api
from datetime import datetime,timedelta


class weekly_schedule(models.Model):
    _name = 'weekly_schedule'
    _description = 'weekly_schedule'

    name = fields.Char(string='Nombre', required=True)
    day_of_week = fields.Selection([
        ('monday', 'Lunes'),
        ('tuesday', 'Martes'),
        ('wednesday', 'Miércoles'),
        ('thursday', 'Jueves'),
        ('friday', 'Viernes'),
        ('saturday', 'Sábado'),
        ('sunday', 'Domingo')
    ], string='Día de la semana')
    rest_day = fields.Boolean(string='Descanso')
    start_time = fields.Char(string='Hora de inicio', required=True)
    end_time = fields.Char(string='Hora fin', required=True)
    break_time = fields.Integer(string='Tiempo descanso', required=True)
    break_start_time = fields.Char(string='Inicio descanso', required=True)
    break_end_time = fields.Char(string='Fin descanso', required=True, compute="_compute_break_end_time")

    @api.constrains('start_time', 'end_time', 'break_start_time', 'break_end_time')
    def _check_time_values(self):
        for record in self:
            print('record  weekly',record)
            if record.start_time:
                self._validate_time(record.start_time)
            if record.end_time:
                self._validate_time(record.end_time)
            if record.break_start_time:
                self._validate_time(record.break_start_time)
            if record.break_end_time:
                self._validate_time(record.break_end_time)

    def _validate_time(self, time_str):
        try:
            hour, minute = map(int, time_str.split(':'))
            if hour < 1 or hour > 23 or minute < 0 or minute > 59:
                raise ValidationError("Formato invalido.La hora debe estar entre 01:00 y 23:59.")
        except ValueError:
            raise ValidationError("Formato invalido. La hora debe estar en el formato HH:MM.")

    @api.depends('break_end_time')
    def _compute_break_end_time(self):
        for record in self:
            print('_compute_break_end_time',record)
            if record.break_start_time and record.break_time:
                print("data: ", record.break_start_time, " - ", record.break_time)
                record.break_end_time = record.break_start_time + str(record.break_time)


class hr_applicant_doc(models.Model):
    _name = 'hr_applicant_doc'
    _description = 'Documentation schedule'
    applicant_id = fields.Many2one('hr.applicant', string="Applicant")
    datetimeSession = fields.Datetime(string='Fecha y Hora', required=True)
    place = fields.Many2one(
        'res.company',
        string='Lugar', required=True
    )
    contactSession = fields.Many2one(
        'hr.employee',
        string='Contacto sesión contratación', required=True
    )
    workDate = fields.Date(string='Fecha laboral')
    weekly_schedule = fields.Many2many(
        'weekly_schedule',
        string='Horario semanal', required=False
    )

    format_id = fields.Many2one('hr.applicant.doc.format', string='Formato a enviar', ondelete='set null')
    duration = fields.Char(string='Duración de la contratación')

    @api.model
    def default_get(self, fields_list):
        defaults = super(hr_applicant_doc, self).default_get(fields_list)
        applicant_id = self._context.get('default_applicant_id')
        print("obtener applicant default:",applicant_id)
        defaults['applicant_id'] = int(applicant_id)
        return defaults

    @api.model
    def create(self, vals):
        record = super(hr_applicant_doc, self).create(vals)
        # Agendar en calendario
        try:
            fecha_start_str = vals.get('datetimeSession')
            fecha_start = datetime.strptime(fecha_start_str, '%Y-%m-%d %H:%M:%S')
            contacto = vals.get('contactSession')
            fecha_stop = fecha_start + timedelta(hours=1)
            calendar_value = {
                'name': 'Recibir candidato a contratación',
                'start': fecha_start,
                'stop': fecha_stop,
                'partner_ids': [(4, contacto)]
            }
            self.env['calendar.event'].sudo().create(calendar_value)
        except Exception as e:
            print("Error calendar:", e)

        return record
    
    def action_send(self):
        self.ensure_one()
        self._fill_and_send_pdf()
        return {'type': 'ir.actions.act_window_close'}

    def _fill_and_send_pdf(self):
        import base64
        import io
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import letter

        applicant = self.applicant_id
        email_to = applicant.email_from
        if not email_to:
            raise ValidationError('El candidato no tiene correo electrónico registrado.')

        if not self.format_id or not self.format_id.pdf_file:
            raise ValidationError('No se ha seleccionado un formato PDF.')

        # Datos a insertar
        fecha_hora = self.datetimeSession
        fecha_str = fecha_hora.strftime('%d/%m/%Y') if fecha_hora else ''
        hora_str  = fecha_hora.strftime('%H:%M') if fecha_hora else ''
        contacto  = self.contactSession.name if self.contactSession else ''
        duracion  = self.duration or ''
        tel     = self.contactSession.work_phone or self.contactSession.mobile_phone or '' if self.contactSession else ''
        mail_rh = self.contactSession.user_id.email or self.contactSession.work_email or '' if self.contactSession else ''

        # Leer PDF base
        pdf_bytes = base64.b64decode(self.format_id.pdf_file)
        base_reader = PdfReader(io.BytesIO(pdf_bytes))

        # Crear overlay con los datos
        packet = io.BytesIO()
        c = rl_canvas.Canvas(packet, pagesize=letter)
        c.setFont('Helvetica', 9)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(185, 222, fecha_str)
        c.drawString(355, 222, hora_str)
        c.drawString(115, 200, contacto)
        c.drawString(390, 200, duracion)
        c.drawString(115, 78,  tel)
        c.drawString(115, 61,  mail_rh)
        c.save()
        packet.seek(0)

        # Fusionar
        from pypdf import PdfReader as PR2
        overlay_reader = PR2(packet)
        writer = PdfWriter()
        base_page = base_reader.pages[0]
        base_page.merge_page(overlay_reader.pages[0])
        writer.add_page(base_page)

        output = io.BytesIO()
        writer.write(output)
        pdf_filled = base64.b64encode(output.getvalue()).decode()

        # Crear adjunto
        att = self.env['ir.attachment'].sudo().create({
            'name': self.format_id.pdf_filename or 'requisitos_contratacion.pdf',
            'datas': pdf_filled,
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
            'mimetype': 'application/pdf',
        })

        # Enviar correo
        body = f"""
        <p>Estimado/a <strong>{applicant.partner_name}</strong>,</p>
        <p>Le informamos que su proceso de contratación continúa. A continuación los detalles:</p>
        <ul>
            <li><strong>Fecha y hora:</strong> {fecha_str} {hora_str}</li>
            <li><strong>Lugar:</strong> {self.place.name if self.place else ''}</li>
            <li><strong>Contacto:</strong> {contacto}</li>
            <li><strong>Duración:</strong> {duracion}</li>
        </ul>
        <p>Se adjunta la carta con los requisitos necesarios para su presentación.</p>
        <p>Atentamente,<br/>Grupo Kuale</p>
        """
        mail = self.env['mail.mail'].sudo().create({
            'subject': 'Requisitos de contratación - Grupo Kuale',
            'body_html': body,
            'email_to': email_to,
            'attachment_ids': [(6, 0, [att.id])],
            'auto_delete': True,
        })
        mail.send()

class HrApplicantDocFormat(models.Model):
    _name = 'hr.applicant.doc.format'
    _description = 'Formato de requisitos de contratación'

    name = fields.Char(string='Nombre', required=True)
    pdf_file = fields.Binary(string='Archivo PDF', attachment=True)
    pdf_filename = fields.Char(string='Nombre archivo')
    docx_file = fields.Binary(string='Archivo Word (.docx)', attachment=True)
    docx_filename = fields.Char(string='Nombre archivo Word')
    active = fields.Boolean(default=True)