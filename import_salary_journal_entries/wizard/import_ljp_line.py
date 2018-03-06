# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class import_ljp_line(models.TransientModel):
    _name = "import.ljp.line"

    import_id = fields.Many2one('import.ljp', 'LJP')
    description = fields.Char(required=True)
    account_id = fields.Many2one('account.account', 'Account', required=True)
    debit = fields.Float(required=True, digits=(16, 2))
    credit = fields.Float(required=True, digits=(16, 2))
