# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import time

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class import_ljp(models.TransientModel):
    """ Importeren Salary Journal Entries """

    _name = "import.ljp"
    _description = "Import Salary Journal Entries"

    @api.model
    def _get_journal(self):
        journal = self.env['account.journal'].search(
            [('company_id', '=', self.env.user.company_id.id),
             ('code', '=', 'LJP')],
            limit=1)
        return journal

    @api.model
    def _get_format(self):
        Format = self.env['import.ljp.format']
        format = Format.search([], limit=1)
        return format

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=lambda self: self.env.user.company_id
    )
    format_id = fields.Many2one(
        'import.ljp.format',
        'Format',
        required=True,
        default=_get_format
    )
    journal_id = fields.Many2one(
        'account.journal',
        'Journal',
        required=True,
        default=_get_journal
    )
    booking_date = fields.Date('Entry Date', required=True)
    lines = fields.One2many('import.ljp.line', 'import_id', 'Rows')
    ljp_data = fields.Binary('File', required=True)
    ljp_fname = fields.Char('File Name', required=True)
    state = fields.Selection(
        [('draft', 'Draft'),
         ('ready', 'ready'),
         ],
        default='draft',
        required=True
    )

    @api.model
    def get_description(self, items, pos, default_value):
        if pos == 'default':
            return default_value

        try:
            pos = int(pos) - 1
            return items[pos]
        except:
            return False

    @api.model
    def get_amount(self, items, pos, format):
        if format == '-9.99':
            try:
                pos = int(pos) - 1
                amount = items[pos].replace(',', '')
                return float(amount)
            except:
                return False
        elif format == '-9,99':
            try:
                pos = int(pos) - 1
                amount = items[pos].replace('.', '').replace(',', '.')
                return float(amount)
            except:
                return False
        else:
            return False

    @api.model
    def get_amount_debit(self, items, pos, format):
        debit = self.get_amount(items, pos, format)
        if debit > 0.0:
            return debit
        return 0.0

    @api.model
    def get_amount_credit(self, items, pos, format):
        credit = self.get_amount(items, pos, format)
        if credit < 0.0:
            return abs(credit)
        return 0.0

    @api.model
    def get_account(self, company_id, items, pos, format):
        try:
            pos = int(pos) - 1
            acc_code = items[pos].strip()
        except:
            return False

        if format == '9999.99':
            if '.' not in acc_code:
                acc_code = '%s.00' % (acc_code)

        account = self.env['account.account'].search(
            [('company_id', '=', company_id), ('code', '=', acc_code)],
            limit=1)
        if not account:
            raise UserError(_('Account [%s] is not valid!' % (acc_code)))
        return account.id

    @api.multi
    def do_import(self):
        self.ensure_one()

        try:
            resultfile = self.ljp_data
        except:
            raise UserError(_('An error occured while importing the entries.'))

        recordlist = unicode(
            base64.decodestring(resultfile),
            'windows-1252', 'strict').split('\n')

        lines = []
        for line in recordlist:
            if not line:
                continue

            unicode_string = line.decode("utf-8")
            len_string = len(unicode_string)
            if not len_string:
                continue

            items = line.split(
                ',' if self.format_id.delimiter == 'comma' else ';')
            line = {
                'description': self.get_description(
                    items,
                    self.format_id.pos_descr,
                    self.format_id.value_descr),
                'account_id': self.get_account(
                    self.company_id.id,
                    items,
                    self.format_id.pos_account,
                    self.format_id.format_account),
                'debit': self.get_amount_debit(
                    items,
                    self.format_id.pos_amount,
                    self.format_id.format_amount),
                'credit': self.get_amount_credit(
                    items,
                    self.format_id.pos_amount,
                    self.format_id.format_amount)
            }
            lines.append((0, 0, line))

        try:
            self.write({'lines': [(5,)]})
            self.write({'lines': lines, 'state': 'ready'})
        except:
            raise
            raise UserError(_(
                '''Error while importing!
                Please check if you used the correct format.'''))

        view_id = self.env['ir.model.data'].get_object_reference(
            'import_salary_journal_entries', 'view_import_ljp')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': _(''),
            'res_model': 'import.ljp',
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'nodestroy': True,
        }

    @api.multi
    def do_book(self):
        self.ensure_one()

        move_lines = []
        for line in self.lines:
            if line.debit:
                l = {
                    'debit': line.debit,
                    'credit': 0.0,
                    'account_id': line.account_id.id,
                    'partner_id': False,
                    'ref': line.description,
                    'name': line.description,
                    'date': self.booking_date,
                    'currency_id': False,
                    'amount_currency': 0.0,
                    'company_id': self.company_id.id,
                }
                move_lines.append((0, 0, l))
            elif line.credit:
                l = {
                    'debit': 0.0,
                    'credit': line.credit,
                    'account_id': line.account_id.id,
                    'partner_id': False,
                    'ref': line.description,
                    'name': line.description,
                    'date': self.booking_date,
                    'currency_id': False,
                    'amount_currency': 0.0,
                    'company_id': self.company_id.id,
                }
                move_lines.append((0, 0, l))

        if move_lines:
            if self.journal_id.sequence_id:
                jn_number = self.journal_id.sequence_id.next_by_id()
            else:
                jn_number = '/'

            move = {
                'name': jn_number,
                'ref': 'Import loonjournaalposten: %s' % (
                    time.strftime('%Y-%m-%d')
                ),
                'line_ids': move_lines,
                'journal_id': self.journal_id.id,
                'date': self.booking_date,
                'narration': '',
                'company_id': self.company_id.id,
                }
            self.env['account.move'].create(move)
