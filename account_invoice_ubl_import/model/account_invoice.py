# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
from odoo.tools import float_round


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.depends('ubl_import_process_id')
    def display_error_message(self):
        for rec in self:
            if not rec.ubl_import_process_id:
                return
            rec_vendor_bill_amount = rec.ubl_import_process_id.tax_inclusive_amount if rec.ubl_import_process_id.tax_inclusive_amount else rec.ubl_import_process_id.payable_amount
            rec_vendor_bill_amount = (rec_vendor_bill_amount * -1) if rec.type == 'in_refund' else rec_vendor_bill_amount
            if float_round(rec.amount_total, rec.currency_id.decimal_places) != float_round(rec_vendor_bill_amount, rec.currency_id.decimal_places):
                rec.display_message = True
                rec.invoice_amount = float_round(rec.amount_total, rec.currency_id.decimal_places)
                rec.error_message = float_round(rec_vendor_bill_amount, rec.currency_id.decimal_places)

    # Ubl Vendor bill
    ubl_import_process_id = fields.Many2one(
        'receive.vendor.bill',
        string='UBL Import Process', ondelete='restrict')
    display_message = fields.Boolean('Display Error Message',
                                     compute='display_error_message')
    invoice_amount = fields.Float('Invoice Amount',
                                  compute='display_error_message')
    error_message = fields.Float('Receive Vendor Bill Amount',
                                 compute='display_error_message')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
