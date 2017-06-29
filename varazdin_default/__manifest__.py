# -*- coding: utf-8 -*-
{
    'name' : 'varazdin_default',
    'version' : '10.0.0.1',
    'summary': 'default module for varazdin',
    'sequence': 30,
    'description': """
Varazdin
========
    """,
    'category': 'Default',
    'author': 'jeo Software,',
    'website': 'http://www.jeosoft.com',
    'images' : [],
    'depends' : ['stock'],
    'data': [
        'views/simple_picking.xml',
        'views/config_settings_view.xml',
        'views/courier_view.xml',
        'views/location_view.xml',
        'views/route_view.xml'
    ],
    'demo': [

    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
