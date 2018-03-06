# -*- coding: utf-8 -*-
from odoo import models, api


class InvoiceConfirmation(models.TransientModel):
    _name = 'invoice.confirmation'
    _description = 'Create Invoice Confirmation for Receive Vendor Bill'

    @api.multi
    def redirect_to_invoice(self):
        self.ensure_one()
        receive_vendor_bill = self.env['receive.vendor.bill'].browse(
            self._context.get('active_id'))
        receive_vendor_bill.with_context(
            {'with_confirmation': True}).create_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
