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


class AccountJournal(orm.Model):
    _name = "account.journal"
    _inherit = 'account.journal'
    _columns = {
        'integration_payment': fields.boolean('Es cobro electrónico',
                                              help=u'Este diario sirve para cobros mediante integraciones?'),
        'integration_partner': fields.many2one('res.partner', string='Proveedor de Integracion',
                                               help=u'Si el diario sirve para cobros mediante integraciones. \n\r'
                                                    u'Este es el proveedor de integración, usado para contabilizacion de pagos')
    }

