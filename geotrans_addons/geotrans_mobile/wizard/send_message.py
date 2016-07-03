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
import time
from lxml import etree
from openerp.osv import fields, osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
import xlrd
import base64
import logging
import tempfile
from openerp.tools.translate import _
from openerp import tools
from openerp.tools.sql import drop_view_if_exists

_logger = logging.getLogger(__name__)


class wizard_sendmessage(osv.osv_memory):
    _name = 'wizard.sendmessage'
    _description = 'Enviar Mensaje'

    _columns = dict(
        wiz_tittle=fields.char(string='Título'),
        wiz_message=fields.text(string='Mensaje'),
        ps_ids=fields.many2many('gt.service.partner', string='Lista de Proveedores de Servicio'),
    )

    def send(self, cr, uid, ids, context=None):
        for wiz in self.browse(cr, uid, ids, context):
            notification = {
                "type": 1,
                "collapse_key": "Mensaje de T-Llevo",
                "title": wiz.wiz_tittle,
                "message": wiz.wiz_message,
            }
            ps_ids=[]
            for ps in wiz.ps_ids:
                ps_ids.append(ps.id)

            self.pool.get('gt.service.partner').action_send_message(cr, uid, ps_ids,notification,context)

        return True

    def notify_travel(self, cr, uid, ids, context=None):
        notification = {}
        travels = [('Junto a la cruz roja', 'Carlos Nolivos', 'Retirar documento', '-78.4863386', '-0.1861183'),
                   ('Catalina Aldaz', 'Carlos Nolivos', 'Retirar paquete', '-78.4791932', '-0.1824812'),
                   ('Camara de comercio', 'Carlos Nolivos', 'Retirar paquete', '-78.4863386', '-0.1861183')]
        for wiz in self.browse(cr, uid, ids, context):
            notification.update(
                {
                    'type': 2,
                    'collapse_key': "travel",
                    'title': "Nuevo Viaje Solicitado",
                    'message': "Cliente esperando PS",
                    'route': travels,
                    'km': "50",
                    'price': "25",
                    'service_types': "Documentos",
                }
            )
            ps_ids = []
            for ps in wiz.ps_ids:
                ps_ids.append(ps.id)
            self.pool.get('gt.service.partner').action_send_message(cr, uid, ps_ids, notification, context)
        return True

    def send_cash_balance(self, cr, uid, ids, context=None):
        notification = {}
        for wiz in self.browse(cr, uid, ids, context):
            notification.update(
                {
                    'type': 3,
                    'collapse_key': "cash_balance",
                    'title': "Saldo del proveedor de servicio",
                    'message': "Saldo del proveedor de servicio",
                    'cash_balance': "150.50",
                }
            )
            ps_ids = []
            for ps in wiz.ps_ids:
                ps_ids.append(ps.id)
            self.pool.get('gt.service.partner').action_send_message(cr, uid, ps_ids, notification, context)
        return True

    def send_total_penalty(self, cr, uid, ids, context=None):
        notification = {}
        for wiz in self.browse(cr, uid, ids, context):
            notification.update(
                {
                    'type': 4,
                    'collapse_key': "penalty",
                    'title': "Actualizando Multa",
                    'message': "Actualizando Multa",
                    'penalty': "50.50",
                }
            )
            ps_ids = []
            for ps in wiz.ps_ids:
                ps_ids.append(ps.id)
            self.pool.get('gt.service.partner').action_send_message(cr, uid, ps_ids, notification, context)
        return True

    def find_request(self, cr, uid, ids, context=None):
        notification = {}
        for wiz in self.browse(cr, uid, ids, context):
            notification.update(
                {
                    'type': 5,
                    'collapse_key': "find_request",
                    'title': "Encontro Ps",
                    'message': "Encontro Ps",
                }
            )
            ps_ids = []
            for ps in wiz.ps_ids:
                ps_ids.append(ps.id)
            self.pool.get('gt.service.partner').action_send_message(cr, uid, ps_ids, notification, context)
        return True

