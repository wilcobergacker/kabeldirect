# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.tools.translate import _


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def _default_account(self):
        # set default account to invoice line
        # set acconnt base on company property from partner account_id
        invoice_type = self._context.get('type')
        journal = self.env['account.journal'].browse(
            self._context.get('journal_id'))
        if self._context.get('partner_id'):
            partner = self.env['res.partner'].with_context(
                force_company=journal.company_id.id).browse(
                    self._context.get('partner_id'))
            # check invoice type as in_invoice, In_refund
            if partner and invoice_type in ['in_invoice', 'in_refund']:
                if partner.property_account_expense:
                    return partner.property_account_expense.id
        return super(AccountInvoiceLine, self)._default_account()

    account_id = fields.Many2one(
        'account.account', string='Account',
        required=True, domain=[('deprecated', '=', False)],
        default=_default_account,
        help="The income or expense account related to the selected product.")

    @api.onchange('account_id')
    def _onchange_account_id(self):
        if (
            self.account_id and self.partner_id and (
                not self.product_id) and self._context.get(
                    'type') in ['in_invoice', 'in_refund']):
            # We have a manually entered account_id (no product_id, so the
            # account_id is not the result of a product selection).
            # Store this account_id as future default in res_partner.
            assert self.partner_id, (
                _('No object created for partner %d') % self.partner_id)
            if self.partner_id.auto_update_account_expense:
                old_account_id = (
                    self.partner_id.property_account_expense
                    and self.partner_id.property_account_expense.id)
                if self.account_id.id != old_account_id:
                    # only write when something really changed
                    vals = {'property_account_expense': self.account_id.id}
                    self.partner_id.write(vals)
        return super(AccountInvoiceLine, self)._onchange_account_id()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
