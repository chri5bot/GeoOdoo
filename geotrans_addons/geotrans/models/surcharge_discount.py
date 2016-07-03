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

_DAYWEEK = [('0', 'Lunes'), ('1', 'Martes'),('2', 'Miercoles'),
            ('3', 'Jueves'), ('4', 'Viernes'), ('5', 'Sabado'),
            ('6', 'Domingo')]
_TYPE = [('date', 'Por Fechas'), ('day', 'Por día de la semana'),]


class SurchargeDiscount(osv.osv):
    _name = 'gt.surcharge.discount'
    _description = 'Recargo Descuento'

    _columns = dict(
        sd_id=fields.many2one('gt.service.configuration', string='Configuración Servicio',
                              help="Seleccione a la configuración que pertenece"),
        type=fields.selection(_TYPE, string='Criterio de aplicación', help=u'Seleccione el criterio de aplicación sobre la tarifa original'),
        priority=fields.integer(string='Orden', help=u'Número de orden'),
        value_sd=fields.float(string='Porcentaje', help=u'Porcentaje del Recargo/Descuento'),
        date_begin=fields.date(string='Fecha Inicio', help=u'Fecha inicio del Recargo/Descuento'),
        date_end=fields.date(string='Fecha Fin', help=u'Fecha fin del Recargo/Descuento'),
        day=fields.selection(_DAYWEEK, string='Día de la semana', help=u'Seleccione el día de la semana'),

    )

    _order = "priority asc"