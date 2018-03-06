# -*- coding: utf-8 -*-

from openerp import models, fields, api

class InvoiceEmailSend(models.TransientModel):
    _name = 'invoice.email.send'
    
    @api.multi
    def invoice_email_send(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['account.invoice'].browse(active_ids):
            if record.partner_id.email:
                module = self.env['ir.module.module'].sudo().search([('name', '=', 'portal_sale')])
                if module.state == 'installed':
                   template = self.env.ref('account.email_template_edi_invoice')
                   template.send_mail(record.id, force_send=False)
                else:
                   template = self.env.ref('account.email_template_edi_invoice')
                   template.send_mail(record.id, force_send=False)
        return record

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
