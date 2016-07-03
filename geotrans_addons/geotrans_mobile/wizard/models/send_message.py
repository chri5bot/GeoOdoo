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
from openerp.osv import fields, osv, orm
import pytz
from datetime import datetime
from pytz import UTC
import openerp.tools as tools
import json
import logging
_logger = logging.getLogger(__name__)

_PARTNERTYPE = [('US', 'Usuario'), ('PS', 'Proveedor')]


class wizard_sendmessage(osv.osv_memory):
    _name = 'wizard.sendmessage'
    _description = 'Enviar Mensaje'

    _columns = dict(
        wiz_tittle=fields.char(string='Título'),
        wiz_message=fields.text(string='Mensaje'),
        ps_ids=fields.many2many('gt.service.partner', string='Lista de Proveedores de Servicio'),
        customer_ids=fields.many2many('gt.customer', string='Lista de Usuarios'),
        partnertype=fields.selection(_PARTNERTYPE, string='Elija el destinatario del mensaje', required=True,
                                     helpu=u'Elija el destinatario del mensaje Usuario/Proveedor')
    )

    _defaults = dict(
        partnertype='PS'
    )

    def to_openerp_date(self, cr, uid, dto_date):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        local_tz = pytz.timezone(user.partner_id.tz)
        fecha = datetime.strptime(dto_date, '%d/%m/%Y %H:%M:%S')
        fecha = local_tz.localize(fecha, is_dst=False)
        fecha = fecha.astimezone(UTC)
        return fecha.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)

    def send(self, cr, uid, ids, context=None):
        notify_obj = self.pool.get('gt.mobile.notify')
        for wiz in self.browse(cr, uid, ids, context):
            notification = {
                "type": 1,
                "collapse_key": "Mensaje de T-Llevo",
                "title": wiz.wiz_tittle,
                "message": wiz.wiz_message,
            }
            ps_ids = []
            customer_ids = []
            if wiz.partnertype == 'PS':
                for ps in wiz.ps_ids:
                    ps_ids.append(ps.id)
                    notify_values = {
                        'service_partner_id': ps.id,
                        'type': 'PS',
                        "title": wiz.wiz_tittle,
                        'message': wiz.wiz_message,
                        'date': self.to_openerp_date(cr, uid, datetime.now().strftime('%d/%m/%Y %H:%M:%S')),
                    }
                    notify_obj.create(cr, uid, notify_values)
                self.pool.get('gt.service.partner').action_send_message(cr, uid, ps_ids, notification, context)
            else:
                for customer in wiz.customer_ids:
                    customer_ids.append(customer.id)
                    notify_values = {
                        'customer_partner_id': customer.id,
                        'type': 'US',
                        "title": wiz.wiz_tittle,
                        'message': wiz.wiz_message,
                        'date': self.to_openerp_date(cr, uid, datetime.now().strftime('%d/%m/%Y %H:%M:%S')),
                    }
                    notify_obj.create(cr, uid, notify_values)
                self.pool.get('gt.customer').action_send_message(cr, uid, customer_ids, notification, context)
        return True

    def notify_travel(self, cr, uid, ids, context=None):
        notification = {}
        travels = [('Junto a la cruz roja', 'Carlos Nolivos', 'Retirar documento', '-78.4863386', '-0.1861183'),
                   ('Catalina Aldaz', 'Carlos Nolivos', 'Retirar paquete', '-78.4791932', '-0.1824812'),
                   ('Camara de comercio', 'Carlos Nolivos', 'Retirar paquete', '-78.4863386', '-0.1861183')]
        for wiz in self.browse(cr, uid, ids, context):
            notification.update(
                {
                    'Type': 2,
                    'CollapseKey': "travel",
                    'Title': "Nuevo Viaje Solicitado",
                    'Message': "Cliente esperando PS",
                    'Route': travels,
                    'Kilometers': "5000",
                    'Price': "25",
                    'ServiceTypes': "Documentos",
                }
            )
            ps_ids = []
            for ps in wiz.ps_ids:
                ps_ids.append(ps.id)
            self.pool.get('gt.service.partner').action_send_message(cr, uid, ps_ids, notification, context)
        return True

    def notify_travel2(self, cr, uid, ids, context=None):
        for wiz in self.browse(cr, uid, ids, context):
            route_obj = self.pool.get('gt.route')
            route_obj.mobile_confirmroute(cr, uid, int(wiz.wiz_tittle))
        return True

    def send_cash_balance(self, cr, uid, ids, context=None):
        notification = {}
        for wiz in self.browse(cr, uid, ids, context):
            notification.update(
                {
                    'Type': 3,
                    'CollapseKey': "cash_balance",
                    'Title': "Saldo del proveedor de servicio",
                    'Message': "Saldo del proveedor de servicio",
                    'CashBalance': "150.50",
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
                    'Type': 4,
                    'CollapseKey': "penalty",
                    'Title': "Actualizando Multa",
                    'Message': "Actualizando Multa",
                    'Penalty': "50.50",
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
                    'Type': 5,
                    'CollapseKey': "find_request",
                    'Title': "Encontro Ps",
                    'Message': "Encontro Ps",
                }
            )
            ps_ids = []
            for ps in wiz.ps_ids:
                ps_ids.append(ps.id)
            self.pool.get('gt.service.partner').action_send_message(cr, uid, ps_ids, notification, context)
        return True
    #VERIFICAR FUNCIONALIDAD
    def sendCustomer(self, cr, uid, ids, context=None):
        notify_obj = self.pool.get('gt.mobile.notify')
        for wiz in self.browse(cr, uid, ids, context):
            notification = {
                "type": 1,
                "collapse_key": "Mensaje de T-Llevo",
                "title": wiz.wiz_tittle,
                "message": wiz.wiz_message,
            }
            customer_ids = []
            for customer in wiz.customer_ids:
                customer_ids.append(customer.id)
                notify_values = {
                    'customer_partner_id': customer.id,
                    'type': 'US',
                    "title": wiz.wiz_tittle,
                    'message': wiz.wiz_message,
                    'date': self.to_openerp_date(cr, uid, datetime.now().strftime('%d/%m/%Y %H:%M:%S')),
                }
                notify_obj.create(cr, uid, notify_values)

            self.pool.get('gt.customer').action_send_message(cr, uid, customer_ids, notification, context)
        return True
