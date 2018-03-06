# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Import Salary Journal Entries',
    'author': 'Onestein',
    'summary': 'Import Salary Journal Entries from CSV.',
    'website': 'http://www.onestein.eu',
    'license': 'AGPL-3',
    'version': '10.0.1.0.0',
    'depends': [
        'account',
        'account_asset',
    ],
    'category': 'Accounting & Finance',
    'data': [
        'security/ir.model.access.csv',
        'views/import_ljp_format.xml',
        'wizard/import_ljp.xml',
        'menu_items.xml',
    ],
    'installable': True,
}
