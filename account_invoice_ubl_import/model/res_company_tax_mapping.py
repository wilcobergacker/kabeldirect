# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResCompanyTaxMapping(models.Model):
    _name = 'res.company.tax.mapping'
    _description = 'Company Tax Mapping'

    tax_name = fields.Char(string='Tax Name', size=64)
    account_tax_id = fields.Many2one('account.tax', string='Tax ID')
    company_id = fields.Many2one('res.company', string='Company')
    tax_percent = fields.Float(string='Tax Percent')

    # Tax mapping base on tax tax percent
    @api.constrains('account_tax_id')
    def check_comapny_tax(self):
        # Set Tax according to company
        if self.account_tax_id.company_id != self.company_id:
            raise ValidationError(_("Please select the proper 'Tax Code' that belong to the company"))
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
