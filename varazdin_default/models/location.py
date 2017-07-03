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
from odoo import fields, models


class Location(models.Model):
    _inherit = "stock.location"

    secupack_id = fields.Char(
        help=u'Hash interno de la plataforma'
    )
    default_courier_id = fields.Many2one(
        'varazdin_default.courier',
        'Transporte por defecto',
        help="Transporte que se usará para programar si se utiliza la opcion de transportes por defecto"
    )

    """
    "date":"2017-06-25T12:57:12.965Z",
    "courierId":"594ec96190d1872408e4b37f",  <- ID Interno de Trasportes
    "packTypeId":"594ec98490d1872408e4b380"	, <- ID Interno de paquetes
    "name":"NOMBRE DEL BAR",
    "code":	"TOMESTAMP DEBE SER UNIQUE",
    "address":"Direccion del bar",
    "notes" : "Si queres poner algun dato"	,
    "gpsmandatory":true,
    """

