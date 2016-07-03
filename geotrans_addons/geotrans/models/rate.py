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
from base_geoengine import geo_model
from geotrans import *

_RATETYPES = [('day', 'Diurno'),('night','Nocturno'),('wait','Espera'),('base','Mínima')]

class ServiceRate(osv.osv):
    _name = 'gt.rate'
    _description = 'Tarifas de Servicio'

    _columns = dict(
        value_rate=fields.float('Valor Tarifa usuario', required=True, help=u'Valor de la tarifa para el usuario final'),
        value_rate_internal=fields.float('Valor Tarifa para PS', required=True, help=u'Valor de la tarifa para PS'),
        rate_type=fields.selection(_RATETYPES, string='Tarifas Vigentes',required=True, help=u'Tarifas vigentes'),
    )

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for rate in self.browse(cr, uid, ids, context=context):
                if rate.rate_type:
                    name=''
                    for i in _RATETYPES:
                        if rate.rate_type ==  i[0]:
                            name= i[1]
                    result[rate.id] =  "Tarifa "+str(name)+"  [$ "+str(rate.value_rate)+"]"
                else:
                    result[rate.id] = "Tarifa [$ " + str(rate.value_rate) + "]"
        return result.items()
