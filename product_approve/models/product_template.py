# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('approved', 'Approved')
                   ], string='Product state',
        default='draft',
        help='Product status.')

    @api.multi
    def button_product_approve(self):
        """Product approve"""
        return self.write({'state': 'approved'})

    @api.multi
    def button_set_to_draft(self):
        """Product set to draft"""
        return self.write({'state': 'draft'})


ProductTemplate()
