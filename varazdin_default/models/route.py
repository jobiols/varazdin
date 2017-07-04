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
            help='Flag de info recibida'
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
        logger.info('========== sync rutas')
        conf = self.env['varazdin_default.config.settings'].search([], order='id desc', limit=1)[0]
        client = SecupackClient(user=conf.default_user, password=conf.default_password)

        notes = ' '
        for contact in self.location_id.partner_id.child_ids:
            notes = contact.name + (' - '+contact.phone if contact.phone else ' - '+contact.mobile if contact.mobile else ' ')
            break

        if client.logged():
            data = {
                'date': self.date,
                'courierId': self.courier_id.secupack_id,  # <- ID Interno de Trasportes
                'packTypeId': conf.default_pack_type_id,  # <- ID Interno de paquetes
                'name': self.location_id.name,
                'code': conf.default_user + '-' + str(self.id),
                'address': self.location_id.partner_id.street if self.location_id.partner_id else ' ',
                'gpsmandatory': False,
                'notes': notes
            }
            self.secupack_ans = client.set_courier_package(data=data)
            logger.info('================>' + self.secupack_ans)

    @api.multi
    def sync(self):
        """ Sincroniza el modelo con la plataforma, corre cada tanto
            lanzado por las acciones planificadas
        """
        logger.info('========== testeando sincronizacion de rutas')
        print '----------------------------SYNC RUTAS---------------------------'


        # obtener la fecha de la última sincronizacion de envio de paquetes
        last_sync = self.env['ir.config_parameter'].get_param("route.last.sync")

        # obtener todos los registros a subir
        domain = [('write_date', '>', last_sync), ('secupack_ans', '=', False)] if last_sync else []
        last_sync = fields.Datetime.now()  # datetime.datetime.utcnow().isoformat()
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
        domain = [('secupack_ans', '!=', False), ('secupack_recv', '=', False)]
        print 'dominio de los registros a bajar', domain
        try:
            to_download = self.env['varazdin_default.route'].search(domain)
            print 'to download',len(to_download)
            for rec in to_download:
                rec.do_download()
        except:
            logger.error('Fallo la bajada de datos')
            raise

    @api.one
    def do_download(self):
        logger.info('================================ downloading data')
        conf = self.env['varazdin_default.config.settings'].search([], order='id desc', limit=1)[0]
        client = SecupackClient(user=conf.default_user, password=conf.default_password)

        if client.logged():
            data = client.get_package_by_code(conf.default_user + '-' + str(self.id))
            print '------------------------------------OBTENIENDO INFO ----------------------------------'

            pack = data.get('pack', False)
            if pack:
                completed = pack.get('completed', 'False')
                if completed:
                    print 'paquete completo--'
                    self.secupack_recv = 'Completado'
                    actions = pack.get('actions', False)
                    for act in actions:
                        value = act.get('value', False)
                        for val in value:
                            print 'datos que vienen de la plataforma', val
                            act = val.get('action', False)  # deja o retira
                            cnt = int(val.get('cnt', False)) * conf.default_vasosxcaja  # cantidad de cajas X vasos x caja
                            default_code = val.get('tipo', False)   # producto
                            print 'de vuelta los datos', act, cnt, default_code
                            """
                            movement = self.env['varazdin_default.movement'].create({
                                action: act,
                                quantity:2,
                                type_id:3,
                            })
                            """
                            # deja en la ubicacion movimiento barazdin -> ubicacion
                            if act == 'deja':
                                source_id = self.env['stock.location'].search([('name', '=', 'Varazdin')])
                                dest_id = self.location_id

                            # retira de la ubicacion movimiento ubicacion -> barazdin
                            if act == 'retira':
                                source_id = self.location_id
                                dest_id = self.env['stock.location'].search([('name', '=', 'Varazdin')])

                            print 'source', source_id, 'destino', dest_id

                            prod_id = self.env['product.product'].search([('default_code', '=', default_code)])
                            if prod_id:
                                moves = [{
                                    'prod_id': prod_id,
                                    'qty': cnt
                                }]
                                print 'moves', moves[0]

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
                for cour in couriers:
                    print 'creando rutas'
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
                print 'creando rutas'
                routes.create({
                    'date': self.date,
                    'location_id': loc.id,
                    'courier_id': loc.default_courier_id.id
                })
