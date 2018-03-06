# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    "name": 'Odoo UBL Factuur Import',
    "version": '1.11',
    "description": """
        Deze module maakt het mogelijk om UBL leveranciersfacturen te
        importeren en zo het proces van verwerken van
        leveranciersfacturen te automatiseren.
    """,
    "author": 'Odoo Experts',
    "website": 'https://www.odooexperts.nl',
    "category": "Accounting",
    "price": 497.00,
    "currency": 'EUR',
    'images': [],
    "depends": ["account", "sale", "account_accountant"],
    "init_xml": [],
    'data': [
        "security/ir.model.access.csv",
        "security/receive_vendor_bill_security.xml",
        "data/cron_process_vendor_bill.xml",
        "data/cron_send_pdf_to_ubl_provider.xml",
        "data/send_mail_to_ubl_provider_email_template.xml",
        "data/deactive_company_registry.xml",
        "wizard/invoice_confirmation.xml",
        "view/fetchmail_view.xml",
        "view/account_invoice_view.xml",
        "view/account_res_config_view.xml",
        "view/res_partner_view.xml",
        "view/receive_vendor_bill_line_view.xml",
        "view/receive_vendor_bill_view.xml",
        "view/receive_vendor_bill_sequence.xml",
        "view/res_company_tax_mapping_view.xml",
        "view/res_company_view.xml",
        "view/receive_vendor_bill_blacklist_view.xml",
    ],
    "test": [],
    "demo_xml": [],
    "installable": True,
    'auto_install': False,
    'license': 'Other proprietary',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
