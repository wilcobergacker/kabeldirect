# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Partner'

    # Propety account expense set base on company login
    property_account_expense = fields.Many2one(
        'account.account',
        string='Default expense account',
        domain=[('user_type_id.type', '=', 'other')],
        company_dependent=True,
        help='Default counterpart account for purchases',
        required=False)

    # onchange if set auto update than it will change account
    auto_update_account_expense = fields.Boolean(
        'Auto Save',
        help='When account selected on invoice, automatically save it',
        default=True)
    company_registry = fields.Char(string="Company Registry")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
