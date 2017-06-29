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
import logging

from odoo import api, fields, models
from odoo.addons.varazdin_default.secupack_lib.secupack import SecupackClient

logger = logging.getLogger(__name__)


class Route(models.Model):
    _name = 'varazdin_default.route'
    _description = 'Rutas'

    name = fields.Char(
            compute="_get_name",
            store=True
    )
    secupack_ans = fields.Char(
            help=u'Respuesta de la plataforma'
    )
    date = fields.Date(
            'Fecha',
            help='Fecha en la que hace el recorrido',
            required=True
    )
    location_id = fields.Many2one(
            'stock.location',
            'Ubicacion',
            help='Ubicacion a vistiar en esta fecha',
            required=True
    )
    courier_id = fields.Many2one(
            'varazdin_default.courier',
            'Transporte',
            help='Transporte que realiza la visita',
            required=True
    )

    @api.one
    def _get_name(self):
        self.name = self.date + '/' + self.location_id.name + '/' + self.courier_id.name

    @api.one
    def do_sync(self):
        print 'ejecutando do sync'
        conf = self.env['varazdin_default.config.settings'].search([], order='id desc', limit=1)[0]
        client = SecupackClient(user=conf.default_user, password=conf.default_password)
        if client.logged():
            data = {
                'date': self.date,
                'courierId': self.courier_id.secupack_id,  # <- ID Interno de Trasportes
                'packTypeId': conf.default_pack_type_id,  # <- ID Interno de paquetes
                'name': self.location_id.name,
                'code': fields.Datetime.now()+str(self.id),
                'address': self.location_id.partner_id.street if self.location_id.partner_id else False,
                'gpsmandatory': False,
            }
            print '------------------'
            print data
            self.secupack_ans = client.set_courier_package(data=data)

    @api.multi
    def sync(self):
        """ Sincroniza el modelo con la plataforma, corre cada tanto
            lanzado por las acciones planificadas
        """
        logger.info('Ejecutando sync')
        print '-------------------------------------------------------------------'

        # obtener la fecha de la última sincronizacion
        last_sync = self.env['ir.config_parameter'].get_param("route.last.sync")
        # obtener todos los registros a actualizar
        domain = [('write_date', '>', last_sync)] if last_sync else []
        last_sync = fields.Datetime.now()
        try:
            to_update = self.env['varazdin_default.route'].search(domain)
            for rec in to_update:
                rec.do_sync()

            # guardar la fecha de la última sincronizacion
            self.env['ir.config_parameter'].set_param("route.last.sync", last_sync)
        except:
            logger.error('Fallo la sincronizacion')
            raise
