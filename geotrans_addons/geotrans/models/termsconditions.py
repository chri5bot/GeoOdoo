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

_STATETERMS = [('active', 'Activo'), ('inactive', 'Inactivo')]


class TermsConditionsPs(osv.osv):
    _name = 'gt.termsconditions.ps'
    _description = 'Terminos y Condiciones Ps'

    _columns = dict(
        id=fields.integer(readonly=True, help=u'Versión de los términos y condiciones'),
        terms_conditions=fields.text('Términos y Condiciones Ps', size=8000, help=u'Ingrese los términos y condiciones del Ps'),
        state=fields.selection(_STATETERMS, 'Estado términos y condiciones', readonly=True, track_visibility='onchange', help=u'Estado términos y condiciones'),
        date_active=fields.char('Fecha activación', size=32, readonly=True, help=u'Fecha de activación de los términos y condiciones'),
        #diferenciar splashart para clientes y proveedores
    )

    _defaults = dict(
        state='inactive'
    )

    def act_active(self, cr, uid, ids, context=None):
        date = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        cr.execute("update gt_termsconditions_ps set state='inactive'")
        self.write(cr, uid, ids, {'state': 'active', 'date_active': date}, context)
        cr.execute("update gt_service_partner "
                   "set confirm_terms_conditions='False', "
                   "terms_conditions=(select id from gt_termsconditions_ps where state='active'), "
                   "txt_terms_conditions=(select terms_conditions from gt_termsconditions_ps where state='active')")
        return True


class TermsConditionsCustomer(osv.osv):
    _name = 'gt.termsconditions.customer'
    _description = 'Terminos y Condiciones Customer'

    _columns = dict(
        id=fields.integer(readonly=True, help=u'Versión de los términos y condiciones'),
        terms_conditions=fields.text('Términos y Condiciones Ps', size=8000,
                                     help=u'Ingrese los términos y condiciones del Cliente'),
        state=fields.selection(_STATETERMS, 'Estado términos y condiciones', readonly=True, track_visibility='onchange',
                               help=u'Estado términos y condiciones'),
        date_active=fields.char('Fecha activación', size=32, readonly=True,
                                  help=u'Fecha de activación de los términos y condiciones'),
        #diferenciar splashart para clientes y proveedores
    )

    _defaults = dict(
        state='inactive'
    )

    def act_active(self, cr, uid, ids, context=None):
        date = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        cr.execute("update gt_termsconditions_customer set state='inactive'")
        self.write(cr, uid, ids, {'state': 'active', 'date_active': date}, context)
        cr.execute("update gt_customer "
                   "set confirm_terms_conditions='False', "
                   "terms_conditions=(select id from gt_termsconditions_customer where state='active'), "
                   "txt_terms_conditions=(select terms_conditions from gt_termsconditions_customer where state='active')")
        return True


