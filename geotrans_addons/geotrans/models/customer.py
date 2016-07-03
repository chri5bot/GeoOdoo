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
from vehicle import *
from validate_email import validate_email
from geotrans import *
import re
from openerp import tools
from openerp.tools.sql import drop_view_if_exists

_CUSTOMERSTATES = [('active', 'Activo'), ('inactive', 'Inactivo'), ('block', 'Bloqueado')]


class Partner(osv.osv):

    _name = 'res.partner'
    _inherit = 'res.partner'
    _description = 'Formulario de Partner para Ecuador'

    _columns = {
        'ced_ruc': fields.char('Cedula/ RUC', size=13, required=False,
                               help='Idenficacion o Registro Unico de Contribuyentes'),
        'type_ced_ruc': fields.selection([('cedula', 'Cedula'), ('ruc', 'RUC'), ('pasaporte', 'Pasaporte')], 'Tipo ID',
                                         required=False),
        'tipo_persona': fields.selection([('6','Persona Natural'),('9','Persona Juridica')], 'Persona', required=False),
        }


class Customer(osv.osv):
    _name = 'gt.customer'
    _description = 'Cliente'
    # _inherits: con esto generamos una nueva tabla con el objeto service partner y se relaciona mediante la columna partner_id
    _inherits = {'res.partner': 'partner_id'}

    def _get_terms_conditions(self, cr, uid, ids, context={}):
        term_object=self.pool.get('gt.termsconditions.customer')
        term_object_id=term_object.search(cr, uid, [('state', '=', 'active')])
        if term_object_id:
            if len(term_object_id) >0:
                return term_object_id[0]
        return False

    def _get_txt_terms_conditions(self, cr, uid, ids, context={}):
        term_object=self.pool.get('gt.termsconditions.customer')
        term_object_id=term_object.search(cr, uid, [('state', '=', 'active')])
        for obj in term_object.browse(cr, uid, term_object_id, context=context):
            return obj.terms_conditions

    def _get_user(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = obj.email
            return res

    _columns = dict(
        last_name=fields.char('Apellido', size=32, required=False, help=u'Ingrese el apellido del Cliente'),
        state=fields.selection(_CUSTOMERSTATES, string='Estado Cliente', help=u"Indique el estado del cliente"),
        user_customer=fields.function(_get_user, method=True, type='char', size=32, string='User', help=u'Usuario para login Customer'),
        pwd_customer=fields.char('Password', size=64, readonly=False, password=True),
        pwd_facebook=fields.char('Password Facebook', size=64, readonly=False, password=True),
        pwd_google=fields.char('Password Google', size=64, readonly=False, password=True),
        terms_conditions=fields.char(string='Versión actual', readonly=True),
        txt_terms_conditions=fields.text('Términos y Condiciones Cliente', size=8000),
        confirm_terms_conditions=fields.boolean('Acepto', readonly=True,
                                                help=u'Indica si el Cliente ha aceptado los términos y Condiciones'),
        confirm_invoicing=fields.boolean('Acepto', readonly=True, help=u'Indica si el Cliente desea facturar'),
        token_id=fields.char('Id Dispositivo', readonly=True, size=256, help=u'Id del dispositivo'),
    )
    _defaults = dict(
        state='inactive',
        terms_conditions=_get_terms_conditions,
        confirm_invoicing=False,
        txt_terms_conditions=_get_txt_terms_conditions,
    )

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for customer in self.browse(cr, uid, ids, context=context):
            if customer.last_name:
                result[customer.id] = customer.name + " " + customer.last_name
            else:
                result[customer.id] = customer.name
        return result.items()

    def act_inactive(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'inactive'}, context)
        return True

    def act_block(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'block'}, context)
        return True
