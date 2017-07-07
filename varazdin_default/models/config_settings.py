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

# tutorial
# http://ludwiktrammer.github.io/odoo/custom-settings-odoo.html


class AppSettings(models.TransientModel):
    _name = 'varazdin_default.config.settings'
    _inherit = 'res.config.settings'

    @api.model
    def default_get(self, fields):
        res = super(AppSettings, self).default_get(fields)
        return res

    user = fields.Char(
            help='Usuario de acceso a la plataforma',
            default_model='varazdin_default.config.settings'
    )

    password = fields.Char(
            help='Contraseña de acceso a la plataforma',
            default_model='varazdin_default.config.settings'
    )

    pack_type_id = fields.Char(
            help='Identificador de tarea de la plataforma',
            default_model='varazdin_default.config.settings'
    )

    company_id = fields.Many2one(
            'res.company', 'Company',
            default=lambda self: self.env.user.company_id, required=True)

    @api.one
    def set_user(self):
        self.env['ir.config_parameter'].set_param('user', self.user or '')

    @api.one
    def get_user(self, fields):
        self.user = self.env['ir.config_parameter'].get_param('user', default=False)

    @api.one
    def set_password(self):
        self.env['ir.config_parameter'].set_param('password', self.password or '')

    @api.one
    def get_password(self, fields):
        self.password = self.env['ir.config_parameter'].get_param('password', default=False)

    @api.one
    def set_pack_type_id(self):
        self.env['ir.config_parameter'].set_param('pack_type_id', self.pack_type_id or '')

    @api.one
    def get_pack_type_id(self, fields):
        self.pack_type_id = self.env['ir.config_parameter'].get_param('pack_type_id', default=False)

    @api.one
    def test_connection(self):
        client = SecupackClient(user=self.user, password=self.password)
        if client.logged():
            raise Warning(u'Conexión exitosa')
        else:
            raise Warning(u'Falló la conexión')
