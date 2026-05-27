
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.http import request
import random
import string
from datetime import date,timedelta
class mail_mail(models.Model):
    _name = 'reclutamiento__kuale.mail_mail'
    _description = "reclutamiento__kuale.mail_mail"

    email_from = fields.Text('Email From', help='Email from')
    email_to = fields.Text('Email To')
    email_cc = fields.Text('Cc')
    subject = fields.Text('Subject')
    body_html = fields.Html('Body', default='', sanitize_style=True)
    scheduled_date = fields.Date('Fecha límite', default=fields.Date.context_today)
    attachments = fields.Binary(string='Attachments')
    sendMail = fields.Boolean(string='Enviar correo', default=True)
    templateMail = fields.Many2one(
         'mail.template',
         string='Mail Template'
     )
    @api.depends('email_from')
    def _compute_applicant_url(self):
        for record in self:
            applicant_id = self._context.get('applicant_id')
            if applicant_id:
                # Generar un token aleatorio de 8 caracteres
                token = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                base_url = request.httprequest.host_url
                # Buscar el registro con el applicant_id especificado
                existing_record = self.env['vigency_complement'].sudo().search([('applicant_id', '=', applicant_id)], limit=1)
                if existing_record:
                    # Obtener la fecha de vigency
                    vigency_date = fields.Datetime.from_string(existing_record.vigency)
                    current_date = fields.Datetime.from_string(fields.Datetime.now())
                    #print("vigency_date: ", vigency_date,"-current_date: ",current_date)
                    # Comparar si han pasado más de 7 días
                    if current_date > vigency_date + timedelta(days=7):
                        print("Actualizar registro new token")
                        existing_record.sudo().write({
                            'token': token,
                            'vigency': fields.Datetime.now(),
                        })
                    else:
                        print("Vigency is still valid.",existing_record.token)
                        record.applicant_url = f"{base_url}/jobs/formRecruitment/{applicant_id}/{existing_record.token}"
                else:
                    print("Crear registro new token")
                    record.applicant_url = f"{base_url}/jobs/formRecruitment/{applicant_id}/{token}"
                    try:
                        self.env['vigency_complement'].sudo().create({
                            'applicant_id': applicant_id,
                            'token': token,
                            'vigency':  fields.Datetime.now(),
                        })
                    except Exception as e:
                        print("Error al crear el registro en vigency_complement:", e)

    applicant_url = fields.Char('Complement Form URL: ', compute='_compute_applicant_url')

    @api.model
    def default_get(self, fields_list):
        defaults = super(mail_mail, self).default_get(fields_list)
        applicant_id = self._context.get('applicant_id')
        applicant_record = self.env['hr.applicant'].search([('id', '=', applicant_id)])[0] if self.env[
            'hr.applicant'].search([('id', '=', applicant_id)]) else False

        if applicant_record:
            defaults['email_from'] = applicant_record.email_from
        return defaults

    def sendEmail(self):
        print("enviando...")
        template = self.templateMail
        email_from = self.email_from
        if template and email_from:
            print("template ",template)
            try:
                additional_text = "Complement Form URL: "+self.applicant_url
                rendered_body = template.body_html
                full_body = additional_text + rendered_body
                mail_values = {
                    'body_html': full_body,
                    'subject': template.subject,
                    'email_to': email_from,
                    'auto_delete': True,
                }
                template.send_mail(self.id, email_values=mail_values, force_send=True)
                applicant = self.env['hr.applicant'].search([('id', '=', self.applicant_url)])
                print('Aplicante.',applicant)
                applicant.write({'resend_complement':True})
                #template.send_mail(self.id, email_values={'email_to': email_from},force_send=True)
                print('Correo electrónico enviado correctamente.')
            except Exception as e:
                print("Error complement send:", e)
        else:
            print(
                'Falta el template o la dirección de correo electrónico.')

    def sendEmailSelected(self):
        print("seleccionado")
        template = self.templateMail
        email_from = self.email_from
        #Cambiar status una vez enviado correo
        applicant_id = self._context.get('applicant_id')
        applicant = self.env['hr.applicant'].search([('id', '=', applicant_id)])
        applicant.write({'stage_id': 6})
        if template and email_from:
            print("template ", template)
            try:
                template.send_mail(self.id, email_values={'email_to': email_from},force_send=True)
                print('Correo electrónico enviado.')
            except Exception as e:
                print("Error:", e)

    def cancelEmail(self):
        print('cancel')

    def cancelInterview(self):
        print('cancel')
    def send_interview(self):
        # cambiar status del applicant a “Primera entrevista”, enviar correo y crear "Actividades pendientes"
        applicant_id = self._context.get('applicant_id')
        applicant = self.env['hr.applicant'].search([('id', '=', applicant_id)])
        activity = self.env['mail.activity.type'].search([('name', '=', 'Actividades pendientes')])
        applicant.write({'stage_id': 3})
        template_id = self.env.ref('reclutamiento__kuale.mail_template_interview').id
        template = self.env['mail.template'].browse(template_id)
        email_from = applicant.email_from
        if template and email_from:
            try:
                emails = template.email_to
                email_list = emails.split(',')
                email_list.append(email_from)
                for email in email_list:
                    template.send_mail(applicant.id, email_values={'email_to': email}, force_send=True)
                    print('Correo inteview enviado.', email)
                for interviewer in applicant.interviewer_ids:
                    print("interviewers",interviewer)
                    try:
                        res_m= self.env['ir.model']._get_id('hr.applicant')
                        print("res_model",res_m)
                        activity_s = self.env['mail.activity'].sudo().create({
                            'res_model_id': res_m,
                            'res_id': applicant.id,
                            'activity_type_id': activity.id,
                            'user_id': interviewer.id,
                            'res_model': 'hr.applicant',
                            'res_name': applicant.name,
                            'summary': 'Programar entrevista',
                            'date_deadline': self.scheduled_date,
                        })
                        schedule= self.env['mail.activity.schedule'].sudo().create({
                            'res_model_id': res_m,
                            'plan_on_demand_user_id':interviewer.id,
                            'activity_type_id': activity.id,
                            'activity_user_id': interviewer.id,
                            'res_model': 'hr.applicant',
                            'summary': 'Programar entrevista 1',
                            'date_deadline': self.scheduled_date,
                            'res_ids': applicant.id,
                        })
                        if activity_s:
                            bus = self.env['bus.bus'].sudo()._sendmany([(activity_s.user_id.partner_id, 'mail.activity/updated', {'activity_created': True})])
                    except Exception as e:
                        print("Error schedule:", e)
            except Exception as e:
                print("Error interview:", e)
