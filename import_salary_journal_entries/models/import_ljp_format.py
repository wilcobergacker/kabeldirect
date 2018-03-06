# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class import_ljp_format(models.Model):

    _name = "import.ljp.format"

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=lambda self: self.env.user.company_id)
    name = fields.Char('Format Name', size=50, required=True)
    delimiter = fields.Selection([
        ('comma', ','),
        ('semi', ';'), ], 'Delimiter', required=True, default='comma')
    pos_descr = fields.Selection([
        ('1', 'Field 1'),
        ('2', 'Field 2'),
        ('3', 'Field 3'),
        ('4', 'Field 4'),
        ('5', 'Field 5'),
        ('6', 'Field 6'),
        ('7', 'Field 7'),
        ('8', 'Field 8'),
        ('9', 'Field 9'),
        ('10', 'Field 10'),
        ('default', 'Standard Value')], 'Description', required=True)
    value_descr = fields.Char('Value', size=50, default='1')
    pos_account = fields.Selection([
        ('1', 'Field 1'),
        ('2', 'Field 2'),
        ('3', 'Field 3'),
        ('4', 'Field 4'),
        ('5', 'Field 5'),
        ('6', 'Field 6'),
        ('7', 'Field 7'),
        ('8', 'Field 8'),
        ('9', 'Field 9'),
        ('10', 'Field 10'), ], 'Account',
        default='1',
        required=True)
    format_account = fields.Selection([
        ('9999.99', '9999.99'),
        ('none', 'nvt'), ], 'Format',
        default='9999.99',
        required=True)
    pos_amount = fields.Selection([
        ('1', 'Field 1'),
        ('2', 'Field 2'),
        ('3', 'Field 3'),
        ('4', 'Field 4'),
        ('5', 'Field 5'),
        ('6', 'Field 6'),
        ('7', 'Field 7'),
        ('8', 'Field 8'),
        ('9', 'Field 9'),
        ('10', 'Field 10'), ], 'Amount',
        default='1',
        required=True)
    format_amount = fields.Selection([
        ('-9.99', '-9.99'),
        ('-9,99', '-9,99'), ], 'Format',
        default='-9.99',
        required=True)
