# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2016 Tandicorp - http://www.tandicorp.com/
#    All Rights Reserved.
#
############################################################################
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
##############################################################################
from openerp.osv import fields, osv

_CHAT_TYPE = [('PS', 'Proveedor'), ('US', 'Usuario')]


class ChatLine(osv.osv):
    _name = 'gt.chat.line'
    _description = 'Lineas de chat'

    _columns = dict(
        route_id=fields.many2one('gt.route', string='Ruta', help=u'Ruta'),
        type=fields.selection(_CHAT_TYPE, string='Tipo', readonly=False, help=u'Quien escribio el mensaje'),
        service_partner_id=fields.many2one('gt.service.partner', string='Proveedor de Servicio'),
        message=fields.text(string='Mensaje', readonly=False,
                            help=u'Indica el mensajes de texto de ésta linea de chat'),
        date=fields.datetime(string='Fecha', readonly=False),
    )
