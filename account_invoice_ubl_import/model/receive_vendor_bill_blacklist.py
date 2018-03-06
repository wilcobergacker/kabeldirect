# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class ReceiveVendorBillBlacklist(models.Model):
    _name = 'receive.vendor.bill.blacklist'
    _description = 'Blacklist For Receiving Vendor Bills'
    _rec_name = 'email'

    email = fields.Char('Email For Blacklist', copy=False)
    reason = fields.Text('Reason For Blacklist', copy=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
