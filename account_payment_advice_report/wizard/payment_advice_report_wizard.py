# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class PaymentAdviceReportWizard(models.TransientModel):
    _name = 'wizard.payment.advice.report'
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self.env.user.company_id)
    from_date = fields.Date('From date', required=True)
    to_date = fields.Date('To date', required=True)
    # date_range_id = fields.Many2one('date.range', 'Date range')
    target = fields.Selection([
        ('posted', 'All Posted Payments'),
        ('reconciled', 'All Reconciled Payments'),
        ('all', 'All Entries'),
    ], 'Target Payments', required=True, default='reconciled')

    '''
    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        if self.date_range_id:
            self.from_date = self.date_range_id.date_start
            self.to_date = self.date_range_id.date_end
        else:
            self.from_date = self.to_date = None
    '''

    @api.multi
    def print_payment_advice_report(self):
        payment_domain = []
        if self.target == 'all':
            state = ['posted','reconciled']
        else:
            state = [self.target]
        payment_domain += [('state','in',state)]
        payment_domain += [('payment_date', '<=', self.to_date), ('payment_date', '>=', self.from_date)]

        payments = self.env['account.payment'].search(payment_domain)

        return self.env['report'].get_action(payments.ids, 'account_payment_advice_report.payment_advice_report_template')