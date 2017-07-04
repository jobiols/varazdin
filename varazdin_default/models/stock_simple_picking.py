# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    simple_qty = fields.Float('Cantidad', compute='_get_simple_qty')

    @api.multi
    def test_move(self):
        logger.info('New TEST Move')

        source = 'varazdin'
        dest = 'La Vasca'
        obs = 'ADK-FFD-888*-'

        moves = []
        default_code = 'V1'
        prod_id = self.env['product.product'].search([('default_code', '=', default_code)])
        if not prod_id:
            logger.error('bad product code %s', default_code)
        moves.append({
            'prod_id': prod_id,
            'qty': 34
        })

        default_code = 'V100'
        prod_id = self.env['product.product'].search([('default_code', '=', default_code)])
        if not prod_id:
            logger.error('bad product code %s', default_code)
        moves.append({
            'prod_id': prod_id,
            'qty': 200
        })

        source_id = self.env['stock.location'].search([('name', '=', source)])
        if not source_id:
            logger.error('bad source location %s', source)

        dest_id = self.env['stock.location'].search([('name', '=', dest)])
        if not source_id:
            logger.error('bad destination location %s', dest)
        self.do_programatic_simple_transfer(source_id, dest_id, moves, obs)

    @api.multi
    def do_programatic_simple_transfer(self, source_id, dest_id, moves, obs):
        # crear el picking
        pick = self.create({
            'name': self.env['ir.sequence'].next_by_code('varazdin.move'),
            'location_id': source_id.id,
            'location_dest_id': dest_id.id,
            'min_date': fields.Datetime.now(),
            'origin': obs,
            'move_type': 'one',
            'picking_type_id': 5
        })

        for move in moves:
            logger.info('== MOVIMIENTO == source %s, dest %s, prod %s, qty %s, %s',
                        source_id.name,
                        dest_id.name,
                        move['prod_id'].name,
                        str(move['qty']),
                        obs)

            pick.pack_operation_ids.create({
                'product_uom_id': move['prod_id'].uom_id.id,
                'picking_id': pick.id,
                'product_id': move['prod_id'].id,
                'product_qty': move['qty'],
                'qty_done': move['qty'],
                'date': fields.Datetime.now(),
                'location_id': source_id.id,
                'location_dest_id': dest_id.id,
            })

        # crear el inmediate transfer
        wiz = self.env['stock.immediate.transfer'].create({'pick_id': pick.id})
        # If still in draft => confirm and assign

        if wiz.pick_id.state == 'draft':
            wiz.pick_id.action_confirm()

            if wiz.pick_id.state != 'assigned':
                wiz.pick_id.action_assign()
                if wiz.pick_id.state != 'assigned':
                    raise UserError(_(
                            "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))

        for pack in wiz.pick_id.pack_operation_ids:
            if pack.product_qty > 0:
                pack.write({'qty_done': pack.product_qty})
            else:
                pack.unlink()

        wiz.pick_id.do_transfer()

    @api.multi
    def do_new_simple_transfer(self):

        for pick in self:
            pack_operations_delete = self.env['stock.pack.operation']
            if not pick.move_lines and not pick.pack_operation_ids:
                raise UserError(('Por favor ingrese productos y cantidades a transferir.'))

            # este chequeo pasa bien, se podría sacar, pickking type es transferencias internas.
            # In draft or with no pack operations edited yet, ask if we can just do everything
            if pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                # If no lots when needed, raise error
                picking_type = pick.picking_type_id
                if (picking_type.use_create_lots or picking_type.use_existing_lots):
                    for pack in pick.pack_operation_ids:
                        if pack.product_id and pack.product_id.tracking != 'none':
                            raise UserError(
                                    _('Some products require lots/serial numbers, so you need to specify those first!'))

                view = self.env.ref('stock.view_immediate_transfer')
                wiz = self.env['stock.immediate.transfer'].create({'pick_id': pick.id})

                # If still in draft => confirm and assign
                if wiz.pick_id.state == 'draft':
                    wiz.pick_id.action_confirm()

                    if wiz.pick_id.state != 'assigned':
                        wiz.pick_id.action_assign()
                        if wiz.pick_id.state != 'assigned':
                            raise UserError(_(
                                    "Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))

                for pack in wiz.pick_id.pack_operation_ids:
                    if pack.product_qty > 0:
                        pack.write({'qty_done': pack.product_qty})
                    else:
                        pack.unlink()
                wiz.pick_id.do_transfer()

            return

        print 'antes de do transfer >>>>>>>>>>>>>>>>>>>>>>'
        self.do_transfer()
        return
