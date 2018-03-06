# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    "name" : "Mass Invoices Send by Email",
    "version" : "11.0.0.0",
    "category" : "Accounting",
    "depends" : ['base','sale','account','sale_management'],
    "author": "BrowseInfo",
    'summary': 'Apps helps to send mass email for invoices in one click.',
    "description": """
send mass email in one click, mass invoices send by email, mass sales order send by email, mass purchase order send by email, mass email sales order, mass email purchase order, mass email invoices send by email. Apps helps to send mass email for invoices, sales order and purchase orders in one click, easy email, email to customer, email to invoice, invoice email, email to sales, sales email, purchase email, send to customer, bulk invoice send by email, bulk sales order send by email, bulk purchase order send by email.
    """,
    "website" : "www.browseinfo.in",
    'price': '10.00',
    'currency': "EUR",
    "data": [
        'views/mass_mail_view.xml',
    ],
    'qweb': [],
    "auto_install": False,
    "installable": True,
    "images":['static/description/banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
