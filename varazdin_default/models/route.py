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
from odoo.exceptions import Warning

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
    completed = fields.Boolean(
            help="El viaje está cerrado, se cargaron los movimientos de stock"
    )

    _sql_constraints = [
        ('date_location_courier', 'unique(date,location_id,courier_id)',
         u'Solo se permite a cada trasporte una entrega por dia'),
    ]

    @api.one
    def _get_name(self):
        self.name = self.date + '/' + self.location_id.name + '/' + self.courier_id.name

    @api.multi
    def do_get_secupack(self):
        print 'aaaaaaaaaaaa-aaaaaaaaaaaaaa-aaaaaaaaaaaaa-aaaaaaaaaaa'

        def prod2id(default_code):
            prod_id = self.env['product.product'].search([('default_code', '=', default_code)])
            if not prod_id:
                logger.error('bad product code %s', default_code)
            return prod_id

        def loc2id(location):
            source_id = self.env['stock.location'].search([('name', '=', location)])
            if not source_id:
                logger.error('bad source location %s', location)
            return source_id

        print 'ejecutando get secupack ----------------------------------'
        return
        for route in self:
            conf = self.env['varazdin_default.config.settings'].search([], order='id desc', limit=1)[0]
            client = SecupackClient(user=conf.default_user, password=conf.default_password)
            if client.logged():
                logger.info('getting courier #' + str(route.id))
                data = client.get_courier_by_code(route.id)
                print data
                """
                # traducir los codigos a id's
                source_id = loc2id(data['source'])
                dest_id = loc2id(data['dest'])
                moves = []
                for move in data[]:
                    moves.append(move)

                # hacer el movimiento programatico
                pickings = self.env['stock.picking']
                pickings.do_programatic_simple_transfer(self, source_id, dest_id, moves, obs)
                """
    @api.one
    def do_sync(self):
        print 'ejecutando do sync'
        conf = self.env['varazdin_default.config.settings'].search([], order='id desc', limit=1)[0]
        client = SecupackClient(user=conf.default_user, password=conf.default_password)

        print '>>>>>>>>>', self.date
        #        dt = datetime.strptime(self.date, '%Y-%m-%d').utcnow().isoformat
        if client.logged():
            data = {
                'date': self.date,
                'courierId': self.courier_id.secupack_id,  # <- ID Interno de Trasportes
                'packTypeId': conf.default_pack_type_id,  # <- ID Interno de paquetes
                'name': self.location_id.name,
                'code': str(self.id),
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
        last_sync = datetime.datetime.utcnow().isoformat()
        try:
            to_update = self.env['varazdin_default.route'].search(domain)
            for rec in to_update:
                rec.do_sync()

            # guardar la fecha de la última sincronización
            self.env['ir.config_parameter'].set_param("route.last.sync", last_sync)
        except:
            logger.error('Fallo la sincronizacion')
            raise

    @api.multi
    def get_secupack(self):
        """ Trae los paquetes de secupack y hace los movimientos de stock
        """
        logger.info('Ejecutando get_secupack')
        # obtener los viajes a consultar y traer los datos
        consult = self.search([('completed', '=', False)])
        for rec in consult:
            if rec.do_get_secupack():
                rec.completed = True


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

