# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def _get_payment_advice_report_pages(self):

        p_type_dict = {}
        for option in self._fields['payment_type'].selection:
            p_type_dict[option[0]] = option[1]

        res = {}
        for payment in self:
            key = (payment.payment_date, payment.company_id, payment.payment_type)
            if key not in res:
                res[key] = {}
            if payment not in res[key]:
                res[key][payment] = {}
            if payment.partner_id not in res[key][payment]:
                res[key][payment][payment.partner_id] = []
            for move_line in payment.move_line_ids:
                reconciled_lines = move_line.matched_debit_ids.mapped('debit_move_id') + move_line.matched_credit_ids.mapped('credit_move_id')
                for reconciled_line in reconciled_lines:
                    invoice = reconciled_line.invoice_id
                    if (invoice.type in ('out_invoice', 'in_refund') and reconciled_line in move_line.matched_debit_ids.mapped('debit_move_id')) or (invoice.type in ('in_invoice', 'out_refund') and reconciled_line in move_line.matched_credit_ids.mapped('credit_move_id')):

                        row = {
                            'journal': move_line.journal_id.name,
                            'journal_entry': move_line.move_id.name,
                            'invoice_date': invoice.date_invoice,
                            'date_due': invoice.date_due,
                            'invoice_number': invoice.move_name,
                            'invoice_amount': invoice.amount_total,
                            'invoice_due_amount': invoice.residual,
                            'payment_amount': reconciled_line.credit or reconciled_line.debit,
                            'difference': invoice.residual - (reconciled_line.credit or reconciled_line.debit),
                            'bank_account': payment.partner_bank_account_id and payment.partner_bank_account_id.acc_number or '',
                        }
                        res[key][payment][payment.partner_id].append(row)

        ret = []
        for date, company, payment_type in res:
            key = (date, company, payment_type)
            record = {'date': date, 'company': company.name, 'payment_type':p_type_dict[payment_type], 'lines': []}
            for payment in res[key]:
                record2 = {'payment': payment.name, 'lines': []}
                for partner in res[key][payment]:
                    record2['lines'].append({'partner': partner.name, 'lines': res[key][payment][partner]})
                record['lines'].append(record2)
            ret.append(record)

        return ret