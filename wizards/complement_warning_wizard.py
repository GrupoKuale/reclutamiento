from odoo import models, fields, api


class ComplementWarningWizard(models.TransientModel):
    _name        = 'reclutamiento__kuale.complement_warning_wizard'
    _description = 'Advertencia complemento pendiente'

    applicant_id = fields.Many2one('hr.applicant', required=True)
    step         = fields.Integer(default=1)

    # ── Campos computed para mostrar detalle de pendientes ───────────────────
    missing_bank         = fields.Boolean(compute='_compute_missing', store=False)
    missing_beneficiary  = fields.Boolean(compute='_compute_missing', store=False)
    missing_docs_names   = fields.Char(compute='_compute_missing', store=False)
    missing_formatos     = fields.Boolean(compute='_compute_missing', store=False)
    can_skip             = fields.Boolean(compute='_compute_missing', store=False)

    @api.depends('applicant_id')
    def _compute_missing(self):
        for rec in self:
            a = rec.applicant_id

            rec.missing_bank        = not a.bank_account_ids
            rec.missing_beneficiary = not a.beneficiaries_ids

            # Documentos no confirmados
            docs_pending = a.documentation_ids.filtered(
                lambda d: d.state != 'confirmed'
            )
            if docs_pending:
                label_map = dict(
                    self.env['hr.applicant.documentation']
                    .fields_get(['doc_type'])['doc_type']['selection']
                )
                names = [label_map.get(d.doc_type, d.doc_type) for d in docs_pending]
                rec.missing_docs_names = ', '.join(names)
            else:
                rec.missing_docs_names = False

            rec.missing_formatos = not a.formatos_verified

            # Solo se puede omitir si documentación y formatos están completos
            # (solo faltan bancarios o beneficiarios)
            rec.can_skip = not rec.missing_formatos

    def action_skip(self):
        """Paso 1 → Paso 2: confirmación antes de crear sin bancarios."""
        self.write({'step': 2})
        return {
            'type':      'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id':    self.id,
            'target':    'new',
        }

    def action_confirm_skip(self):
        """Paso 2: crear empleado con complemento pendiente."""
        return self.applicant_id._do_create_employee(complement_pending=True)

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}