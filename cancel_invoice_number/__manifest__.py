# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Othmane GHANDI (Usman BEK)
#    Copyright (C) <http://www.odoo.gotodoo.com>.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Invoice number in cancelled invoices',
    'version': '10.0',
    'category': 'Accounting',
    'sequence': 1,
    'complexity': 'normal',
    'description': '''This module will show invoice number even if invoice is
cancelled.''',

    'author': 'Odoo Tips',
    'license': 'AGPL-3',
    'website': 'http://www.gotodoo.com',
    'currency': 'EUR',
    'price': 5.99,
    'depends': ['base',
                'account',
                'account_cancel',
                ],
    'data': [
        'invoice_cancel_view.xml',
        'report_invoice.xml',
    ],
    'images': ['images/main_screenshot.png'],
    'update': [],
    'test': [],  # YAML files with tests
    'installable': True,
    'application': False,
    # If it's True, the modules will be auto-installed when all dependencies
    # are installed
    'auto_install': False,
    'certificate': '',
}
