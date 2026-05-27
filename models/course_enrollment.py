
from odoo import api, models, fields


class SlideChannel(models.Model):
    _inherit = 'slide.channel.partner'

    startDate = fields.Datetime(string='Fecha de inicio')
    endDate = fields.Datetime(string='Fecha de finalización')

    def unlink(self):
        for record in self:
            calendar_events = self.env['calendar.event'].search([
                ('name', '=', f'Course {self.channel_id.name}'),
                ('partner_ids', 'in', record.partner_id.id)
            ])
            if calendar_events:
                calendar_events.unlink()

        return super(SlideChannel, self).unlink()


class CourseEnrollment(models.TransientModel):
    _inherit = 'slide.channel.invite'

    startDate = fields.Datetime('Fecha de inicio', required=True)
    endDate = fields.Datetime('Fecha de finalización', required=True)

    def action_invite(self):
        # Lógica existente del wizard
        res = super(CourseEnrollment, self).action_invite()

        invited_partners = self.channel_id.partner_ids

        for partner in invited_partners:
            # Buscar la inscripción específica para cada partner
            enrollment = self.env['slide.channel.partner'].sudo().search([
                ('channel_id', '=', self.channel_id.id),
                ('partner_id', '=', partner.id)
            ], limit=1)
            
            # Actualizar las fechas de inicio y fin de la inscripción
            if enrollment:
                enrollment.sudo().write({
                    'startDate': self.startDate,
                    'endDate': self.endDate
                })

        formatted_attendees = []
        for partner in invited_partners:
            formatted_attendees.append([0, 0, {
                'partner_id': partner.id,
                'state': 'accepted' 
            }])

        self.env['calendar.event'].create({
            'name': f'Course {self.channel_id.name}',
            'start': self.startDate,
            'stop': self.endDate,
            'course': True,
            'description': self.channel_id.description,
            'attendee_ids': formatted_attendees, 
        })

        return res

