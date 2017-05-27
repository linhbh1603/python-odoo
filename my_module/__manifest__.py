# -*- coding: utf-8 -*-
{
    'name': "my_module",

    'summary': "Short subtitle phrase",

    'description': """Long description""",

    'author': "Your name",
    'website': "http://www.example.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'decimal_precision'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/authors.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/library_book.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}