# -*- coding: utf-8 -*-
# © 2016 Lorenzo Battistini - Agile Business Group
# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Payment Advice Report",
    "summary": "Payment Advice Report",
    "version": "10.0.1.1.0",
    "category": "Accounting & Finance",
    "website": "https://www.agilebg.com/",
    "author": "Onestein, "
              "ERP|OPEN, "
              "Cas Vissers, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
    ],
    "data": [
        "report/payment_advice_report_template.xml",
        "wizard/payment_advice_report_wizard.xml",
    ],
    "images": [
        'images/tax_balance.png',
    ]
}
