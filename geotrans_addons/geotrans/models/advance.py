# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2010 moylop260 - http://www.hesatecnica.com.com/
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

_ADVANCESTATES = [('requested', 'Solicitada'), ('approved', 'Aprovada'), ('invoiced', 'Facturada')]


class AdvanceReason(osv.osv):
    _name = 'gt.advance.reason'
    _description = 'Motivo del Anticipo'

    _columns = dict(
        name=fields.integer('Código', required=True, help=u'Código del motivo'),
        description=fields.text('Descripción', required=True, size=80, help=u'Descripción del motivo'),
    )


class Advance(osv.osv):
    _name = 'gt.advance'
    _description = 'Solicitud del Anticipo'

    _columns = dict(
        advance_reason=fields.many2one('gt.advance.reason', string='Motivo Solicitud',
                                       help=u'Motivo de solicitud del anticipo'),
        state=fields.selection(_ADVANCESTATES, string='Estado Solicitud', help=u'Estado actual de la solicitud'),
        request_date=fields.date('Fecha Solicitud', required=True,help=u'Fecha de solicitud del anticipo'),
        description=fields.text('Descripción', required=True, size=80,
                                help=u'Indique una descripción de afirmación o negación de pedido')
    )
    _defaults = dict(
        state='requested'
    )
