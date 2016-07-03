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

_MESSAGE = [('one', 'message one'), ('two', 'message two'), ('three', 'message three'), ('four', 'message four'),
            ('five', 'message five'), ('six', 'message six'), ('seven', 'message seven'), ('eight', 'message eight')]


class Predefined_Message(osv.osv):
    _name = 'gt.predefined.message'
    _description = 'Mensajes Predefinidos'

    _columns = dict(
        code=fields.selection(_MESSAGE, string='Mensajes Predefinidos', required=True, size=16,
                              help=u'Mensajes Predefinidos'),
        name=fields.char('Nombre para Mostrar', size=64, required=True, help=u'Ingrese el nombre del mensaje'),
        active=fields.boolean('Activo', help=u'Indica si estan activos')
    )

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for pmsg in self.browse(cr, uid, ids, context=context):
            names = [item for item in _MESSAGE if item[0] == pmsg.name]
            if len(names) > 0:
                result[pmsg.id] = names[0][1]
            else:
                result[pmsg.id] = pmsg.name
        return result.items()

    def get_active_reasons(self, cr, uid, context=None):
        messagetypes = {}
        messages_object_ids = self.search(cr, uid, [('active', '=', 'True')])
        messages = self.browse(cr, uid, messages_object_ids)
        for message_type in messages:
            messagetypes.update(
                {
                    message_type.code: message_type.name,
                }
            )
        return messagetypes
