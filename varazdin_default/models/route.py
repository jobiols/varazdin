# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------------
#
#    Copyright (C) 2017  jeo Software  (http://www.jeosoft.com.ar)
#    All Rights Reserved.
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
# -----------------------------------------------------------------------------------
from odoo import api, fields, models
from odoo.addons.varazdin_default.secupack_lib.secupack import SecupackClient
from odoo.exceptions import Warning


class Route(models.Model):
    _name = 'route'
    _description = 'Rutas'

    date = fields.Date(
        'Fecha',
        help='Fecha en la que hace el recorrido'
    )
    location_id = fields.Many2one(
        'stock.location',
        'Ubicacion',
        help='Ubicacion a vistiar en esta fecha'
    )
    courier_id = fields.Many2one(
        'courier',
        'Transporte',
        help='Transporte que realiza la visita'
    )