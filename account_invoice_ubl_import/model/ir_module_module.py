# -*- coding: utf-8 -*-

from odoo import api, models


class Module(models.Model):
    _inherit = "ir.module.module"

    @api.model
    def deactive_company_registry_module(self):
        """Deactive the company registry field"""
        search_ids = self.search([
            ('name', '=', 'company_registry'),
            ('state', '=', 'installed'),
        ])
        try:
            view_id = self.env.ref(
                'account_invoice_ubl_import.view_res_partner_inherit_company_registry_form', False)
            if search_ids:
                view_id.write({'active': False})
            else:
                if not view_id.active:
                    view_id.write({'active': True})
        except Exception:
            pass

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
