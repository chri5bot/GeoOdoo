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


class MobileSettingsPs(osv.osv):
    _name = 'gt.mobilesetting.ps'
    _description = 'Configuraciones Mobiles Ps'

    def _only_gif(self, cr, uid, ids,context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.mobile_splashart_filename[-4:] == ".gif" or obj.mobile_splashart_filename_publicity[-4:] == ".gif":
                return True
        return False

    _columns = dict(
        mobile_splashart=fields.binary('Archivo(.gif)', required=False,
                                       help=u'Ingrese el splash art que va estar mostrado en la app del Ps'),
        mobile_splashart_filename=fields.char('Filename'),
        mobile_splashtime=fields.integer('Tiempo', required=False,
                                         help=u'Tiempo en segundos que se va mostrar el splash art'),
        mobile_activate=fields.boolean('Activar',
                                       help=u'Seleccione la actividad del splash recuerde que debe ser unico'),
        mobile_splashart_publicity=fields.binary('Archivo(.gif)', required=False,
                                                 help=u'Ingrese el splash publicitario '
                                                      u'que va estar mostrado en la app del Ps'),
        mobile_splashart_filename_publicity=fields.char('Filename'),
        mobile_splashtime_publicity=fields.integer('Tiempo', required=False,
                                                   help=u'Tiempo en segundos que se va mostrar el splash art'),
        mobile_activate_publicity=fields.boolean('Activar',
                                                 help=u'Seleccione la actividad del splash recuerde que debe ser unico'),
        api_key=fields.char('API KEY Google', size=50, required=True, help=u'Ingrese el API KEY'),
        package=fields.char('Paquete de la aplicación de PS', size=50,
                            required=True, help=u'Ingrese el Paquete de la aplicación de PS ej: com.geotrans'),
        url_tutorial=fields.char(string='Url Tutorial', help=u'Ingrese la url del tutorial'),
        reason_ids=fields.many2many('gt.reason', string="Rechazos Disponibles",
                                          help=u"Seleccione los rechazos disponibles"),
        message_ids=fields.many2many('gt.predefined.message', string=u"Mensajes predefinidos",
                                     help=u"Elija los mensajes que van estar predefinidos en la aplicación")
        #diferenciar splashart para clientes y proveedores
    )

    _constraints = [(_only_gif, ('Solo se permiten archivos .gif'), ['Splash art'])]

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for ps in self.browse(cr, uid, ids, context=context):
            result[ps.id] = "Configuración Proveedor de servicio"
        return result


class MobileSettingsCustomer(osv.osv):
    _name = 'gt.mobilesetting.customer'
    _description = 'Configuraciones Mobiles Customer'

    def _only_gif(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.mobile_splashart_filename[-4:] == ".gif" or obj.mobile_splashart_filename_publicity[-4:] == ".gif":
                return True
        return False

    _columns = dict(
        mobile_splashart=fields.binary('Archivo(.gif)',  required=False,
                                       help=u'Ingrese el splash art que va estar mostrado en la app del usuario'),
        mobile_splashart_filename=fields.char('Filename'),
        mobile_splashtime=fields.integer('Tiempo', required=False,
                                         help=u'Tiempo en segundos que se va mostrar el splash art'),
        mobile_activate=fields.boolean('Activar',
                                       help=u'Seleccione la actividad del splash recuerde que debe ser unico'),
        mobile_splashart_publicity=fields.binary('Archivo(.gif)', required=False,
                                                 help=u'Ingrese el splash publicitario '
                                                      u'que va estar mostrado en la app del usuario'),
        mobile_splashart_filename_publicity=fields.char('Filename'),
        mobile_splashtime_publicity=fields.integer('Tiempo', required=False,
                                                   help=u'Tiempo en segundos que se va mostrar el splash art'),
        mobile_activate_publicity=fields.boolean('Activar',
                                                 help=u'Seleccione la actividad del splash recuerde que debe ser unico'),
        api_key=fields.char('API KEY Google', size=50, required=True, help=u'Ingrese el API KEY'),
        package=fields.char('Paquete de la aplicación de Cliente', size=50, required=True,
                            help=u'Ingrese el Paquete de la aplicación de PS ej: com.geotrans.client'),
        activation_server=fields.char('Servidor de Activación de cuenta', size=80, required=True,
                                      help=u'Ingrese el URL del servidor de activación'),
        url_tutorial=fields.char(string='Url Tutorial', help=u'Ingrese la url del tutorial'),
        credit_card=fields.boolean('Permite tarjeta de crédito', help=u'Elija si permite tarjeta de crédito')
    )

    _constraints = [(_only_gif, ('Solo se permiten archivos .gif'), ['Splash art'])]

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for ps in self.browse(cr, uid, ids, context=context):
            result[ps.id] = "Configuración Usuario"
        return result
