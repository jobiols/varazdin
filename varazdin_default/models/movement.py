from odoo import api, fields, models

class Movement(models.Model):
    _name = 'varazdin_default.movement'
    _description = 'Movimientos de stock'
    
    action = fields.Selection([
              ('deja', 'deja'),
              ('retira', 'retira') ])
    quantity = fields.Integer(
    )
    type_id = fields.Many2one(
        'product.product'
    )
    route_id = fields.Many2one(
        'varazdin_default.route'
    (

