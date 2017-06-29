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

from odoo import fields, models, api
from odoo.addons.varazdin_default.secupack_lib.secupack import SecupackClient

logger = logging.getLogger(__name__)


class Courier(models.Model):
    _name = 'varazdin_default.courier'
    _description = "Couriers"

    secupack_id = fields.Char(
            help=u'Hash interno de la plataforma'
    )
    name = fields.Char(
            help=u'Dominio del vehículo',
            string=u'Dominio',
            required=True,
            index=True
    )
    user = fields.Char(
            help=u'Usuario de la app android / ios',
            string=u'Usuario'
    )
    active = fields.Boolean(
            help=u'Indica si el usuario está activo',
            string='Activo',
            default=True
    )

    @api.one
    def do_sync(self):
        print 'ejecutando do sync'
        conf = self.env['varazdin_default.config.settings'].search([], order='id desc', limit=1)[0]
        client = SecupackClient(user=conf.default_user, password=conf.default_password, debug=True)
        if client.logged():
            print 'logged!!!!!!!!!!!!!!!!!---'
            data = {
                'denomination': self.name,
                'user': self.user,
                'active': self.active
            }
            print 'esta es mi data', data
            # hacer alta o modificación según tenga o no el id
            print 'este es secupack', self.secupack_id
            if self.secupack_id:
                print 'modificacion--'
                a = client.set_courier(data=data, id=self.secupack_id)
            else:
                print 'alta --- '
                self.secupack_id = client.set_courier(data=data)

    @api.multi
    def sync(self):
        """ Sincroniza el modelo con la plataforma, corre cada tanto
            lanzado por las acciones planificadas
        """
        logger.info(u'Ejecutando sync')
        print '----------------------------SYNC---------------------------------------'

        # obtener la fecha de la última sincronizacion
        last_sync = self.env['ir.config_parameter'].get_param("courier.last.sync")
        # obtener todos los registros a actualizar
        domain = [('write_date', '>', last_sync)] if last_sync else []
        last_sync = fields.Datetime.now()

        try:
            to_update = self.env['varazdin_default.courier'].search(domain)
            for rec in to_update:
                rec.do_sync()

            # guardar la fecha de la última sincronizacion
            self.env['ir.config_parameter'].set_param("courier.last.sync", last_sync)
        except:
            raise
            logger.error(u'Fallo la sincronizacion')
