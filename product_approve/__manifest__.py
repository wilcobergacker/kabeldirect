# -*- coding: utf-8 -*-
# © 2017 Vivek Technology (technologyvivek@gmail.com).
# krupesh.laiya@gmail.com
{
    'name': "Product Approve",

    'summary': """
        Feature of product approve.""",

    'description': """
        User can only select those products in sale and purchase which are
        approved.
    In user have new access right added to approve product so user with that access
    right only approve products.
    """,

    'author': "Vivek Technology",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '10.0.0.0.1',
    'currency': 'EUR',
    'price': '0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'sale', 'purchase', ],

    # always loaded
    'data': [
        'security/product_security.xml',
        #'wizard/mass_update_product_view.xml',
        'views/product_template_view.xml',
        'views/sale_view.xml',
        'views/purchase_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}
