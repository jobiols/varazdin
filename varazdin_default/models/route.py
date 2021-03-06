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
import datetime
import logging

from odoo import api, fields, models
from odoo.addons.varazdin_default.secupack_lib.secupack import SecupackClient
from odoo.exceptions import Warning

logger = logging.getLogger(__name__)


# receta 594e853c0d8d08609f9b9f3d

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
    secupack_recv = fields.Char(
            'Recibido',
            help='Flag de info recibida'
    )
    secupack_obs = fields.Char(
            help='Observaciones'
    )
    #    movement_ids = fields.One2many(
    #            'varazdin_default.movement',
    #            'route_id',
    #            help='Movimientos de stock'
    #    )

    _sql_constraints = [
        ('date_location_courier', 'unique(date,location_id,courier_id)',
         u'Solo se permite a cada trasporte una entrega por dia'),
    ]

    @api.one
    def _get_name(self):
        self.name = self.date + '/' + self.location_id.name + '/' + self.courier_id.name

    @api.one
    def do_sync(self):
        logger.info('========== sincronizando rutas')

        user = self.env['ir.config_parameter'].get_param('user', 'demo_user')
        password = self.env['ir.config_parameter'].get_param('password', 'pwd')
        pack_type_id = self.env['ir.config_parameter'].get_param('pack_type_id', 'pwd')
        client = SecupackClient(user=user, password=password)

        notes = ' '
        for contact in self.location_id.partner_id.child_ids:
            notes = contact.name + (
            ' - ' + contact.phone if contact.phone else ' - ' + contact.mobile if contact.mobile else ' ')
            break

        if client.logged():
            data = {
                'date': self.date + 'T12:00:00.000000',  # poner las doce del mediodia
                'courierId': self.courier_id.secupack_id,  # <- ID Interno de Trasportes
                'packTypeId': pack_type_id,   # <- ID Interno de paquetes
                'name': self.location_id.name,
                'code': user + '-' + str(self.id),
                'address': self.location_id.partner_id.street if self.location_id.partner_id else ' ',
                'gpsmandatory': False,
                'notes': notes
            }

            self.secupack_ans = str(self.id) + ' ' + client.set_courier_package(data=data)
            logger.info('================>' + str(self.id) + ' ' + self.secupack_ans)

    @api.multi
    def sync(self):
        """ Sincroniza el modelo con la plataforma, corre cada tanto
            lanzado por las acciones planificadas
        """
        logger.info('========== Testeando sincronizacion de rutas')

        # obtener la fecha de la última sincronizacion de envio de paquetes
        last_sync = self.env['ir.config_parameter'].get_param("route.last.sync")

        # ,('date', '=', datetime.date.today().isoformat())
        # obtener todos los registros a subir
        domain = [('write_date', '>', last_sync),
                  ('secupack_ans', '=', False)] if last_sync else []
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

        # obtener todos los registros a bajar ,
        domain = [('secupack_ans', '!=', False),
                  ('secupack_recv', '=', False),
                  ('date', '=', datetime.date.today().isoformat())]
        try:
            to_download = self.env['varazdin_default.route'].search(domain)
            for rec in to_download:
                rec.do_download()
        except:
            logger.error('Fallo la bajada de datos')
            raise

    @api.one
    def do_download(self):
        def get_delivery(lista):
            ret = ' '
            for element in lista:
                if element['description'] == 'Observacion':
                    ret = element['value']
            return ret

        user = self.env['ir.config_parameter'].get_param('user', 'demo_user')
        password = self.env['ir.config_parameter'].get_param('password', 'pwd')
        client = SecupackClient(user=user, password=password)

        if client.logged():
            data = client.get_package_by_code(user + '-' + str(self.id))
            pack = data.get('pack', False)
            if pack:
                completed = pack.get('completed', 'False')
                if completed:
                    logger.info('================================ downloading data')
                    self.secupack_recv = 'Ok-' + str(self.id)
                    self.secupack_obs = get_delivery(pack.get('delivery', False))
                    actions = pack.get('actions', False)
                    for act in actions:
                        value = act.get('value', False)
                        if value is not None:
                            for val in value:
                                print '===== datos que vienen de la plataforma', val
                                act = val.get('action', False)  # deja o retira
                                cajas = int(val.get('cnt', False))  # cantidad de cajas
                                default_code = val.get('tipo', False)  # producto

                                # deja en la ubicacion movimiento barazdin -> ubicacion
                                if act == 'deja':
                                    source_id = self.env['stock.location'].search([('name', '=', 'Varazdin')])
                                    dest_id = self.location_id

                                # retira de la ubicacion movimiento ubicacion -> barazdin
                                if act == 'retira':
                                    source_id = self.location_id
                                    dest_id = self.env['stock.location'].search([('name', '=', 'Varazdin')])

                                prod_id = self.env['product.product'].search([('default_code', '=', default_code)])
                                if prod_id:
                                    moves = [{
                                        'prod_id': prod_id,
                                        'qty': cajas * prod_id.vasos_x_caja
                                    }]
                                    movement = self.env['stock.picking']
                                    movement.do_programatic_simple_transfer(source_id, dest_id, moves, ' ')


class CreateRoute(models.TransientModel):
    _name = 'varazdin_default.generate_route'

    select = fields.Selection([
        (0, 'Todos los transportes van a todas las ubicaciones'),
        (1, 'Los transportes van a las ubicacines por defecto')
    ], "Seleccionar operacion"
    )
    date = fields.Date(
            u'Fecha de programación',
            required="True"
    )

    @api.multi
    def execute(self):
        """ Todos contra todos """
        if self.select == 0:
            couriers = self.env['varazdin_default.courier'].search([])
            locations = self.env['stock.location'].search([('usage', '=', 'internal')])
            routes = self.env['varazdin_default.route']
            for loc in locations:
                # No programamos la ubicacion Varazdin
                if loc.name == 'Varazdin':
                    continue
                for cour in couriers:
                    routes.create({
                        'date': self.date,
                        'location_id': loc.id,
                        'courier_id': cour.id
                    })

        """ cargar los couriers con destinos por defecto """
        if self.select == 1:

            couriers = self.env['varazdin_default.courier'].search([])
            locations = self.env['stock.location'].search([('usage', '=', 'internal')])
            routes = self.env['varazdin_default.route']
            # verificar defaults
            for loc in locations:
                if not loc.default_courier_id:
                    raise Warning('Todas las ubicaciones deben tener un transporte por defecto')

            for loc in locations:
                routes.create({
                    'date': self.date,
                    'location_id': loc.id,
                    'courier_id': loc.default_courier_id.id
                })
