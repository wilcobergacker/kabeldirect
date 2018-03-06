# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = 'Company'

    # Tax maopping configuration
    res_company_tax_mapping_ids = fields.One2many(
        'res.company.tax.mapping',
        'company_id',
        string='Tax Mapping',
    )

    # set PDF2UBL provider from account configuration
    company_pdf2ubl_provider = fields.Selection(
        [('pdf2ubl', 'go2ubl.nl')],
        string='PDF2UBL provider',
        default='pdf2ubl',
    )

    # set emaill Address of Send Pdf to Ubl provider
    company_email_address_fwd_vendor_bill_to = fields.Char(
        string='Email address to forward vendor bill to',
        size=64,
    )

    @api.one
    def get_tax(self, percent=None):
        # tax mapping from Tax Mapping base on percentage value
        tax_id = False
        for tax_map in self.res_company_tax_mapping_ids:
            if tax_map.tax_percent == percent:
                tax_id = tax_map.account_tax_id
        if not tax_id:
            _logger.warning(_("Please configure the Tax in 'Tax Configuration' page at company level."))
        return tax_id
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
