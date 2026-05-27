from odoo import models, fields, api


class FormatosWizardLine(models.TransientModel):
    _name = 'reclutamiento__kuale.formatos_wizard_line'
    _description = 'Linea de formato en wizard'

    wizard_id = fields.Many2one(
        'reclutamiento__kuale.formatos_wizard',
        string='Wizard', ondelete='cascade'
    )
    format_id = fields.Many2one(
        'reclutamiento__kuale.format_employee',
        string='Formato', required=True
    )
    name = fields.Char(
        string='Nombre del formato',
        related='format_id.name',
        readonly=True,
        store=True,
    )
    confirmed = fields.Boolean(string='Confirmado', default=False, store=True)

    # ── NUEVO: referencia al ir.attachment ya guardado en hr.applicant ────────
    # Guardamos el ID del adjunto persistente para poder mostrarlo/quitarlo
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Adjunto guardado',
        ondelete='set null',
    )

    # Campos temporales solo para recibir el archivo del wizard de subida
    attachment_datas = fields.Binary(
        string='Datos del archivo (temporal)',
        attachment=False,
    )
    attachment_display_name = fields.Char(
        string='Archivo adjunto',
        store=True,
    )

    def _reopen_wizard(self):
        wizard = self.wizard_id
        if not wizard:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formatos_wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
            'context': {'dialog_size': 'medium'},
        }

    def action_open_format(self):
        self.ensure_one()
        applicant = self.wizard_id.applicant_id
        preview = self.env['reclutamiento__kuale.formatos_preview_wizard'].create_for_format(
            applicant.id,
            self.format_id.id,
        )
        return {
            'name': 'Vista previa - %s' % (self.name or ''),
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formatos_preview_wizard',
            'view_mode': 'form',
            'res_id': preview.id,
            'target': 'new',
            'context': {
                'dialog_size': 'extra-large',
                'formatos_wizard_id': self.wizard_id.id,
            },
        }

    def action_upload_file(self):
        self.ensure_one()
        upload_wiz = self.env['reclutamiento__kuale.formatos_upload_wizard'].create({
            'line_id': self.id,
        })
        return {
            'name': 'Adjuntar archivo - %s' % (self.name or ''),
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formatos_upload_wizard',
            'view_mode': 'form',
            'res_id': upload_wiz.id,
            'target': 'new',
            'context': {'dialog_size': 'small'},
        }

    def action_open_attachment_preview(self):
        self.ensure_one()
        # Primero intentar con el adjunto persistente
        if self.attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.attachment_id.id}?download=false',
                'target': 'new',
            }
        # Fallback: datos temporales en memoria
        if not self.attachment_datas:
            return {'type': 'ir.actions.act_window_close'}
        tmp = self.env['ir.attachment'].sudo().create({
            'name': self.attachment_display_name or 'archivo',
            'type': 'binary',
            'datas': self.attachment_datas,
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{tmp.id}?download=false',
            'target': 'new',
        }

    def action_remove_attachment(self):
        self.ensure_one()
        # Si hay adjunto persistente en hr.applicant, borrarlo también
        if self.attachment_id:
            self.attachment_id.sudo().unlink()
        self.sudo().write({
            'attachment_datas': False,
            'attachment_display_name': False,
            'attachment_id': False,
            'confirmed': False,
        })
        return self._reopen_wizard()

    def action_confirm_line(self):
        """
        Al confirmar: guarda INMEDIATAMENTE el archivo como ir.attachment
        vinculado a hr.applicant (persistencia real). Ya no depende del
        TransientModel para conservar el archivo.
        """
        self.ensure_one()

        # Si ya tiene adjunto persistente, solo marcar confirmado
        if self.attachment_id:
            self.sudo().write({'confirmed': True})
            return self._reopen_wizard()

        if not self.attachment_datas:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Atención',
                    'message': 'Debes adjuntar el archivo antes de confirmar.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        applicant = self.wizard_id.applicant_id

        # ── GUARDAR EN hr.applicant DE INMEDIATO ─────────────────────────────
        att = self.env['ir.attachment'].sudo().create({
            'name': self.attachment_display_name or self.name or 'formato',
            'type': 'binary',
            'datas': self.attachment_datas,
            'res_model': 'hr.applicant',
            'res_id': applicant.id,
            # Tag para identificar que viene del wizard de formatos
            'description': 'formato_wizard:%s' % (self.format_id.id if self.format_id else ''),
        })

        self.sudo().write({
            'confirmed': True,
            'attachment_id': att.id,
            # Limpiar datos temporales para no duplicar en action_confirm (FormatosConfirmWizard)
            'attachment_datas': False,
        })

        return self._reopen_wizard()

    def action_scan_formato(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'kuale_scan_formato',
            'params': {
                'line_id': self.id,
                'wizard_id': self.wizard_id.id,
                'doc_label': self.name or 'Formato',
            },
        }


class FormatosWizard(models.TransientModel):
    _name = 'reclutamiento__kuale.formatos_wizard'
    _description = 'Wizard de formatos del candidato'

    applicant_id = fields.Many2one('hr.applicant', string='Candidato', required=True)
    line_ids = fields.One2many(
        'reclutamiento__kuale.formatos_wizard_line',
        'wizard_id',
        string='Formatos'
    )
    all_confirmed = fields.Boolean(
        string='Todos confirmados',
        compute='_compute_all_confirmed'
    )

    # ── Contrato ──────────────────────────────────────────────────────────────
    contract_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Adjunto contrato (persistente)',
        ondelete='set null',
    )
    contract_datas = fields.Binary(
        string='Datos del contrato (temporal)',
        attachment=False,
    )
    contract_display_name = fields.Char(
        string='Contrato adjunto',
        store=True,
    )

    # ── Formato de Contratación GK ────────────────────────────────────────────
    formato_contratacion_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Adjunto formato contratación (persistente)',
        ondelete='set null',
    )
    formato_contratacion_datas = fields.Binary(
        string='Datos formato contratación (temporal)',
        attachment=False,
    )
    formato_contratacion_display_name = fields.Char(
        string='Formato contratación adjunto',
        store=True,
    )

    @api.depends('line_ids.confirmed')
    def _compute_all_confirmed(self):
        for rec in self:
            rec.all_confirmed = bool(rec.line_ids) and all(
                line.confirmed for line in rec.line_ids
            )

    @api.model
    def create_for_applicant(self, applicant_id):
        """
        Crea el wizard y, si ya existen adjuntos confirmados en hr.applicant
        de una sesión anterior, los recupera para mostrar el estado correcto.
        """
        applicant = self.env['hr.applicant'].browse(applicant_id)
        job = applicant.job_id
        formatos = job.formatos_ids.filtered(lambda f: f.active)

        lines = []
        for f in formatos:
            line_vals = {'format_id': f.id}

            # Buscar si ya hay un adjunto guardado para este formato
            att = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'hr.applicant'),
                ('res_id', '=', applicant_id),
                ('description', '=', 'formato_wizard:%s' % f.id),
            ], limit=1, order='id desc')

            if att:
                line_vals['attachment_id'] = att.id
                line_vals['attachment_display_name'] = att.name
                line_vals['confirmed'] = True

            lines.append((0, 0, line_vals))

        # Recuperar contrato si ya fue guardado
        contract_att = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', applicant_id),
            ('description', '=', 'contrato_firmado'),
        ], limit=1, order='id desc')

        # Recuperar formato contratación si ya fue guardado
        fmt_att = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.applicant'),
            ('res_id', '=', applicant_id),
            ('description', '=', 'formato_contratacion_gk'),
        ], limit=1, order='id desc')

        wizard_vals = {
            'applicant_id': applicant_id,
            'line_ids': lines,
        }
        if contract_att:
            wizard_vals['contract_attachment_id'] = contract_att.id
            wizard_vals['contract_display_name'] = contract_att.name
        if fmt_att:
            wizard_vals['formato_contratacion_attachment_id'] = fmt_att.id
            wizard_vals['formato_contratacion_display_name'] = fmt_att.name

        return self.create(wizard_vals)

    def action_generate_contract(self):
        self.ensure_one()
        wizard = self.env['reclutamiento__kuale.contrato_wizard'].create({
            'applicant_id':       self.applicant_id.id,
            'formatos_wizard_id': self.id,
        })
        return {
            'name':      'Generar Contrato de Trabajo',
            'type':      'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.contrato_wizard',
            'view_mode': 'form',
            'res_id':    wizard.id,
            'target':    'new',
            'context':   {'dialog_size': 'medium'},
        }

    def action_upload_contract(self):
        self.ensure_one()
        upload_wiz = self.env['reclutamiento__kuale.formatos_upload_wizard'].create({
            'contract_wizard_id': self.id,
        })
        return {
            'name': 'Adjuntar contrato firmado',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formatos_upload_wizard',
            'view_mode': 'form',
            'res_id': upload_wiz.id,
            'target': 'new',
            'context': {'dialog_size': 'small'},
        }

    def action_open_contract_preview(self):
        self.ensure_one()
        # Preferir adjunto persistente
        if self.contract_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.contract_attachment_id.id}?download=false',
                'target': 'new',
            }
        if not self.contract_datas:
            return {'type': 'ir.actions.act_window_close'}
        tmp = self.env['ir.attachment'].sudo().create({
            'name': self.contract_display_name or 'contrato',
            'type': 'binary',
            'datas': self.contract_datas,
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{tmp.id}?download=false',
            'target': 'new',
        }

    def action_remove_contract(self):
        # Borrar adjunto persistente si existe
        if self.contract_attachment_id:
            self.contract_attachment_id.sudo().unlink()
        self.sudo().write({
            'contract_datas': False,
            'contract_display_name': False,
            'contract_attachment_id': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'dialog_size': 'medium'},
        }

    def _save_contract_attachment(self, datas, filename):
        """Guarda el contrato como adjunto persistente en hr.applicant."""
        applicant = self.applicant_id
        # Borrar anterior si existe
        if self.contract_attachment_id:
            self.contract_attachment_id.sudo().unlink()
        att = self.env['ir.attachment'].sudo().create({
            'name': filename or 'Contrato firmado',
            'type': 'binary',
            'datas': datas,
            'res_model': 'hr.applicant',
            'res_id': applicant.id,
            'description': 'contrato_firmado',
        })
        self.sudo().write({
            'contract_attachment_id': att.id,
            'contract_display_name': filename or 'Contrato firmado',
            'contract_datas': False,
        })
        return att

    def _save_formato_contratacion_attachment(self, datas, filename):
        """Guarda el formato contratación como adjunto persistente en hr.applicant."""
        applicant = self.applicant_id
        if self.formato_contratacion_attachment_id:
            self.formato_contratacion_attachment_id.sudo().unlink()
        att = self.env['ir.attachment'].sudo().create({
            'name': filename or 'FormatoContratacion.pdf',
            'type': 'binary',
            'datas': datas,
            'res_model': 'hr.applicant',
            'res_id': applicant.id,
            'description': 'formato_contratacion_gk',
            'mimetype': 'application/pdf',
        })
        self.sudo().write({
            'formato_contratacion_attachment_id': att.id,
            'formato_contratacion_display_name': filename or 'FormatoContratacion.pdf',
            'formato_contratacion_datas': False,
        })
        return att

    def action_accept(self):
        self.ensure_one()
        if not self.all_confirmed:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Atención',
                    'message': 'Debes confirmar todos los formatos antes de aceptar.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        confirm_wiz = self.env['reclutamiento__kuale.formatos_confirm_wizard'].create({
            'applicant_id': self.applicant_id.id,
            'formatos_wizard_id': self.id,
        })
        return {
            'name': 'Confirmar Formatos',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formatos_confirm_wizard',
            'view_mode': 'form',
            'res_id': confirm_wiz.id,
            'target': 'new',
        }

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    def action_scan_contrato(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'kuale_scan_contrato',
            'params': {
                'wizard_id': self.id,
                'doc_label': 'Contrato firmado',
            },
        }

    def action_generar_formato_contratacion(self):
        """Abre el wizard para seleccionar el formato base y generar el PDF."""
        self.ensure_one()
        wizard = self.env['reclutamiento__kuale.formato_contratacion_wizard'].create({
            'applicant_id': self.applicant_id.id,
            'formatos_wizard_id': self.id,
        })
        return {
            'name': 'Generar Formato de Contratación',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formato_contratacion_wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    def action_upload_formato_contratacion(self):
        self.ensure_one()
        upload_wiz = self.env['reclutamiento__kuale.formatos_upload_wizard'].create({
            'formato_contratacion_wizard_id': self.id,
        })
        return {
            'name': 'Adjuntar Formato de Contratación',
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formatos_upload_wizard',
            'view_mode': 'form',
            'res_id': upload_wiz.id,
            'target': 'new',
            'context': {'dialog_size': 'small'},
        }

    def action_scan_formato_contratacion(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'kuale_scan_formato_contratacion',
            'params': {
                'wizard_id': self.id,
                'doc_label': 'Formato de Contratación GK',
            },
        }

    def action_preview_formato_contratacion(self):
        self.ensure_one()
        # Preferir adjunto persistente
        if self.formato_contratacion_attachment_id:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.formato_contratacion_attachment_id.id}?download=false',
                'target': 'new',
            }
        if not self.formato_contratacion_datas:
            return {'type': 'ir.actions.act_window_close'}
        tmp = self.env['ir.attachment'].sudo().create({
            'name': self.formato_contratacion_display_name or 'formato_contratacion.pdf',
            'type': 'binary',
            'datas': self.formato_contratacion_datas,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{tmp.id}?download=false',
            'target': 'new',
        }

    def action_remove_formato_contratacion(self):
        if self.formato_contratacion_attachment_id:
            self.formato_contratacion_attachment_id.sudo().unlink()
        self.sudo().write({
            'formato_contratacion_datas': False,
            'formato_contratacion_display_name': False,
            'formato_contratacion_attachment_id': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'dialog_size': 'medium'},
        }


class FormatosConfirmWizard(models.TransientModel):
    _name = 'reclutamiento__kuale.formatos_confirm_wizard'
    _description = 'Confirmacion final de formatos'

    applicant_id = fields.Many2one('hr.applicant', string='Candidato', required=True)
    formatos_wizard_id = fields.Many2one(
        'reclutamiento__kuale.formatos_wizard',
        string='Wizard de formatos'
    )

    def action_confirm(self):
        """
        Los archivos de las líneas ya fueron guardados al confirmar cada una.
        Aquí solo guardamos contrato y formato_contratacion si aún están en
        memoria (subidos pero no persistidos), y marcamos formatos_verified.
        """
        self.ensure_one()
        wizard = self.formatos_wizard_id
        applicant = self.applicant_id

        if wizard:
            # Las líneas ya persistieron su adjunto en action_confirm_line.
            # Solo manejar los que aún tengan datos en memoria (no persistidos aún).
            for line in wizard.line_ids:
                if line.attachment_datas and not line.attachment_id:
                    self.env['ir.attachment'].sudo().create({
                        'name': line.attachment_display_name or line.name or 'formato',
                        'type': 'binary',
                        'datas': line.attachment_datas,
                        'res_model': 'hr.applicant',
                        'res_id': applicant.id,
                        'description': 'formato_wizard:%s' % (line.format_id.id if line.format_id else ''),
                    })

            # Contrato: persistir si aún está en memoria
            if wizard.contract_datas and not wizard.contract_attachment_id:
                wizard._save_contract_attachment(
                    wizard.contract_datas,
                    wizard.contract_display_name or 'Contrato firmado'
                )

            # Formato contratación: persistir si aún está en memoria
            if wizard.formato_contratacion_datas and not wizard.formato_contratacion_attachment_id:
                wizard._save_formato_contratacion_attachment(
                    wizard.formato_contratacion_datas,
                    wizard.formato_contratacion_display_name or 'FormatoContratacion.pdf'
                )

        applicant.write({'formatos_verified': True})
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        self.ensure_one()
        wizard = self.formatos_wizard_id
        if not wizard:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formatos_wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
            'context': {'dialog_size': 'medium'},
        }


class FormatosUploadWizard(models.TransientModel):
    _name = 'reclutamiento__kuale.formatos_upload_wizard'
    _description = 'Subir archivo de formato'

    line_id = fields.Many2one(
        'reclutamiento__kuale.formatos_wizard_line',
        string='Línea'
    )
    contract_wizard_id = fields.Many2one(
        'reclutamiento__kuale.formatos_wizard',
        string='Wizard (contrato)'
    )
    formato_contratacion_wizard_id = fields.Many2one(
        'reclutamiento__kuale.formatos_wizard',
        string='Wizard (formato contratación)'
    )
    attachment_data = fields.Binary(string='Archivo', attachment=False)
    attachment_filename = fields.Char(string='Nombre del archivo')

    def _regresar_wizard(self):
        wizard = (
            self.contract_wizard_id
            or self.formato_contratacion_wizard_id
            or (self.line_id.wizard_id if self.line_id else False)
        )
        if not wizard:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'reclutamiento__kuale.formatos_wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
            'context': {'dialog_size': 'medium'},
        }

    def action_upload(self):
        self.ensure_one()
        if not self.attachment_data:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Atención',
                    'message': 'Selecciona un archivo antes de subir.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        filename = self.attachment_filename or 'archivo'

        if self.formato_contratacion_wizard_id:
            # ── Persistir inmediatamente en hr.applicant ─────────────────────
            self.formato_contratacion_wizard_id._save_formato_contratacion_attachment(
                self.attachment_data, filename
            )
        elif self.contract_wizard_id:
            # ── Persistir inmediatamente en hr.applicant ─────────────────────
            self.contract_wizard_id._save_contract_attachment(
                self.attachment_data, filename
            )
        elif self.line_id:
            filename = self.attachment_filename or self.line_id.name or 'formato'
            # Solo guardar en la línea (temporal); el usuario confirmará después
            self.line_id.sudo().write({
                'attachment_datas': self.attachment_data,
                'attachment_display_name': filename,
            })

        return self._regresar_wizard()

    def action_cancel(self):
        self.ensure_one()
        return self._regresar_wizard()