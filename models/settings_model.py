from odoo import models, fields, api
from datetime import date, datetime
import csv
import os


class RecruitmentSettings(models.Model):
    _name = 'reclutamiento__kuale.recruitment_settings'

    email_recruitment = fields.Char(string="Correo")
    access_token_wsp = fields.Char(string="Token de Acceso")
    number_id = fields.Char(string="Identificador de número de teléfono")
    template_wsp = fields.Char(string="Plantilla")
    cities_created = fields.Boolean(default=False, string="Archivo cargado")
    schooling_created = fields.Boolean(default=False, string="Catalogo de grados academicos cargado")
    _sql_constraints = [
        ('unique_recruitment_settings', 'UNIQUE(id)', 'Solo puede existir un registro de configuración.')
    ]

    def create(self, vals):
        # Buscar el registro existente
        existing_record = self.sudo().search([], limit=1)
        if existing_record:
            # Si ya existe, se actualiza y se devuelve el registro
            existing_record.write(vals)
            return existing_record
        else:
            # Si no existe, se crea un nuevo registro
            return super(RecruitmentSettings, self).create(vals)

    @api.model
    def default_get(self, fields_list):
        res = super(RecruitmentSettings, self).default_get(fields_list)
        # Buscar el único registro existente
        existing = self.sudo().search([], limit=1)
        if existing:
            res['email_recruitment'] = existing.email_recruitment
            res['access_token_wsp'] = existing.access_token_wsp
            res['number_id'] = existing.number_id
            res['template_wsp'] = existing.template_wsp
        return res

    def import_postal_codes(self):
        print("import_postal_codes")
        try:
            if not self.cities_created:
                module_path = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(module_path, '..', 'static/src/codes.csv')
                ruta = os.path.normpath(file_path)
                print("ruta", ruta)
                with open(ruta, 'r') as file:
                    reader = csv.DictReader(file)
                    print("reader")
                    for row in reader:
                        print("row['Código']", row['Código'])
                        self.env['reclutamiento__kuale.city'].create({
                            'code': row['Código'],
                            'settlement': row['Asentamiento'],
                            'settlement_type': row['Tipo'],
                            'municipality': row['Municipio'],
                            'city': row['Ciudad'],
                            'state': row['Estado'],
                        })
                    print("fin")
                self.write({'cities_created': True})
        except Exception as e:
            print("Error import_postal_codes :", e)

    def import_schooling_catalog(self):
        print("import_schooling_catalog")
        try:
            if not self.schooling_created:
                module_path = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(module_path, '..', 'static/src/schooling.csv')
                ruta = os.path.normpath(file_path)
                with open(ruta, 'r') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        self.env['reclutamiento__kuale.schooling'].create({
                            'name': row['Name'],
                            'description': row['Description'],
                        })
                self.write({'schooling_created': True})
        except Exception as e:
            print("Error import_schooling_catalog :", e)
