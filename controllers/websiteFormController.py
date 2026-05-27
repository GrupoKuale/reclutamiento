import base64
import json
from markupsafe import Markup
from odoo import http, SUPERUSER_ID, _, _lt
from odoo.http import request
from psycopg2 import IntegrityError
from odoo.tools import plaintext2html
from odoo.addons.base.models.ir_qweb_fields import nl2br, nl2br_enclose
from werkzeug.exceptions import BadRequest
from odoo.exceptions import AccessDenied, ValidationError, UserError
from odoo.tools.misc import hmac, consteq
import re


class WebsiteForm(http.Controller):

    @http.route('/website/form3/<string:model_name>', type='http', auth="public", methods=['POST'], website=True,
                csrf=False)
    def website_form(self, model_name, **kwargs):
        print("website")
        csrf_token = request.params.pop('csrf_token', None)
        if request.session.uid and not request.validate_csrf(csrf_token):
            raise BadRequest('Session expired (invalid CSRF token)')
        try:
            with request.env.cr.savepoint():
                if request.env['ir.http']._verify_request_recaptcha_token('website_form'):
                    kwargs = dict(request.params)
                    kwargs.pop('model_name')
                    return self._handle_website_form(model_name, **kwargs)
            error = _("Suspicious activity detected by Google reCaptcha.")
        except (ValidationError, UserError) as e:
            error = e.args[0]
        return json.dumps({'error': error})

    def _handle_website_form(self, model_name, **kwargs):
            model_record = request.env['ir.model'].sudo().search(
                [('model', '=', model_name), ('website_form_access', '=', True)])
            if not model_record:
                return json.dumps({'error': _("The form's specified model does not exist")})
            requisition_ids = kwargs.get('requisition_id', '').split(',')
            for req_id in requisition_ids:
                req_id = req_id.strip()
                try:
                    applicant_id = 0
                    if not req_id:
                        applicant_id = kwargs.get('status_stage_id')
                    data = self.extract_data(model_record, kwargs, req_id, applicant_id)
                except ValidationError as e:
                    return json.dumps({'error_fields': e.args[0]})

                try:
                    # Pasar knowledge e idiomas extraídos al insert_record vía kwargs
                    kwargs['knowledge_items'] = data.get('knowledge_items', {})
                    kwargs['language_items']  = data.get('language_items',  {})

                    id_record = self.insert_record(request, model_record, data['record'], data['custom'], req_id,
                                                applicant_id, data['experiences'], data['studies'], data['schedule'],
                                                kwargs, data.get('meta'))
                    if id_record:
                        self.insert_attachment(model_record, id_record, data['attachments'])
                except IntegrityError:
                    return json.dumps(False)

            request.session['form_builder_model_model'] = model_record.model
            request.session['form_builder_model'] = model_record.name
            request.session['form_builder_id'] = id_record
            return json.dumps({'id': id_record})

    # -------------------------------------------------------------------------
    # PRE-SANITIZACIÓN: limpia valores con comas duplicadas ANTES de todo
    # -------------------------------------------------------------------------
    def _presanitize_values(self, model_name, values):
        """
        Recorre TODOS los valores del formulario y, para campos cuyo tipo real
        en el modelo es integer, float, monetary o selection, toma el primer
        valor cuando vienen separados por coma (efecto de dos inputs con mismo name).
        Se ejecuta ANTES del loop principal de extract_data para que ninguna
        rama pueda recibir el valor sucio.
        """
        model_fields = request.env[model_name]._fields
        clean = {}
        for k, v in values.items():
            # No tocar archivos ni valores que ya no son string
            if hasattr(v, 'filename') or not isinstance(v, str) or ',' not in v:
                clean[k] = v
                continue
            field_meta = model_fields.get(k)
            ftype = field_meta.type if field_meta else None

            if ftype in ('integer', 'many2one'):
                first = v.split(',')[0].strip()
                try:
                    clean[k] = str(int(first))
                    print(f"[presanitize {ftype}] {k}: '{v}' -> '{clean[k]}'")
                except (ValueError, TypeError):
                    print(f"[presanitize {ftype} invalido] {k}: '{v}' -> descartado")
            elif ftype in ('float', 'monetary'):
                first = v.split(',')[0].strip()
                try:
                    clean[k] = str(float(first or '0'))
                    print(f"[presanitize float] {k}: '{v}' -> '{clean[k]}'")
                except (ValueError, TypeError):
                    print(f"[presanitize float invalido] {k}: '{v}' -> descartado")
            elif ftype == 'selection':
                clean[k] = v.split(',')[0].strip()
                print(f"[presanitize selection] {k}: '{v}' -> '{clean[k]}'")
            else:
                clean[k] = v
        return clean

    # -------------------------------------------------------------------------
    # extract_data
    # -------------------------------------------------------------------------
    def extract_data(self, model, values, requisition_id, applicant_id):
            dest_model = request.env[model.sudo().model]

            values = self._presanitize_values(model.sudo().model, values)

            data = {
                'record': {},
                'attachments': [],
                'custom': '',
                'meta': '',
                'experiences': [],
                'studies': [],
                'schedule': [],
                'knowledge_items': {},
                'language_items':  {},
            }
            error_fields = []
            custom_fields = []
            try:
                authorized_fields = model.with_user(SUPERUSER_ID)._get_form_writable_fields()
            except Exception as e:
                print("Error al obtener authorized_fields:", e)
                authorized_fields = {}

            for _m2m in ('competencies_ids', 'ability_ids', 'identification_options_ids'):
                authorized_fields.pop(_m2m, None)

            bank_comp = False
            account1 = {}
            account2 = {}
            beneficiaries = {}

            data_card1 = ["account_number", "interbank_clabe", "bank", "payroll_card_number"]
            data_card2 = ["account_number2", "interbank_clabe2", "bank2", "payroll_card_number2"]
            data_beneficiary_prefixes = ["beneficiary_name", "beneficiary_relationship", "other_relationship",
                                        "beneficiary_percentage"]
            data_experience_prefixes = ["companyE", "cityE", "periodEIn", "periodEOut", "positionE", "salaryE",
                                        "supervisorE", "referenceE", "referencePhoneE", "reasonE", "functionsE",
                                        "currently"]
            other_studies_prefixes = ["name_study", "school_studies", "has_document", "document_type"]
            experiences = {}
            studies = {}
            knowledge_items = {}
            language_items  = {}
            schedule = {
                'monday':    {'time_start': None, 'time_end': None},
                'tuesday':   {'time_start': None, 'time_end': None},
                'wednesday': {'time_start': None, 'time_end': None},
                'thursday':  {'time_start': None, 'time_end': None},
                'friday':    {'time_start': None, 'time_end': None},
                'saturday':  {'time_start': None, 'time_end': None},
                'sunday':    {'time_start': None, 'time_end': None},
            }

            fields_out = [
                "identification_select", "identification_ineSelect",
                "schedule_monday_start",    "schedule_monday_end",
                "schedule_tuesday_start",   "schedule_tuesday_end",
                "schedule_wednesday_start", "schedule_wednesday_end",
                "schedule_thursday_start",  "schedule_thursday_end",
                "schedule_friday_start",    "schedule_friday_end",
                "schedule_saturday_start",  "schedule_saturday_end",
                "schedule_sunday_start",    "schedule_sunday_end",
                "postal_code_ids", "adress_options", "options_states",
                "options_municipality", "options_colony",
                "currently", "has_document",
                "competencies_required_check", "abilities_required_check",
                "experience_filled", "schedule_filled",
                "competencies_ids",
                "ability_ids",
                "identification_options_ids",
            ]

            field_mapping = {
                'about_vacancy_value':       'about_vacancy',
                'previous_experience_value': 'previous_experience',
                'lives_with_value':          'lives_with',
                'children_value':            'children',
                'has_experience_value':      'has_experience',
            }

            for field_name, field_value in values.items():

                if hasattr(field_value, 'filename'):
                    field_name = field_name.split('[', 1)[0]
                    if field_name in authorized_fields and authorized_fields[field_name]['type'] == 'binary':
                        data['record'][field_name] = base64.b64encode(field_value.read())
                        field_value.stream.seek(0)
                        if authorized_fields[field_name]['manual'] and field_name + "_filename" in dest_model:
                            data['record'][field_name + "_filename"] = field_value.filename
                    else:
                        field_value.field_name = field_name
                        data['attachments'].append(field_value)

                elif field_name in authorized_fields:
                    try:
                        if field_name == 'requisition_id' and requisition_id:
                            data['record'][field_name] = int(requisition_id)
                        else:
                            input_filter = self._input_filters[authorized_fields[field_name]['type']]
                            data['record'][field_name] = input_filter(self, field_name, field_value)
                        job = request.env.context.get('job')
                        if job:
                            data['record']['job_id'] = job.id
                    except ValueError:
                        error_fields.append(field_name)

                    if dest_model._name == 'mail.mail' and field_name == 'email_from':
                        custom_fields.append((_('email'), field_value))

                elif field_name not in ('context', 'website_form_signature'):
                    try:
                        if field_name == 'requisition_id' and requisition_id:
                            data['record']['requisition_id'] = requisition_id

                        elif field_name == 'status_stage_id':
                            pass

                        elif field_name in field_mapping:
                            if field_value:
                                mapped_field = field_mapping[field_name]
                                if mapped_field == 'children':
                                    data['record'][mapped_field] = (field_value == 'true')
                                else:
                                    data['record'][mapped_field] = field_value

                        elif field_name.startswith('competencies_ids_') and field_value:
                            if 'competencies_ids' not in data['record']:
                                data['record']['competencies_ids'] = []
                            data['record']['competencies_ids'].append(int(field_value))

                        elif field_name.startswith('ability_ids_') and field_value:
                            if 'ability_ids' not in data['record']:
                                data['record']['ability_ids'] = []
                            data['record']['ability_ids'].append(int(field_value))

                        # ── Conocimientos ──────────────────────────────────────────
                        elif field_name.startswith('knowledge_applicant_') and field_value:
                            idx = field_name.replace('knowledge_applicant_', '')
                            if idx not in knowledge_items:
                                knowledge_items[idx] = {}
                            knowledge_items[idx]['name'] = field_value

                        elif field_name.startswith('knowledge_type_') and field_value:
                            idx = field_name.replace('knowledge_type_', '')
                            if idx not in knowledge_items:
                                knowledge_items[idx] = {}
                            knowledge_items[idx]['tipo'] = field_value

                        # ── Idiomas ────────────────────────────────────────────────
                        elif field_name.startswith('language_id_') and field_value:
                            idx = field_name.replace('language_id_', '')
                            if idx not in language_items:
                                language_items[idx] = {}
                            language_items[idx]['language_id'] = int(field_value)

                        elif field_name.startswith('level_id_') and field_value:
                            idx = field_name.replace('level_id_', '')
                            if idx not in language_items:
                                language_items[idx] = {}
                            language_items[idx]['level_id'] = int(field_value)

                        elif field_name == 'clothing_size' and applicant_id != 0:
                            try:
                                product_ids = field_value.split(',')
                                product_list = []
                                applicant = request.env['hr.applicant'].sudo().search(
                                    [('id', '=', applicant_id)], limit=1)
                                for product_id in product_ids:
                                    product = product_id.split(':')
                                    new_product = request.env['hr.applicant.product'].with_user(
                                        SUPERUSER_ID).with_context(mail_create_nosubscribe=True).create({
                                        'applicant_id':        applicant_id,
                                        'product_id':          int(product[1]),
                                        'quantity':            1,
                                        'product_template_id': int(product[0]),
                                        'job_id':              applicant.job_id.id
                                    })
                                    product_list.append(new_product.id)
                                data['record']['clothing_size'] = [(6, 0, product_list)]
                            except Exception as e:
                                print("Error en clothing:", e)

                        elif field_name == 'state_birth_Select' and field_value:
                            city_record = request.env['reclutamiento__kuale.city'].sudo().search([
                                ('state', 'ilike', field_value)
                            ], limit=1, order='id asc')
                            if city_record:
                                data['record']['state_birth_Select'] = city_record.id
                                print(f"[state_birth_Select] '{field_value}' -> id {city_record.id} ({city_record.state})")
                            else:
                                print(f"[state_birth_Select] no encontrado: '{field_value}'")

                        elif field_name == 'birthplace_select' and field_value:
                            state_val = values.get('state_birth_Select', '')
                            domain = [('municipality', 'ilike', field_value)]
                            if state_val:
                                domain.append(('state', 'ilike', state_val))
                            city_record = request.env['reclutamiento__kuale.city'].sudo().search(
                                domain, limit=1, order='id asc'
                            )
                            if city_record:
                                data['record']['birthplace_select'] = city_record.id
                                print(f"[birthplace_select] '{field_value}' -> id {city_record.id} ({city_record.municipality})")
                            else:
                                print(f"[birthplace_select] no encontrado: '{field_value}'")

                        elif field_name in data_card1 and field_value:
                            bank_comp = True
                            account1[field_name] = field_value

                        elif field_name in data_card2 and field_value:
                            account2[field_name[:-1]] = field_value

                        else:
                            prefix = field_name[:-1]
                            index  = field_name[-1]

                            if prefix in data_beneficiary_prefixes:
                                if index not in beneficiaries:
                                    beneficiaries[index] = {}
                                if field_value:
                                    beneficiaries[index][prefix] = field_value

                            elif prefix in data_experience_prefixes:
                                if index not in experiences:
                                    experiences[index] = {}
                                if field_value:
                                    experiences[index][prefix] = field_value

                            elif prefix in other_studies_prefixes:
                                if index not in studies:
                                    studies[index] = {}
                                if field_value:
                                    studies[index][prefix] = field_value

                            elif field_name not in fields_out:
                                valid_model_fields = set(dest_model._fields.keys())
                                if field_name in valid_model_fields:
                                    data['record'][field_name] = field_value
                                else:
                                    print(f"Campo ignorado (no en modelo): {field_name}")

                        if field_name.startswith("schedule"):
                            schedule = self.process_schedule(field_name, field_value, schedule)

                        if field_name == 'identification_options_ids' and field_value:
                            ids = [int(x) for x in field_value.split(',') if x.strip()]
                            data['record']['identification_options_ids'] = [(6, 0, ids)]

                        if field_name == 'competencies_ids' and field_value:
                            ids = [int(x) for x in field_value.split(',') if x.strip()]
                            data['record']['competencies_ids'] = [(6, 0, ids)]

                        if field_name == 'ability_ids' and field_value:
                            ids = [int(x) for x in field_value.split(',') if x.strip()]
                            data['record']['ability_ids'] = [(6, 0, ids)]

                    except Exception as e:
                        print("Error en ciclo for:", e)

            if schedule:
                data['schedule'] = schedule

            if knowledge_items:
                data['knowledge_items'] = knowledge_items

            if language_items:
                data['language_items'] = language_items

            if bank_comp:
                bank_list = []
                account1['applicant_id'] = applicant_id
                account1_create = request.env['bank.account'].with_user(SUPERUSER_ID).with_context(
                    mail_create_nosubscribe=True).create(account1)
                bank_list.append(account1_create.id)
                if account2:
                    account2['applicant_id'] = applicant_id
                    account2_create = request.env['bank.account'].with_user(SUPERUSER_ID).with_context(
                        mail_create_nosubscribe=True).create(account2)
                    bank_list.append(account2_create.id)
                data['record']['bank_account_ids'] = [(6, 0, bank_list)]
                array_beneficiaries = [b for _, b in sorted(beneficiaries.items())]
                data_list = []
                for beneficiary in array_beneficiaries:
                    beneficiary['applicant_id'] = applicant_id
                    data_create = request.env['hr.applicant.beneficiary'].with_user(SUPERUSER_ID).with_context(
                        mail_create_nosubscribe=True).create(beneficiary)
                    data_list.append(data_create.id)
                data['record']['beneficiaries_ids'] = [(6, 0, data_list)]

            data['custom'] = "\n".join([u"%s : %s" % v for v in custom_fields])

            if requisition_id:
                data['experiences'] = experiences
                data['studies'] = studies

            if request.env['ir.config_parameter'].sudo().get_param('website_form_enable_metadata'):
                environ = request.httprequest.headers.environ
                data['meta'] += "%s : %s\n%s : %s\n%s : %s\n%s : %s\n" % (
                    "IP",              environ.get("REMOTE_ADDR"),
                    "USER_AGENT",      environ.get("HTTP_USER_AGENT"),
                    "ACCEPT_LANGUAGE", environ.get("HTTP_ACCEPT_LANGUAGE"),
                    "REFERER",         environ.get("HTTP_REFERER")
                )

            if hasattr(dest_model, "website_form_input_filter"):
                data['record'] = dest_model.website_form_input_filter(request, data['record'])

            missing_required_fields = [label for label, field in authorized_fields.items()
                                    if field['required'] and label not in data['record']]
            if any(error_fields):
                raise ValidationError(error_fields + missing_required_fields)
            
            # Convertir listas acumuladas al formato ORM Many2many
            if isinstance(data['record'].get('competencies_ids'), list):
                data['record']['competencies_ids'] = [(6, 0, data['record']['competencies_ids'])]

            if isinstance(data['record'].get('ability_ids'), list):
                data['record']['ability_ids'] = [(6, 0, data['record']['ability_ids'])]

            return data

    # -------------------------------------------------------------------------
    # insert_record
    # -------------------------------------------------------------------------
    def insert_record(self, request, model, values, custom, req_id, applicant_id, experiences, studies, schedule,
                        kwargs, meta=None):
            model_name = model.sudo().model

            # Barrera 1: eliminar campos inexistentes en el modelo
            model_fields = request.env[model_name]._fields
            valid_model_fields = set(model_fields.keys())
            values = {k: v for k, v in values.items() if k in valid_model_fields}

            # Barrera 2: corregir valores con coma usando tipos REALES del modelo (_fields)
            for fname in list(values.keys()):
                fval = values[fname]
                if not isinstance(fval, str) or ',' not in fval:
                    continue
                fmeta = model_fields.get(fname)
                if not fmeta:
                    continue
                if fmeta.type in ('integer', 'many2one'):
                    try:
                        values[fname] = int(fval.split(',')[0].strip())
                        print(f"[Barrera2 {fmeta.type}] {fname}: '{fval}' -> {values[fname]}")
                    except (ValueError, TypeError):
                        del values[fname]
                        print(f"[Barrera2 {fmeta.type} invalido] {fname}: '{fval}' -> eliminado")
                elif fmeta.type in ('float', 'monetary'):
                    try:
                        values[fname] = float(fval.split(',')[0].strip() or '0')
                        print(f"[Barrera2 float] {fname}: '{fval}' -> {values[fname]}")
                    except (ValueError, TypeError):
                        del values[fname]
                        print(f"[Barrera2 float invalido] {fname}: '{fval}' -> eliminado")
                elif fmeta.type == 'selection':
                    values[fname] = fval.split(',')[0].strip()
                    print(f"[Barrera2 selection] {fname}: '{fval}' -> '{values[fname]}'")

            # Extraer knowledge y language antes de crear el record
            knowledge_items = kwargs.get('knowledge_items', {})
            language_items  = kwargs.get('language_items',  {})

            try:
                if req_id:
                    record = request.env[model_name].with_user(SUPERUSER_ID).with_context(
                        mail_create_nosubscribe=True).create(values)

                    if experiences:
                        array_experiences = [exp for _, exp in sorted(experiences.items())]
                        data_listE = []
                        for experience in array_experiences:
                            experience['applicant_id'] = record.id
                            if 'currently' in experience:
                                experience['currently'] = experience['currently'] == 'on'
                            if 'salaryE' in experience:
                                try:
                                    experience['salaryE'] = int(str(experience['salaryE']).replace(',', '').replace('$', '').strip() or 0)
                                except (ValueError, TypeError):
                                    experience['salaryE'] = 0
                            dataE_create = request.env['hr.applicant.experience'].with_user(SUPERUSER_ID).with_context(
                                mail_create_nosubscribe=True).create(experience)
                            data_listE.append(dataE_create.id)
                        record.write({'experiencies_ids': [(6, 0, data_listE)]})

                    if studies:
                        array_studies = [s for _, s in sorted(studies.items())]
                        data_listS = []
                        for study in array_studies:
                            study['applicant_id'] = record.id
                            dataS_create = request.env['hr.applicant.other_studies'].with_user(SUPERUSER_ID).with_context(
                                mail_create_nosubscribe=True).create(study)
                            data_listS.append(dataS_create.id)
                        record.write({'other_studies_ids': [(6, 0, data_listS)]})

                    if schedule:
                        for day, times in schedule.items():
                            if times['time_start'] and times['time_end']:
                                record_schedule = request.env[
                                    'reclutamiento__kuale.schedule_student'].sudo().create({
                                    'day':        day,
                                    'time_start': times['time_start'],
                                    'time_end':   times['time_end'],
                                })
                                record.write({'schedule_student': [(4, record_schedule.id)]})

                    # ── Conocimientos y Herramientas ───────────────────────────────
                    if knowledge_items:
                        for idx, item in sorted(knowledge_items.items()):
                            if item.get('name'):
                                try:
                                    request.env['reclutamiento__kuale.applicant_knowledge'].with_user(
                                        SUPERUSER_ID).with_context(mail_create_nosubscribe=True).create({
                                        'applicant_id': record.id,
                                        'tipo':         item.get('tipo', 'Conocimiento'),
                                        'name':         item['name'],
                                    })
                                except Exception as e:
                                    print(f"Error al guardar knowledge {idx}:", e)

                    # ── Idiomas ────────────────────────────────────────────────────
                    if language_items:
                        for idx, item in sorted(language_items.items()):
                            if item.get('language_id') and item.get('level_id'):
                                try:
                                    request.env['reclutamiento__kuale.applicant_language'].with_user(
                                        SUPERUSER_ID).with_context(mail_create_nosubscribe=True).create({
                                        'applicant_id': record.id,
                                        'language_id':  item['language_id'],
                                        'level_id':     item['level_id'],
                                    })
                                except Exception as e:
                                    print(f"Error al guardar language {idx}:", e)

                    try:
                        files = {k: v for k, v in kwargs.items()
                                if k.startswith(('identity_document', 'ine_document'))}
                        for index, (key, file) in enumerate(files.items(), start=1):
                            # Verificar que el archivo tenga contenido real
                            content = file.read()
                            if not content:
                                continue
                            binary = base64.b64encode(content)
                            request.env['reclutamiento__kuale.documents_applicant'].sudo().create({
                                'applicant_id': record.id,
                                'doc_data':     binary,
                                'doc_name':     f"DocumentoIdentidad{index}",
                            })
                    except Exception as error:
                        print("Error al guardar documentos:", error)

                    company_name = values.get('company_name')
                    company = request.env['res.company'].sudo().search([('name', '=', company_name)])
                    employees = request.env['hr.employee'].sudo().search(
                        [('company_id', '=', company.id), ('rol_employee_selection', '=', 'lgp')])
                    for user in employees:
                        if user.id:
                            record.message_subscribe([user.id])

                else:
                    if applicant_id:
                        try:
                            record = request.env[model_name].with_user(SUPERUSER_ID).browse(int(applicant_id))
                            clean_values = {}
                            model_fields = request.env[model_name]._fields
                            for k, v in values.items():
                                if k not in model_fields:
                                    continue
                                ftype = model_fields[k].type
                                if ftype == 'boolean':
                                    clean_values[k] = bool(v) if not isinstance(v, bool) else v
                                elif ftype in ('many2one',) and not v:
                                    continue
                                else:
                                    clean_values[k] = v
                            record.with_context(mail_create_nosubscribe=True).write(clean_values)
                            print(f"Complemento actualizado para applicant {applicant_id}: {list(clean_values.keys())}")
                            
                            # ── Guardar cuentas bancarias ──────────────────────────
                            BankAccount = request.env['bank.account'].with_user(SUPERUSER_ID)
                            record.bank_account_ids.unlink()
                            for i in range(1, 3):
                                acc   = kwargs.get(f'account_number{i}', '').strip()
                                clabe = kwargs.get(f'interbank_clabe{i}', '').strip()
                                if acc and clabe:
                                    try:
                                        BankAccount.create({
                                            'applicant_id':       record.id,
                                            'account_number':     acc,
                                            'interbank_clabe':    clabe,
                                            'bank':               kwargs.get(f'bank{i}', 'N/A').strip() or 'N/A',
                                            'payroll_card_number': kwargs.get(f'payroll_card_number{i}', '').strip(),
                                            'account_type':       'nomina',
                                        })
                                    except Exception as e:
                                        print(f"ERROR guardando cuenta {i}:", e)

                            # ── Guardar beneficiarios ──────────────────────────────
                            Beneficiary = request.env['hr.applicant.beneficiary'].with_user(SUPERUSER_ID)
                            record.beneficiaries_ids.unlink()
                            for i in range(1, 5):
                                name = kwargs.get(f'beneficiary_name{i}', '').strip()
                                rel  = kwargs.get(f'beneficiary_relationship{i}', '').strip()
                                pct  = kwargs.get(f'beneficiary_percentage{i}', '').strip()
                                other_rel = kwargs.get(f'other_relationship{i}', '').strip()
                                print(f"DEBUG beneficiario {i}: name='{name}' rel='{rel}' pct='{pct}'")
                                if name and rel:
                                    try:
                                        Beneficiary.create({
                                            'applicant_id': record.id,
                                            'beneficiary_name': name,
                                            'beneficiary_relationship': rel,
                                            'other_relationship': other_rel,
                                            'beneficiary_percentage': pct,
                                        })
                                        print(f"Beneficiario {i} guardado OK")
                                    except Exception as e:
                                        print(f"ERROR guardando beneficiario {i}:", e)

                            # ── Guardar contactos de emergencia ───────────────────────────
                            Emergency = request.env['hr.applicant.emergency'].with_user(SUPERUSER_ID)
                            record.emergency_contacts.unlink()
                            for i in range(1, 6):  # hasta 5 contactos
                                name  = kwargs.get(f'emergency_name{i}', '').strip()
                                rel   = kwargs.get(f'emergency_relationship{i}', '').strip()
                                phone = kwargs.get(f'emergency_phone{i}', '').strip()
                                print(f"DEBUG emergencia {i}: name='{name}' rel='{rel}' phone='{phone}'")
                                if name and rel and phone:
                                    try:
                                        Emergency.create({
                                            'applicant_id': record.id,
                                            'name':         name,
                                            'relationship': rel,
                                            'phone_number': phone,
                                        })
                                        print(f"Contacto emergencia {i} guardado OK")
                                    except Exception as e:
                                        print(f"ERROR guardando contacto emergencia {i}:", e)
                        except Exception as e:
                            print("Error al actualizar complemento:", e)
                            raise
                    else:
                        record = request.env[model_name].with_user(SUPERUSER_ID).with_context(
                            mail_create_nosubscribe=True).create(values)

            except Exception as e:
                print("Error en insert_record:", e)
                raise

            if custom or meta:
                _custom_label = "%s\n___________\n\n" % _("Other Information:")
                if model_name == 'mail.mail':
                    _custom_label = "%s\n___________\n\n" % _("This message has been posted on your website!")
                default_field      = model.website_form_default_field_id
                default_field_data = values.get(default_field.name, '')
                custom_content = (default_field_data + "\n\n" if default_field_data else '') \
                    + (_custom_label + custom + "\n\n" if custom else '') \
                    + (self._meta_label + "\n________\n\n" + meta if meta else '')

                if default_field.name:
                    if default_field.ttype == 'html' or model_name == 'mail.mail':
                        custom_content = nl2br_enclose(custom_content)
                    record.update({default_field.name: custom_content})
                elif hasattr(record, '_message_log'):
                    record._message_log(
                        body=nl2br_enclose(custom_content, 'p'),
                        message_type='comment',
                    )

            return record.id

    # -------------------------------------------------------------------------
    # insert_attachment
    # -------------------------------------------------------------------------
    def insert_attachment(self, model, id_record, files):
        orphan_attachment_ids = []
        model_name = model.sudo().model
        record     = model.env[model_name].browse(id_record)
        authorized_fields = model.with_user(SUPERUSER_ID)._get_form_writable_fields()
        for file in files:
            # Verificar que el archivo tenga contenido real
            content = file.read()
            if not content:
                continue
            file.stream.seek(0)
            
            custom_field = file.field_name not in authorized_fields
            if file.field_name != "identity_document" and file.field_name != "ine_document":
                attachment_value = {
                    'name':        file.filename,
                    'datas':       base64.encodebytes(content),
                    'res_model':   model_name,
                    'res_id':      record.id,
                    'description': file.field_name,   
                }
                attachment_id = request.env['ir.attachment'].sudo().create(attachment_value)
                if attachment_id and not custom_field:
                    record_sudo = record.sudo()
                    value = [(4, attachment_id.id)]
                    if record_sudo._fields[file.field_name].type == 'many2one':
                        value = attachment_id.id
                    record_sudo[file.field_name] = value
                else:
                    orphan_attachment_ids.append(attachment_id.id)

    # -------------------------------------------------------------------------
    # Filtros de entrada
    # -------------------------------------------------------------------------
    _meta_label = _lt("Metadata")

    def identity(self, field_label, field_input):
        return field_input

    def integer(self, field_label, field_input):
        return int(field_input)

    def floating(self, field_label, field_input):
        return float(field_input)

    def html(self, field_label, field_input):
        return plaintext2html(field_input)

    def boolean(self, field_label, field_input):
        return bool(field_input)

    def binary(self, field_label, field_input):
        return base64.b64encode(field_input.read())

    def one2many(self, field_label, field_input):
        return [int(i) for i in field_input.split(',')]

    def many2many(self, field_label, field_input, *args):
        return [(args[0] if args else (6, 0)) + (self.one2many(field_label, field_input),)]

    _input_filters = {
        'char':      identity,
        'text':      identity,
        'html':      html,
        'date':      identity,
        'datetime':  identity,
        'many2one':  integer,
        'one2many':  one2many,
        'many2many': many2many,
        'selection': identity,
        'boolean':   boolean,
        'integer':   integer,
        'float':     floating,
        'binary':    binary,
        'monetary':  floating,
    }

    # -------------------------------------------------------------------------
    # Utilidades
    # -------------------------------------------------------------------------
    def send_job_notification(self, job_id):
        employees = request.env['hr.employee.public'].sudo().search([('job_id', '=', job_id)])
        for user in employees:
            body = "Solicitud de trabajo recibida"
            try:
                mail = request.env['mail.mail'].sudo().create({
                    'email_from':  'santiagovco80@gmail.com',
                    'body_html':   body,
                    'subject':     _('Job applicant!'),
                    'email_to':    user.work_email,
                    'auto_delete': True,
                })
                mail.send()
                u = request.env['res.users'].sudo().browse(user.id)
                request.env['mail.message'].sudo().create({
                    'model':        'res.users',
                    'res_id':       u.id,
                    'subject':      'NOTI',
                    'body':         body,
                    'message_type': 'notification',
                })
            except Exception as e:
                print("Error al enviar notificacion:", e)

    def process_schedule(self, field_name, field_value, schedule):
        days_mapping = {
            'schedule_monday':    'monday',
            'schedule_tuesday':   'tuesday',
            'schedule_wednesday': 'wednesday',
            'schedule_thursday':  'thursday',
            'schedule_friday':    'friday',
            'schedule_saturday':  'saturday',
            'schedule_sunday':    'sunday',
        }
        for day_field, day_name in days_mapping.items():
            if field_name == f'{day_field}_start' and field_value:
                schedule[day_name]['time_start'] = field_value
            if field_name == f'{day_field}_end' and field_value:
                schedule[day_name]['time_end'] = field_value
        return schedule