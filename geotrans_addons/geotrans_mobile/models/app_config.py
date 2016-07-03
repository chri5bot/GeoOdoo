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
import logging
_logger = logging.getLogger(__name__)


class AppMobileConfig(osv.osv):
    _name = 'gt.mobilesetting.ps'
    _description = 'Configuraciones Mobiles Ps'
    _inherit = 'gt.mobilesetting.ps'

    def splash_art(self, cr, uid, var):
        _logger.debug('-------->splash_art:%s', str(datetime.now()))
        res = {}
        splashartid = self.search(cr, uid, [])
        splashart = self.browse(cr, uid, splashartid[0])
        if var == 'Partner' and splashart.mobile_activate:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion exitosa",
                    'MobileSplashArt': splashart.mobile_splashart,
                    'MobileSplashTime':  splashart.mobile_splashtime,
                }
            )
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "Error: El campo no es el correcto",
                }
            )
        _logger.debug('-------->splash_art:%s', str(datetime.now()))
        return res

    def splash_art_publicity(self, cr, uid, var):
        _logger.debug('-------->splash_art:%s', str(datetime.now()))
        res = {
            'IsGranted': False,
            'Message': "Error: El campo no es el correcto",
        }
        splashartid = self.search(cr, uid, [])
        splashart = self.browse(cr, uid, splashartid[0])
        if var == 'Partner' and splashart.mobile_activate_publicity:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion exitosa",
                    'MobileSplashArt': splashart.mobile_splashart_publicity,
                    'MobileSplashTime': splashart.mobile_splashtime_publicity,
                }
            )
        _logger.debug('-------->splash_art:%s', str(datetime.now()))
        return res

    def mobile_get_reasons_rejection(self, cr, uid):
        res = {}
        reasons_ids = self.pool.get('gt.reason').search(cr, 1, [])
        reasons = self.pool.get('gt.reason').browse(cr, 1, reasons_ids)
        reasons_list = {}
        if reasons:
            for r in reasons:
                reasons_list.update(
                    {
                        r.code: r.name,
                    }
                )
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion exitosa",
                    'Reasons': reasons_list,
                }
            )
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "No se encuentran razones configuradas",
                }
            )
        return res

    def mobile_get_url(self, cr, uid):
        res = {}
        id = self.search(cr, 1, [])[0]
        config = self.browse(cr, 1, id)
        if config:
            res.update(
                {
                    'IsGranted': True,
                    'Message': config.url_tutorial,
                }
            )
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "No existe URL",
                }
            )
        return res

    def mobile_get_predefined_messages(self, cr, uid):
        res = {}
        id = self.search(cr, 1, [])[0]
        config = self.browse(cr, 1, id)
        if config:
            messages = {}
            for message in config.message_ids:
                messages.update(
                    {
                        message.code: message.name,
                    }
                )
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion exitosa, lista de mensajes predefinidos",
                    'Messages': messages,
                }
            )
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "No existe una configuración de mensajes predefinida",
                }
            )
        return res


class AppMobileConfigCustomer(osv.osv):
    _name = 'gt.mobilesetting.customer'
    _description = 'Configuraciones Mobiles Cliente'
    _inherit = 'gt.mobilesetting.customer'

    def splash_art(self, cr, uid, var):
        res = {}
        splashartid = self.search(cr, uid, [])
        splashart = self.browse(cr, uid, splashartid[0])
        if var == 'Customer' and splashart.mobile_activate:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion exitosa",
                    'MobileSplashArt': splashart.mobile_splashart,
                    'MobileSplashTime':  splashart.mobile_splashtime,
                }
            )
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "Error: El campo no es el correcto",
                }
            )
        return res

    def splash_art_publicity(self, cr, uid, var):
        _logger.debug('-------->splash_art:%s', str(datetime.now()))
        res = {
            'IsGranted': False,
            'Message': "Error: El campo no es el correcto",
        }
        splashartid = self.search(cr, uid, [])
        splashart = self.browse(cr, uid, splashartid[0])
        if var == 'Customer' and splashart.mobile_activate_publicity:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion exitosa",
                    'MobileSplashArt': splashart.mobile_splashart_publicity,
                    'MobileSplashTime': splashart.mobile_splashtime_publicity,
                }
            )
        _logger.debug('-------->splash_art:%s', str(datetime.now()))
        return res

    def mobile_get_url(self, cr, uid):
        res = {}
        id = self.search(cr, 1, [])[0]
        config = self.browse(cr, 1, id)
        if config:
            res.update(
                {
                    'IsGranted': True,
                    'Message': config.url_tutorial,
                }
            )
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "No existe URL",
                }
            )
        return res
