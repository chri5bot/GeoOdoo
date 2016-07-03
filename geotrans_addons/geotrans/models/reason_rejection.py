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
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
from validate_email import validate_email
import re


class RouteRejection(osv.osv):
    _name = 'gt.route.rejection'
    _description = 'Rechazo de Rutas'

    _columns = dict(
        service_partner_id=fields.many2one('gt.service.partner', string='Proveedor de Servicio', readonly=True),
        reason_id=fields.many2one('gt.reason', string='Motivo del rechazo', readonly=True),
        route_id=fields.many2one('gt.route', string='Ruta', help=u'Ruta'),
        support=fields.boolean('Relevo', help=u'Relevo de proveedor de servicio'),
        date=fields.datetime(string='Fecha', readonly=True),
    )

    _defaults = dict(
        date=fields.datetime.now,
    )

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = "rejection [" + str(obj.id) + "]"
        return result.items()


class Reason(osv.osv):
    _name = 'gt.reason'
    _description = 'Tipos de rechazo'

    _columns = dict(
        code=fields.char(string='Codigo', required=True, size=16, help=u'Codigo Tipo de rechazo'),
        name=fields.char('Razón Rechazo', size=64, required=True, help=u'Descripción Tipo de rechazo'),
        active=fields.boolean('Activo', help=u'Indica si el Tipo de rechazo se encuentra activo')
    )

    def get_active_reasons(self, cr, uid, context=None):
        reasontypes = {}
        reason_object_ids = self.search(cr, uid, [('active', '=', 'True')])
        reason = self.browse(cr, uid, reason_object_ids)
        for reason_type in reason:
            reasontypes.update(
                {
                    reason_type.code: reason_type.name,
                }
            )
        return reasontypes
