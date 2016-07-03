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
import time
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
from base_geoengine import geo_model
from geotrans import *

_STATE = [('entered', 'Ingresada'), ('confirmed', 'Confirmada'),
          ('invoiced', 'Facturada'), ('canceled', 'Anulada')]


class Penalty_Application(osv.osv):
    _name = 'gt.penalty.application'
    _description = 'Aplicacion Multas'

    def _get_price(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        for r in self.browse(cr, uid, ids, context=context):
            if r.penalty_id.product_id and r.penalty_id.product_id.product_tmpl_id and r.penalty_id.product_id.product_tmpl_id.list_price:
                result[r.id] = r.penalty_id.product_id.product_tmpl_id.list_price
            else:
                result[r.id] = 0.0
        return result

    _columns = dict(
        penalty_id=fields.many2one('gt.penalty', string='Aplicación de Multa', required=True),
        penalty_partner_id=fields.many2one('gt.service.partner', string='Proveedor de Servicio', required=True),
        value=fields.function(_get_price, method=True, type='float', string='Valor', help=u'Valor de la multa'),
        state=fields.selection(_STATE, string='Estado de la multa', readonly=True, track_visibility='onchange',
                               help=u'Estado de la multa'),
        date=fields.datetime(string='Fecha del incidente', readonly=False),
    )

    _defaults = dict(
        state='entered',
        date=fields.datetime.now,
    )

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False):
        res = super(Penalty_Application, self).read_group(cr, uid, domain, fields, groupby, offset, limit=limit, context=context, orderby=orderby)
        if 'value' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(cr, uid, line['__domain'], context=context)
                    valor = 0.0
                    for pa in self.browse(cr, uid, lines, context=context):
                        valor += pa.value
                    line['value'] = valor
        return res

    def act_invoice(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'invoiced'}, context)
        return True

    def act_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'canceled'}, context)
        return True

    def act_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'}, context)
        return True

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for appli in self.browse(cr, uid, ids, context=context):
            result[appli.id] = u"["+appli.penalty_id.name+u"] "+appli.penalty_partner_id.name_get()[0][1]
        return result.items()


class Penalty(osv.osv):
    _name = 'gt.penalty'
    _description = 'Multas'

    _columns = dict(
        name=fields.char('Código', size=8, required=True, help=u'Código de la multa'),
        description=fields.text('Descripción de la multa', size=5000, help=u'Descripción de la multa'),
        product_id=fields.many2one('product.product', string='Ítem para facturación', required=True),

    )

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for penalty in self.browse(cr, uid, ids, context=context):
            result[penalty.id] = penalty.name + " - " + penalty.description
        return result.items()

