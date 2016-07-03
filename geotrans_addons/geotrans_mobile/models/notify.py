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
import logging

_logger = logging.getLogger(__name__)

_NOTIFY_TYPE = [('PS', 'proveedor'), ('US', 'usuario')]


class MobileNotify(osv.osv):
    _name = 'gt.mobile.notify'
    _description = 'Notificaciones'
    _columns = dict(
        date=fields.datetime('Fecha Mensaje', required=True, help=u'Fecha de envio del mensaje'),
        type=fields.selection(_NOTIFY_TYPE, 'Tipo Mensaje', readonly=False, track_visibility='onchange',
                               help=u'Estado actual de la ruta'),
        customer_partner_id=fields.many2one('gt.customer', string='Cliente',
                                            help=u'Cliente que recibe el mensaje'),
        service_partner_id=fields.many2one('gt.service.partner', string='Proveedor de Servicio',
                                            help=u'PS que recibe el mensaje'),
        title=fields.char(string='Título', readonly=False, help=u'Indica el título de la notificación'),
        message=fields.text(string='Mensaje', readonly=False, help=u'Indica el mensaje de la notificación'),
    )


