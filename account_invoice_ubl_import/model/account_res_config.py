# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pdf2ubl_provider = fields.Selection(
        [('pdf2ubl', 'go2ubl.nl')],
        string='PDF2UBL provider *',
    )
    email_address_fwd_vendor_bill_to = fields.Char(
        string='Email address to forward vendor bill to *',
        size=64,
    )

    @api.model
    def get_values(self):
        # get email to forward vendor bill
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'pdf2ubl_provider': self.env.user.company_id.company_pdf2ubl_provider,
            'email_address_fwd_vendor_bill_to': self.env.user.company_id.company_email_address_fwd_vendor_bill_to
        })
        return res

    @api.multi
    def set_values(self):
        self.ensure_one()
        super(ResConfigSettings, self).get_values()
        # set pdf2ubl to company
        self.env.user.company_id.sudo().write({
            'company_pdf2ubl_provider': self.pdf2ubl_provider})
        # set email to forward vendor bill
        self.env.user.company_id.sudo().write({
            'company_email_address_fwd_vendor_bill_to': self.email_address_fwd_vendor_bill_to})

    # send mail to go2ubl to inform while any pdf is send to ubl accoding to user company
    @api.multi
    def send_mail_to_g02ubl(self):
        self.ensure_one()
        company = self.env.user.company_id
        # create comapny address
        company_address = [
            company.street or '',
            company.street2 or '',
            company.city or '',
            company.state_id and company.state_id.name or '',
            company.zip or '',
            company.country_id and company.country_id.name or ''
        ]
        company_address = ', '.join(filter(lambda a: a, company_address))
        # create message for msg body
        message = _("<div style='font-family: \'Lucida Grande\', Ubuntu, Arial, Verdana, sans-serif; font-size: 12px; color: rgb(34, 34, 34); background-color: #FFF;'>\n   <pre>\n        Hello Go2Ubl,\n\n        This company has installed the Odoo UBL module and has selected Go2UBL as the preferred UBL provider. Please contact them and make the right settings for Odoo.\n\n        - %s,%s\n\n        - %s\n\n        - %s\n\n        - %s\n\n        Thank you.\n   </pre>\n</div>\n" % (
            company.name, company_address, company.company_registry or '',
            company.email or '', company.phone or ''))
        mail_vals = {
            'state': 'outgoing',
            'subject': 'UBL mail Inform to go2ubl',
            'email_from': company.email,
            'email_to': 'info@go2ubl.nl',
            'email_cc': 'info@odooexperts.nl',
            'body_html':  message,
            'auto_delete': True,
            'model': self._name,
            'res_id': self.id,
            'reply_to': company.email or '',
        }
        # mail send if any issue reise exception
        mail_mail = self.env['mail.mail'].create(mail_vals)
        mail_mail.send(raise_exception=True)

    @api.multi
    def setup_company_taxes(self):
        action = self.env.ref('base.action_res_company_form').read()[0]
        action['res_id'] = self.env.user.company_id.id
        action['views'] = [[self.env.ref('base.view_company_form').id, 'form']]
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
