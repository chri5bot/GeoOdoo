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

from openerp.osv import orm, osv
from gcm import GCM
import logging
_logger = logging.getLogger(__name__)

# Es la llave del proyecto en google developer


class gcm_common(orm.AbstractModel):
    API_KEY = False
    PACKAGE_NAME= False

    _name = 'gcm.common'

    def set_apikey(self,api_key):
        self.API_KEY=api_key

    def set_package(self, package):
        self.PACKAGE_NAME = package

    def gcm_topic_send(self, cr, uid, topic,notification, conext=None):
        # Topic Messaging
        if not self.API_KEY:
            raise osv.except_osv(u'Alera', u'No se a configurado el API KEY de Google GCM')
        gcm = GCM(self.API_KEY)

        if not notification:
            notification={
            "type": "Notificación de tópico",
            "message": "Tópico de Tandi GCM!"
            }
        if not topic:
            topic = 'tandigcm'

        response = gcm.send_topic_message(topic=topic, data=notification)
        print(response)

    def gcm_disp_send(self, cr, uid, registration_ids, notification, conext=None):
        # JSON request
        print ("____>PACKAGE:"+str(self.PACKAGE_NAME))
        if not self.API_KEY:
            raise osv.except_osv(u'Error', u'No se a configurado el API KEY de Google GCM')
        if not self.PACKAGE_NAME:
            raise osv.except_osv(u'Error', u'No se a configurado el Paquete Para la Aplicacion')

        gcm = GCM(self.API_KEY)

        if not notification:
            notification = {
                "type": 0,
                "collapse_key":"GRUPO DE MENSAJES",
                "title": "Nueva notificación Openerp",
                "message": "Notificación modelo de Tandi-GCM!",
            }
        _logger.info('gcm.json_request:package:{0} api:{1} '.format(str(self.PACKAGE_NAME),str(self.API_KEY)), exc_info=False)
        response = gcm.json_request(registration_ids=registration_ids,
                                    data=notification,
                                    collapse_key='notify_update',
                                    restricted_package_name=str(self.PACKAGE_NAME),
                                    priority='high',
                                    delay_while_idle=False)

        # Successfully handled registration_ids
        if response and 'success' in response:
            for reg_id, success_id in response['success'].items():
                _logger.debug('Successfully sent notification for reg_id {0}'.format(reg_id), exc_info=False)

            return True

        # Handling errors
        if 'errors' in response:
            for error, reg_ids in response['errors'].items():
                # Check for errors and act accordingly
                if error in ['NotRegistered', 'InvalidRegistration']:
                    # Remove reg_ids from database
                    for reg_id in reg_ids:
                        self.gcm_remove_tokens(cr, uid, reg_id, conext)
                else:
                    _logger.info('>>> ERROR gcm.json_request: '+str(response), exc_info=False)


        # Repace reg_id with canonical_id in your database
        if 'canonical' in response:
            for reg_id, canonical_id in response['canonical'].items():
                _logger.debug("Replacing reg_id: {0} with canonical_id: {1} in db".format(reg_id, canonical_id), exc_info=False)

        return False


    def gcm_remove_tokens(self, cr, uid, token, conext=None):
        _logger.debug("Por favor implemente le metodo de borrado del token {0}".format(token), exc_info=False)
        return True

class gcm_message(orm.AbstractModel):
    _name = 'gcm.message'


