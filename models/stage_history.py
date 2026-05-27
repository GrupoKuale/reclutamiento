from odoo import models, fields, api
from datetime import datetime


class StageHistory(models.Model):
    _name = 'hr.applicant.stage_history'
    _description = 'Historial de cambios de etapa'

    applicant_id = fields.Many2one('hr.applicant', string="Aplicación")
    stage_id = fields.Many2one('hr.recruitment.stage', string="Etapa", required=True)
    start_time = fields.Datetime(string="Hora de inicio", required=True, default=fields.Datetime.now)
    end_time = fields.Datetime(string="Hora de fin")
    duration = fields.Float(string="Duración (horas)", compute='_compute_duration', store=False)
    duration_readable = fields.Char(string="Duración", compute='_compute_duration_readable', store=False)

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for record in self:
            if not record.end_time:
                delta = datetime.now() - record.start_time
            record.duration = delta.total_seconds() / 3600  # Duración en horas

    @api.depends('start_time', 'end_time')
    def _compute_duration_readable(self):
        for record in self:
            if record.end_time:
                end_time = record.end_time
            else:
                end_time = datetime.now()
            if record.start_time:
                delta = end_time - record.start_time
                days = delta.days
                hours, remainder = divmod(delta.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                readable_format = []
                if days:
                    readable_format.append(f"{days} día{'s' if days > 1 else ''}")
                if hours:
                    readable_format.append(f"{hours} hora{'s' if hours > 1 else ''}")
                if minutes:
                    readable_format.append(f"{minutes} minuto{'s' if minutes > 1 else ''}")

                record.duration_readable = ', '.join(readable_format)


    def close_stage(self):
        self.end_time = fields.Datetime.now()


class RecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'

    visualize_form = fields.Boolean('Visualizar en formulario', default=False)