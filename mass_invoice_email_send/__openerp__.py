# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Mass Invoices Send by Email',
    'version': '1.0',
    'price': 20.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category': 'Accounting',
    'summary': 'This module allow user to send invoices to customers by running mass mailing wizard.',
    'description': """
This module allow user to send invoices to customers by running mass mailing wizard.'

Tags:
Send Invoice by email
Invoices by email
Email invoices
Send Invoice email to customers
mass invoice
mass email
mass mail
group invoices
group invoice
send invoice
invoice send by email
customer invoices by email
email to customer
invoice report to customer send
odoo invoice
            """,
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'www.probuse.com',
    'images': ['static/description/img1.jpeg'],
    'live_test_url' : 'https://youtu.be/6NvrcASpJAg',
    'depends': ['account'],
    'data': [
            'wizard/invoice_email_send.xml',
             ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
