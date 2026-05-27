# -*- coding: latin-1 -*-
from odoo import http, fields
from odoo.addons.website.controllers.main import Website
from odoo.http import request
from odoo.tools.misc import groupby
from odoo.osv.expression import AND
from datetime import datetime, timedelta
import random
import string

from werkzeug.exceptions import BadRequest
from werkzeug.urls import url_encode
from odoo.exceptions import AccessDenied, ValidationError, UserError

KUALE_VERIFY_KEY = '_kuale_verify'
KUALE_CODE_TTL   = 5

COMPANY_ALIASES = {
    "Carl's": "Carl's Jr.", 
    'Hamburguesas Mafis S.A. de C.V.': "Carl's Jr.",
    'Helados Mafis SA de CV': 'Dairy Queen',
    'Proyectos Sifam S.A. de C.V.': 'Tintocinco',
    'MFDA y Copropietarios': 'MFDA',
    'Inmobiliaria Erben': 'Inmobiliaria Erben',
    'Hidrol�gica Kuale S.A. de C.V.': 'Hidrol�gica',
    'Tintocinco S.A. de C.V.': 'Tintocinco',
    'Gente Kuale S.A. de C.V.': 'Gente Kuale',
    'Servicios Kuale S.A. de C.V.': 'Servicios Kuale',
    'Publipuentes Tamaulipas S.A. de C.V.': 'Publipuentes',
    'Mister Motor S.A. de C.V.': 'Mister Motor',
    'Plaza Faja de Oro': 'Plaza Faja de Oro',
    'Plaza Universidad Express': 'Plaza Universidad Express',
    'Offshore de M�xico S.A. de C.V.': 'Offshore',
    'Productora del Golfo S.A. de C.V.': 'Productora del Golfo',
    'Comercial Kuale S.A. de C.V.': 'Comercial Kuale',
    'Kuale S. de R.L. de C.V.': 'Kuale',
}

COMPANY_STATE = {
    'Hidrol�gica Kuale S.A. de C.V.': 'Quer�taro y Tamaulipas',
}
DEFAULT_STATE = 'Tamaulipas'

class CustomWebsite(Website):
    _jobs_per_page = 12

    def _redirect_to_recruitment_if_needed(self):
        recruitment_website = request.env.ref('reclutamiento__kuale.website_reclutamiento', raise_if_not_found=False)
        if recruitment_website:
            recruitment_website = recruitment_website.sudo()
        if not recruitment_website:
            return False
        if request.website.id == recruitment_website.id:
            return False

        recruitment_website._force()
        path = request.httprequest.path or '/'
        query = request.httprequest.query_string.decode()
        target = f'{path}?{query}' if query else path
        return request.redirect(target)

    @staticmethod
    def _redirect_to_jobs():
        query = request.httprequest.query_string.decode()
        target = '/jobs'
        if query:
            target = f'{target}?{query}'
        return request.redirect(target)

    @staticmethod
    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _job_city_name(job):
        if job.address_id and job.address_id.city:
            return (job.address_id.city or '').strip()
        if job.city_Job and job.city_Job.city:
            return (job.city_Job.city or '').strip()
        return 'N/A'

    @staticmethod
    def _company_scope_ids(env, company_id):
        company = env['res.company'].sudo().browse(company_id)
        if not company.exists():
            return []
        company_ids = env['res.company'].sudo().search([('id', 'child_of', company.id)]).ids
        if company.parent_id:
            company_ids.append(company.parent_id.id)
        return list(set(company_ids))

    def sitemap_jobs(env, rule, qs):
        if not qs or qs.lower() in '/jobs':
            yield {'loc': '/jobs'}

    @http.route(['/test'], type='http', auth="public", website=True)
    def test(self, **kwargs):
        return "Mensaje de prueba desde el controlador"

    @http.route(['/vacancy'], type='http', auth="public", website=True)
    def vacancy(self, **kwargs):
        switch_response = self._redirect_to_recruitment_if_needed()
        if switch_response:
            return switch_response
        return self._redirect_to_jobs()

    @http.route(['/vacantes'], type='http', auth="public", website=True)
    def vacantes(self, **kwargs):
        switch_response = self._redirect_to_recruitment_if_needed()
        if switch_response:
            return switch_response
        return self._redirect_to_jobs()

    @http.route([
        '/jobs/company',
        '/jobs/company/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=sitemap_jobs)
    def jobs_extended(self, country_id=None, department_id=None, office_id=None, contract_type_id=None,
                      is_remote=False, is_other_department=False, is_untyped=None, page=1, search=None,
                      company_id=None, **kwargs):
        return self.jobs(
            country_id=country_id,
            department_id=department_id,
            office_id=office_id,
            contract_type_id=contract_type_id,
            is_remote=is_remote,
            is_other_department=is_other_department,
            is_untyped=is_untyped,
            page=page,
            search=search,
            company_id=company_id,
            **kwargs,
        )

    @http.route([
        '/jobs',
        '/jobs/<int:company_id>',
        '/jobs/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=sitemap_jobs)
    def jobs(self, country_id=None, department_id=None, office_id=None, contract_type_id=None,
            is_remote=False, is_other_department=False, is_untyped=None, page=1, search=None, company_id=None, **kwargs):
        switch_response = self._redirect_to_recruitment_if_needed()
        if switch_response:
            return switch_response

        env = request.env(context=dict(request.env.context, show_address=True, no_tag_br=True))
        Country = env['res.country'].sudo()
        Jobs = env['hr.job'].sudo()
        Department = env['hr.department'].sudo()

        country = Country.browse(int(country_id)) if country_id else None
        department = Department.browse(int(department_id)) if department_id else None
        office_id = int(office_id) if office_id else None
        contract_type_id = int(contract_type_id) if contract_type_id else None
        company_id = self._to_int(company_id)

        table_company_id = self._to_int(kwargs.get('table_company_id'))
        table_city = (kwargs.get('table_city') or '').strip()

        if not (country or department or office_id or contract_type_id or kwargs.get('all_countries')):
            if request.geoip.country_code:
                countries_ = Country.search([('code', '=', request.geoip.country_code)])
                country = countries_[0] if countries_ else None
                if country:
                    country_count = Jobs.search_count(AND([
                        request.website.website_domain(),
                        [('address_id.country_id', '=', country.id)]
                    ]))
                    if not country_count:
                        country = False

        options = {
            'displayDescription': True,
            'allowFuzzy': not request.params.get('noFuzzy'),
            'country_id': country.id if country else None,
            'department_id': department.id if department else None,
            'office_id': office_id,
            'contract_type_id': contract_type_id,
            'is_remote': is_remote,
            'is_other_department': is_other_department,
            'is_untyped': is_untyped,
        }

        all_company_ids = request.env['res.company'].sudo().search([]).ids
        website_ctx = request.website.with_context(allowed_company_ids=all_company_ids).sudo()
        total, details, fuzzy_search_term = website_ctx._search_with_fuzzy(
            "jobs",
            search,
            limit=1000,
            order="is_published desc, sequence, no_of_recruitment desc",
            options=options,
        )

        jobs = details[0].get('results', Jobs).sudo()

        if company_id:
            company_ids = self._company_scope_ids(env, company_id)
            if company_ids:
                company_ids_set = set(company_ids)
                jobs = jobs.filtered(lambda job: job.company_id.id in company_ids_set)
            else:
                jobs = jobs.browse()

        table_company_options = jobs.mapped('company_id').sorted(key=lambda c: (c.name or '').lower())
        table_city_options = sorted({
            self._job_city_name(job)
            for job in jobs
            if self._job_city_name(job) != 'N/A'
        })

        if table_company_id:
            jobs = jobs.filtered(lambda job: job.company_id.id == table_company_id)
        if table_city:
            table_city_norm = table_city.lower()
            jobs = jobs.filtered(lambda job: self._job_city_name(job).lower() == table_city_norm)

        def sort(records_list, field_name):
            return sorted(
                records_list,
                key=lambda item: (item is None, item and item.sudo()[field_name] if item and item.sudo()[field_name] else ''),
            )

        jobs = jobs.filtered(lambda job: job.website_published and job.from_requisition and job.branch_company_id)
        total = len(jobs)

        country_offices = set(j.address_id or None for j in jobs)
        countries = sort(set(o and o.country_id or None for o in country_offices), 'name')
        count_per_country = {'all': total}
        for c, jobs_list in groupby(jobs, lambda job: job.address_id.country_id):
            count_per_country[c] = len(jobs_list)
        count_remote = len(jobs.filtered(lambda job: not job.address_id))
        if count_remote:
            count_per_country[None] = count_remote

        departments = sort(set(j.department_id or None for j in jobs), 'name')
        count_per_department = {'all': total}
        for d, jobs_list in groupby(jobs, lambda job: job.department_id):
            count_per_department[d] = len(jobs_list)
        count_other_department = len(jobs.filtered(lambda job: not job.department_id))
        if count_other_department:
            count_per_department[None] = count_other_department

        offices = sort(set(j.address_id or None for j in jobs), 'city')
        count_per_office = {'all': total}
        for o, jobs_list in groupby(jobs, lambda job: job.address_id):
            count_per_office[o] = len(jobs_list)
        count_remote = len(jobs.filtered(lambda job: not job.address_id))
        if count_remote:
            count_per_office[None] = count_remote

        employment_types = sort(set(j.contract_type_id for j in jobs if j.contract_type_id), 'name')
        count_per_employment_type = {'all': total}
        for t, jobs_list in groupby(jobs, lambda job: job.contract_type_id):
            count_per_employment_type[t] = len(jobs_list)
        count_untyped = len(jobs.filtered(lambda job: not job.contract_type_id))
        if count_untyped:
            count_per_employment_type[None] = count_untyped

        pager = request.website.pager(
            url=request.httprequest.path.partition('/page/')[0],
            url_args=request.httprequest.args,
            total=total,
            page=page,
            step=self._jobs_per_page,
        )
        offset = pager['offset']
        jobs = jobs[offset:offset + self._jobs_per_page]

        # -- Construir job_groups agrupando por nombre de puesto --
        published_jobs = jobs.filtered(lambda j: j.website_published)
        job_groups = {}
        for job in published_jobs:
            gkey = job.name
            if gkey not in job_groups:
                group_jobs = published_jobs.filtered(lambda j, _job=job: j.name == _job.name)
                group_total = sum(group_jobs.mapped('no_of_recruitment'))

                city_map = {}
                for gjob in group_jobs:
                    # Ciudad directamente del job hijo
                    city = (
                        (gjob.address_id.city if gjob.address_id and gjob.address_id.city else None) or
                        (gjob.city_Job.city if gjob.city_Job and gjob.city_Job.city else None) or
                        'N/A'
                    )
                    if city not in city_map:
                        city_map[city] = []

                    # Empresa para el alias
                    company_raw = gjob.company_id.name or ''
                    if gjob.company_id.parent_id:
                        company_raw = gjob.company_id.parent_id.name or company_raw
                    company_display = COMPANY_ALIASES.get(company_raw, company_raw)

                    # Verificar que este job hijo tenga requisici�n autorizada
                    has_authorized_req = gjob.requisition_ids.filtered(
                        lambda r: r.status == 30
                    )

                    # Sucursal = directamente el company_id del job hijo
                    if gjob.company_id and gjob.company_id.parent_id and has_authorized_req:
                        branch_name = gjob.company_id.name
                    else:
                        branch_name = None

                    already = any(e['name'] == branch_name for e in city_map[city])
                    if not already:
                        city_map[city].append({
                            'name':    branch_name,
                            'company': company_display,
                            'count':   gjob.no_of_recruitment,
                        })

                # -- Bolsa de trabajo --
                has_bolsa = any(gjob.bolsa_trabajo for gjob in group_jobs)
                bolsa_city_map = {}
                for bjob in group_jobs.filtered(lambda j: j.bolsa_trabajo and j.website_published):
                    if bjob.company_id and bjob.company_id.parent_id:
                        city = (
                            (bjob.address_id.city if bjob.address_id and bjob.address_id.city else None) or
                            (bjob.city_Job.city if bjob.city_Job and bjob.city_Job.city else None) or
                            'N/A'
                        )
                        if city not in bolsa_city_map:
                            bolsa_city_map[city] = []
                        req = bjob.requisition_ids.filtered(lambda r: r.status == 30)
                        company_display = COMPANY_ALIASES.get(
                            bjob.company_id.parent_id.name,
                            bjob.company_id.parent_id.name
                        )
                        already = any(e['name'] == bjob.company_id.name for e in bolsa_city_map[city])
                        if not already:
                            bolsa_city_map[city].append({
                                'name':    bjob.company_id.name,
                                'company': company_display,
                                'job_id':  bjob.id,
                                'req_id':  req[:1].id if req else 0,
                            })

                job_groups[gkey] = {
                    'job':            job,
                    'group_jobs':     group_jobs,
                    'total':          group_total,
                    'city_map':       city_map,
                    'has_bolsa':      has_bolsa,
                    'bolsa_city_map': bolsa_city_map,
                }
        # -- FIN job_groups --

        office = env['res.partner'].sudo().browse(int(office_id)) if office_id else None
        contract_type = env['hr.contract.type'].sudo().browse(int(contract_type_id)) if contract_type_id else None

        clear_args = {}
        for arg_name in (
            'search', 'country_id', 'department_id', 'office_id',
            'contract_type_id', 'is_remote', 'is_other_department',
            'is_untyped', 'all_countries', 'all_departments', 'all_employment_types',
        ):
            value = request.params.get(arg_name)
            if value:
                clear_args[arg_name] = value
        base_jobs_url = request.httprequest.path.partition('/page/')[0]
        table_filters_clear_url = base_jobs_url
        if clear_args:
            table_filters_clear_url = f"{base_jobs_url}?{url_encode(clear_args)}"

        return request.render("reclutamiento__kuale.extend_index", {
            'jobs': jobs,
            'countries': countries,
            'departments': departments,
            'offices': offices,
            'employment_types': employment_types,
            'country_id': country,
            'department_id': department,
            'office_id': office,
            'contract_type_id': contract_type,
            'is_remote': is_remote,
            'is_other_department': is_other_department,
            'is_untyped': is_untyped,
            'pager': pager,
            'search': fuzzy_search_term or search,
            'search_count': total,
            'original_search': fuzzy_search_term and search,
            'count_per_country': count_per_country,
            'count_per_department': count_per_department,
            'count_per_office': count_per_office,
            'count_per_employment_type': count_per_employment_type,
            'table_company_options': table_company_options,
            'table_city_options': table_city_options,
            'table_company_id': table_company_id,
            'table_city': table_city,
            'table_filters_clear_url': table_filters_clear_url,
            'no_fuzzy': request.params.get('noFuzzy'),
            'job_groups': job_groups,
        })
    
    @http.route('''/jobs/<string:job>/<int:job_id>''', type='http', auth="public", website=True, sitemap=True)
    def job(self, job, job_id, **kwargs):
        switch_response = self._redirect_to_recruitment_if_needed()
        if switch_response:
            return switch_response

        job = request.env['hr.job'].sudo().browse(job_id)

        # La empresa padre es company_id, si tiene parent_id subimos un nivel
        parent_company = job.company_id
        if parent_company.parent_id:
            parent_company = parent_company.parent_id

        company_name = parent_company.name or ''
        company_alias = COMPANY_ALIASES.get(company_name, company_name)
        company_state = COMPANY_STATE.get(company_name, DEFAULT_STATE)

        return request.render("website_hr_recruitment.detail", {
            'job': job,
            'main_object': job,
            'company_alias': company_alias,
            'company_state': company_state,
        })

    @http.route('/jobs/apply2/<int:job_id>', type='http', auth="public", website=True, sitemap=True)
    def jobs_apply1(self, job_id, **kwargs):
        switch_response = self._redirect_to_recruitment_if_needed()
        if switch_response:
            return switch_response
        error = {}
        default = {}
        env = request.env
        job = env['hr.job'].sudo().browse(job_id)
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')
        applicant = env['hr.applicant'].sudo()
        marital_status = applicant.fields_get(['marital_status'])['marital_status']['selection']
        type_road = applicant.fields_get(['type_road'])['type_road']['selection']
        about_vacancy_options = applicant.fields_get(['about_vacancy'])['about_vacancy']['selection']
        gender_options = applicant.fields_get(['gender'])['gender']['selection']
        companyName = job.company_id.name or ''
        identity_options = env['reclutamiento__kuale.identification_option'].sudo().search([])
        identification_option = [(option.id, option.name) for option in identity_options]
        schoolarship = env['reclutamiento__kuale.schooling'].sudo().search([])
        schoolarship_options = [(option.id, option.name) for option in schoolarship]
        knowledge = env['reclutamiento__kuale.knowledge_experience'].sudo().search([])
        knowledge_experience_options = [(option.id, option.name) for option in knowledge]
        language = env['reclutamiento__kuale.language'].sudo().search([])
        language_options = [(option.id, option.name) for option in language]
        language_level = env['reclutamiento__kuale.language_level'].sudo().search([])
        level_options = [(option.id, option.name) for option in language_level]
        competences = env['reclutamiento__kuale.competencies'].sudo().search([])
        competences_options = [(option.id, option.name) for option in competences]
        abilities = env['hr.skill.type'].sudo().search([])
        abilities_options = [(option.id, option.name) for option in abilities]

        # -- Sucursales publicadas del mismo puesto --
        parent_id = job.branch_company_id.id if job.branch_company_id else job.company_id.id
        sibling_jobs = env['hr.job'].sudo().search([
            ('name', '=', job.name),
            ('branch_company_id', '=', parent_id),
            ('website_published', '=', True),
            ('from_requisition', '=', True),
        ])

        # Mapeo job_id ? requisition_id m�s reciente con status=30
        sibling_req_map = {}
        for sjob in sibling_jobs:
            req = env['reclutamiento__kuale.requisitions'].sudo().search([
                ('branch_ids', '=', sjob.company_id.id),
                ('status', '=', 30),
            ], order='id desc', limit=1)
            sibling_req_map[sjob.id] = req.id if req else 0

        # -- Jobs con bolsa de trabajo activa del mismo puesto --
        bolsa_jobs = sibling_jobs.filtered(lambda j: j.bolsa_trabajo)
        has_bolsa = bool(bolsa_jobs)
        bolsa_job_ids = bolsa_jobs.mapped('id')
        bolsa_req_ids = [sibling_req_map.get(jid, 0) for jid in bolsa_job_ids]
        bolsa_branch_names = []
        for jid in bolsa_job_ids:
            bjob = env['hr.job'].sudo().browse(jid)
            if bjob.exists():
                bolsa_branch_names.append(bjob.company_id.name)

        # -- company_alias, company_state, branch_names --
        parent_company = job.company_id
        if parent_company.parent_id:
            parent_company = parent_company.parent_id
        company_name_raw = parent_company.name or ''
        company_alias = COMPANY_ALIASES.get(company_name_raw, company_name_raw)
        company_state = COMPANY_STATE.get(company_name_raw, DEFAULT_STATE)
        branch_names = []

        return request.render("reclutamiento__kuale.apply2", {
            'job': job,
            'sibling_jobs': sibling_jobs,
            'sibling_req_map': sibling_req_map,
            'record': applicant,
            'error': error,
            'default': default,
            'companyName': companyName,
            'marital_status': marital_status,
            'type_road': type_road,
            'about_vacancy_options': about_vacancy_options,
            'gender_options': gender_options,
            'schoolarship_options': schoolarship_options,
            'identification_option': identification_option,
            'knowledge_experience_options': knowledge_experience_options,
            'language_options': language_options,
            'level_options': level_options,
            'competences_options': competences_options,
            'abilities_options': abilities_options,
            'branch_names': branch_names,
            'company_alias': company_alias,
            'company_state': company_state,
            'has_bolsa': has_bolsa,
            'bolsa_job_ids': bolsa_job_ids,
            'bolsa_req_ids': bolsa_req_ids,
            'bolsa_branch_names': bolsa_branch_names,
        })
    
    @http.route([
        '/jobs/formRecruitment/<int:applicant_id>',
        '/jobs/formRecruitment/<int:applicant_id>/<string:token>'
    ], type='http', auth="public", website=True, sitemap=True)
    def jobs_apply(self, applicant_id, token=None, **kwargs):
        switch_response = self._redirect_to_recruitment_if_needed()
        if switch_response:
            return switch_response
        env = request.env
        applicant_record = env['hr.applicant'].sudo().browse(applicant_id)
        if token:
            vigency_record = request.env['vigency_complement'].sudo().search([('token', '=', token)], limit=1)

            if not vigency_record or not vigency_record.vigency:
                return request.render("reclutamiento__kuale.expiredPage", {})

            current_date = fields.Datetime.now()
            days_passed = (current_date - vigency_record.vigency).days

            if days_passed >= 7:
                return request.render("reclutamiento__kuale.expiredPage", {})
        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')

        applicant = env['hr.applicant'].sudo()
        applicant_b = env['hr.applicant.beneficiary'].sudo()
        beneficiary_relationship_options = \
            applicant_b.fields_get(['beneficiary_relationship'])['beneficiary_relationship']['selection']
        beneficiary_relationship_options.insert(0, ('', '   '))

        marital_status = applicant.fields_get(['marital_status'])['marital_status']['selection']
        about_vacancy_options = applicant.fields_get(['about_vacancy'])['about_vacancy']['selection']
        gender_options = applicant.fields_get(['gender'])['gender']['selection']
        schoolarship_options = applicant.fields_get(['scholarship'])['scholarship']['selection']
        clinics = env['reclutamiento__kuale.clinic'].sudo().search([])
        imss_clinic_options = [(clinic.id, clinic.name) for clinic in clinics]
        nationality_options = applicant.fields_get(['nationality'])['nationality']['selection']
        blood_type_options = applicant.fields_get(['blood_type'])['blood_type']['selection']
        job = applicant_record.job_id
        product_garments = job.products
        try:
            product_template_variants = {}
            for garment in product_garments:
                product_template_id = garment.product_template_id.id
                product_name = garment.product_template_id.name
                if product_template_id not in product_template_variants:
                    product_template_variants[product_template_id] = {
                        'name': product_name,
                        'variants': []
                    }
                    variants = garment.product_template_id.product_variant_ids
                    for variant in variants:
                        variant_dict = variant.read()[0]
                        product_template_variants[product_template_id]['variants'].append(variant_dict)
        except Exception as e:
            print("Error JOB GET :", e)
            # print("product_template_variants...", product_template_variants)
        print('product_template_variants...', product_template_variants)        
        print('DEBUG colony:', repr(applicant_record.colony), 'id:', applicant_record.id)
        return request.render("reclutamiento__kuale.formRecruitment", {
            'record': applicant,
            'applicant_record': applicant_record,
            'marital_status': marital_status,
            'beneficiary_relationship_options': beneficiary_relationship_options,
            'about_vacancy_options': about_vacancy_options,
            'gender_options': gender_options,
            'schoolarship_options': schoolarship_options,
            'imss_clinic_options': imss_clinic_options,
            'nationality_options': nationality_options,
            'blood_type_options': blood_type_options,
            'product_template_variants': product_template_variants,
            'error': error,
            'default': default
        })
    
    @http.route(['/quienes-somos'], type='http', auth="public", website=True)
    def quienes_somos(self, **kwargs):
        switch_response = self._redirect_to_recruitment_if_needed()
        if switch_response:
            return switch_response
        return request.render('reclutamiento__kuale.quienes_somos_page', {})
    
    @http.route('/kuale/login', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def kuale_login_post(self, login=None, password=None, redirect=None, **kwargs):
        redirect = redirect or '/jobs'
        try:
            request.session.authenticate(request.db, login, password)
            if request.session.uid:
                return request.redirect(redirect)
        except AccessDenied:
            pass
        return request.redirect('/jobs?login_error=1')

    @http.route('/kuale/login/ajax', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def kuale_login_ajax(self, login=None, password=None, **kwargs):
        if not login or not password:
            return {'error': 'Por favor completa todos los campos.'}
        try:
            request.session.authenticate(request.db, login, password)
            if request.session.uid:
                return {'success': True, 'redirect': '/jobs'}
        except AccessDenied:
            pass
        except Exception as e:
            return {'error': str(e)}
        return {'error': 'Usuario o contrase�a incorrectos.'}

    @http.route('/kuale/send_verification', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def kuale_send_verification(self, email=None, **kwargs):
        if not email:
            return {'error': 'Correo requerido.'}

        email = email.strip().lower()

        env      = request.env(user=request.env.ref('base.user_root'))
        existing = env['res.users'].search([('login', '=', email)], limit=1)
        if existing:
            return {'error': 'Ya existe una cuenta con ese correo electr�nico.'}

        code       = ''.join(random.choices(string.digits, k=6))
        expires_at = (datetime.utcnow() + timedelta(minutes=KUALE_CODE_TTL)).isoformat()

        request.session[KUALE_VERIFY_KEY] = {
            'email':      email,
            'code':       code,
            'expires_at': expires_at,
            'verified':   False,
        }

        try:
            body_html = """
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;">
                <h2 style="color:#FA0000;">Verifica tu correo</h2>
                <p>Usa este c&oacute;digo para completar tu registro en <strong>Grupo Kuale</strong>:</p>
                <div style="font-size:40px;font-weight:900;letter-spacing:12px;
                            color:#111;text-align:center;padding:24px 0;
                            background:#fff5f5;border-radius:8px;margin:16px 0;">
                    {code}
                </div>
                <p style="color:#888;font-size:13px;">
                    V&aacute;lido por <strong>{ttl} minutos</strong>.<br/>
                    Si no solicitaste esto, ignora este mensaje.
                </p>
            </div>
            """.format(code=code, ttl=KUALE_CODE_TTL)

            mail = env['mail.mail'].create({
                'subject':     'Tu c�digo de verificaci�n � Grupo Kuale',
                'body_html':   body_html,
                'email_to':    email,
                'email_from':  'pruebaskuale@gmail.com',  
                'auto_delete': True,
            })
            mail.send()
        except Exception as e:
            return {'error': 'No se pudo enviar el correo. Intenta de nuevo.'}

        return {'success': True}

    @http.route('/kuale/verify_code', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def kuale_verify_code(self, email=None, code=None, **kwargs):
        if not email or not code:
            return {'error': 'Datos incompletos.'}

        email = email.strip().lower()
        code  = code.strip()

        session_data = request.session.get(KUALE_VERIFY_KEY)

        if not session_data:
            return {'error': 'No hay ning�n c�digo activo. Solicita uno nuevo.'}

        if session_data.get('email') != email:
            return {'error': 'El correo no coincide. Solicita un nuevo c�digo.'}

        try:
            expires_at = datetime.fromisoformat(session_data['expires_at'])
        except (KeyError, ValueError):
            return {'error': 'C�digo inv�lido. Solicita uno nuevo.'}

        if datetime.utcnow() > expires_at:
            request.session.pop(KUALE_VERIFY_KEY, None)
            return {'error': 'El c�digo expir�. Solicita uno nuevo.'}

        if session_data.get('code') != code:
            return {'error': 'C�digo incorrecto. Intenta de nuevo.'}

        data = dict(request.session[KUALE_VERIFY_KEY])
        data['verified'] = True
        request.session[KUALE_VERIFY_KEY] = data

        return {'success': True}

    @http.route('/kuale/signup/ajax', type='json', auth='public', methods=['POST'], csrf=False, website=True)
    def kuale_signup_ajax(self, name=None, login=None, password=None, confirm_password=None,
                          kuale_first_name=None, kuale_last_name=None,
                          kuale_second_last=None, phone=None, zip=None, **kwargs):

        first     = (kuale_first_name or name or '').strip()
        last      = (kuale_last_name   or '').strip()
        second    = (kuale_second_last or '').strip()
        phone_val = (phone or '').strip()
        zip_val   = (zip   or '').strip()

        if not first or not login or not password or not confirm_password:
            return {'error': 'Por favor completa todos los campos.'}
        if password != confirm_password:
            return {'error': 'Las contrase�as no coinciden.'}
        if len(password) < 8:
            return {'error': 'La contrase�a debe tener al menos 8 caracteres.'}
        if not last or not second or not phone_val or not zip_val:
            return {'error': 'Por favor completa todos los datos de perfil.'}

        email = login.strip().lower()

        session_data = request.session.get(KUALE_VERIFY_KEY)
        if not session_data or not session_data.get('verified'):
            return {'error': 'El correo no ha sido verificado.'}
        if session_data.get('email') != email:
            return {'error': 'El correo no coincide con el c�digo verificado.'}

        try:
            env      = request.env(user=request.env.ref('base.user_root'))
            existing = env['res.users'].search([('login', '=', email)], limit=1)
            if existing:
                return {'error': 'Ya existe una cuenta con ese correo electr�nico.'}

            portal_group = env.ref('base.group_portal')
            full_name    = ' '.join(filter(None, [first, last, second]))

            new_user = env['res.users'].create({
                'name':      full_name,
                'login':     email,
                'password':  password,
                'share':     True,
                'groups_id': [(6, 0, [portal_group.id])],
            })

            if new_user:
                new_user.partner_id.write({
                    'kuale_first_name':  first,
                    'kuale_last_name':   last,
                    'kuale_second_last': second,
                    'phone':             phone_val,
                    'zip':               zip_val,
                })
                env.cr.commit()

                request.session.pop(KUALE_VERIFY_KEY, None)

                try:
                    request.session.authenticate(request.db, email, password)
                except Exception:
                    pass

                return {'success': True, 'redirect': '/vacantes'}

            return {'error': 'No se pudo crear la cuenta. Intenta de nuevo.'}

        except Exception as e:
            return {'error': str(e)}

    @http.route('/kuale/perfil/ajax', type='json', auth='user', methods=['POST'], csrf=False, website=True)
    def kuale_perfil_ajax(self, kuale_last_name=None, kuale_second_last=None,
                          phone=None, zip=None, **kwargs):
        last      = (kuale_last_name   or '').strip()
        second    = (kuale_second_last or '').strip()
        phone_val = (phone             or '').strip()
        zip_val   = (zip               or '').strip()

        if not all([last, second, phone_val, zip_val]):
            return {'error': 'Por favor completa todos los campos.'}

        partner   = request.env.user.partner_id
        first     = (partner.kuale_first_name or partner.name or '').strip()
        full_name = ' '.join(filter(None, [first, last, second]))

        partner.sudo().write({
            'name':              full_name,
            'kuale_last_name':   last,
            'kuale_second_last': second,
            'phone':             phone_val,
            'zip':               zip_val,
        })

        return {'success': True, 'redirect': '/vacantes'}

    @http.route('/kuale/perfil/datos', type='json', auth='user', methods=['POST'], csrf=False, website=True)
    def kuale_perfil_datos(self, **kwargs):
        partner = request.env.user.partner_id
        return {
            'kuale_first_name':  partner.kuale_first_name  or '',   
            'kuale_last_name':   partner.kuale_last_name   or '',
            'kuale_second_last': partner.kuale_second_last or '',
            'phone':             partner.phone             or '',
            'zip':               partner.zip               or '',
        }

    @http.route('/mis-aplicaciones', type='http', auth='user', website=True)
    def mis_aplicaciones(self, **kwargs):
        user = request.env.user
        request.env.cr.execute("""
            SELECT id FROM hr_applicant
            WHERE email_from = %s
            AND (hidden_by_applicant IS NULL OR hidden_by_applicant = FALSE)
            ORDER BY id DESC
        """, (user.login,))
        ids = [r[0] for r in request.env.cr.fetchall()]

        # -- active_test=False para incluir candidatos rechazados (archivados) --
        applicants = request.env['hr.applicant'].sudo().with_context(active_test=False).browse(ids)
        
        apps_data = []
        for app in applicants:
            branch_clean = 'N/A'
            if app.requisition_id and app.requisition_id.branch_ids:
                branch_clean = app.requisition_id.branch_ids.name or 'N/A'
            elif hasattr(app, 'branch_id') and app.branch_id and app.branch_id.name:
                branch_clean = app.branch_id.name

            complement_url = None
            if app.stage_id and app.stage_id.name == 'Segunda entrevista' and not app.bank_account_ids:
                vigency = request.env['vigency_complement'].sudo().search(
                    [('applicant_id', '=', app.id)], limit=1
                )
                if vigency and vigency.token:
                    complement_url = f'/jobs/formRecruitment/{app.id}/{vigency.token}'

            apps_data.append({
                'app': app,
                'branch': branch_clean,
                'complement_url': complement_url,
            })

        return request.render('reclutamiento__kuale.mis_aplicaciones_page', {
            'aplicaciones': apps_data,
        })

    @http.route('/mis-aplicaciones/abandonar', type='json', auth='user', methods=['POST'], csrf=False, website=True)
    def abandonar_aplicacion(self, applicant_id=None, reason=None, comment=None, **kwargs):
        if not applicant_id or not reason:
            return {'error': 'Datos incompletos.'}

        applicant = request.env['hr.applicant'].sudo().browse(int(applicant_id))

        if not applicant.exists():
            return {'error': 'Aplicaci�n no encontrada.'}

        if applicant.email_from != request.env.user.login:
            return {'error': 'No autorizado.'}

        # NO archivar � solo marcar como abandonado para que siga visible en kanban
        reason_label = dict(
            applicant._fields['abandonment_reason'].selection
        ).get(reason, reason)

        applicant.write({
            'abandoned':           True,
            'abandonment_reason':  reason,
            'abandonment_comment': comment or '',
            'description': f"? Proceso abandonado por el candidato.\nMotivo: {reason_label}\n{comment or ''}",
        })

        return {'success': True}
    
    @http.route('/mis-aplicaciones/ocultar', type='json', auth='user', methods=['POST'], csrf=False, website=True)
    def ocultar_aplicacion(self, applicant_id=None, **kwargs):
        if not applicant_id:
            return {'success': False, 'error': 'Datos incompletos.'}
        applicant = request.env['hr.applicant'].sudo().browse(int(applicant_id))
        if not applicant.exists():
            return {'success': False, 'error': 'Aplicaci�n no encontrada.'}
        if applicant.email_from != request.env.user.login:
            return {'success': False, 'error': 'No autorizado.'}
        applicant.write({'hidden_by_applicant': True})
        return {'success': True}
    
    @http.route('/report/job/preview/<int:job_id>', type='http', auth='user', website=False)
    def job_report_preview(self, job_id, **kwargs):
        job = request.env['hr.job'].sudo().browse(job_id)
        if not job.exists():
            return request.not_found()
        pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'reclutamiento__kuale.jobSpecifications', [job_id]
        )
        return request.make_response(pdf_content, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', 'inline; filename="preview.pdf"'),
        ])
