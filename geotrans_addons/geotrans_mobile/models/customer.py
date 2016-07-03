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
from openerp import pooler
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
from partner import *
from dateutil import parser, rrule
import logging
import pytz
from pytz import UTC
import openerp.tools as tools

_logger = logging.getLogger(__name__)


class CustomerMobile(osv.osv):
    _name = 'gt.customer'
    _description = 'Cliente'
    _inherit = ['gt.customer', 'gcm.common']

    ACTIVATION_SERVER_URL = False

    def to_mobile_datetime(self, cr, uid, model_date):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        local_tz = pytz.timezone(user.partner_id.tz)
        fecha = datetime.strptime(model_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
        fecha = UTC.localize(fecha, is_dst=False)
        fecha = fecha.astimezone(local_tz)
        return fecha.strftime('%d/%m/%Y %H:%M:%S')

    def set_params(self, cr, uid):
        app_config_pool = self.pool.get('gt.mobilesetting.customer')
        id = app_config_pool.search(cr, 1, [])[0]
        config = app_config_pool.browse(cr, 1, id)
        self.set_apikey(config.api_key)
        self.set_package(config.package)
        self.ACTIVATION_SERVER_URL = config.activation_server
        return True

    def mobile_sign_up(self, cr, uid, is_company, name, last_name, mobile, street, email, pwd_customer, pwd_facebook,
                       pwd_google):
        res = {}
        self.set_params(cr, uid)
        if not self.ACTIVATION_SERVER_URL:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "No se puede crear su cuenta",
                }
            )
            return res
        geocustomerids = self.search(cr, uid, [('email', '=', email)])
        if not geocustomerids:
            cust_id = self.create(cr, uid, {'is_company': is_company, 'name': name, 'last_name': last_name,
                                            'mobile': mobile, 'street': street, 'email': email,
                                            'pwd_customer': pwd_customer, 'pwd_facebook': pwd_facebook,
                                            'pwd_google': pwd_google, 'state': 'inactive',})
            customer = self.browse(cr, uid, cust_id)
            mail_model_pool = self.pool.get('mail.thread')
            cipher = crypter.AESCipher("solutandi1811")
            crypted = cipher.encrypt(email)
            post_values = {
                'subject': 'Confirmar Cuenta',
                'body':
                    """
                    <p>Hola {0} {1}, para activar su cuenta por favor ingrese en el siguiente vinculo:</p>
                    <p><a href="{2}/activate_account?token={3}">{2}/activate_account?token={3}</a></p>
                    """.format(customer.name, customer.last_name, self.ACTIVATION_SERVER_URL, crypted),
                'partner_ids': [customer.partner_id.id],
                'attachments': [],
            }
            msg_id = mail_model_pool.message_post(cr, uid, [0], type='comment', subtype='mail.mt_comment', context=None,
                                                  **post_values)

            res.update({
                'IsGranted': True,
                'Message': "Conexion exitosa",
                'CustomerId': customer.id,
            })
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "Ya existe un cliente registrado con ese correo electrónico",
                }
            )
        return res

    def web_activate_account(self, cr, uid, id):
        if id and isinstance(int, id):
            geocustomer = self.browse(cr, uid, id)
            self.write(cr, uid, id, {'state': 'active'})
            _logger.debug("ACTIVANDO CUENTA".format(geocustomer.email), exc_info=False)
        else:
            _logger.debug("NO SE PUDO ACTIVAR", exc_info=False)

    def mobile_set_token(self, cr, uid, customer_id, token_id):
        self.write(cr, uid, [customer_id], {'token_id': token_id})
        return True

    def action_send_message(self, cr, uid, ids, notification, context=None):
        self.set_params(cr, uid)
        partner_obj = self.browse(cr, uid, ids)
        registration_ids = []
        for p_id in partner_obj:
            if p_id.token_id:
                registration_ids.append(p_id.token_id)
        if len(registration_ids) > 0:
            self.gcm_disp_send(cr, uid, registration_ids, notification, context)
        else:
            raise osv.except_osv(u'Alerta', u'No hay usuarios disponibles')
        return True

    def mobile_login(self, cr, uid, var, user, password):
        res = {}
        geocustomerids = self.search(cr, uid, [('email', '=', user)])
        if geocustomerids:
            appconfobj = self.pool.get('gt.mobilesetting.customer')
            appconfid = appconfobj.search(cr, 1, [])[0]
            appconfig = appconfobj.browse(cr, 1, appconfid)
            servicetypesobject = self.pool.get('gt.service.type')
            servicetypes = servicetypesobject.get_active_services(cr, uid)
            geocustomers = self.browse(cr, uid, geocustomerids)
            if geocustomers[0].state == 'active':
                if var == 1:
                    if geocustomers[0].pwd_customer == password:
                        res.update(
                            {
                                'IsGranted': True,
                                'Message': "Conexion exitosa",
                                'ServiceTypes': servicetypes,
                                'CustomerId': geocustomers[0].id,
                                'LoginStatus': 0,
                                'HasCreditCard': appconfig.credit_card,
                                'ConfirmTermsConditions': geocustomers[0].confirm_terms_conditions,
                            }

                        )
                        if geocustomers[0].confirm_terms_conditions == False:
                            res.update(
                                {
                                    'TermsConditions': geocustomers[0].terms_conditions,
                                    'TxtTermsConditions': geocustomers[0].txt_terms_conditions,
                                }
                            )
                    else:
                        res.update(
                            {
                                'IsGranted': False,
                                'Message': "La contraseña es incorrecta",
                                'LoginStatus': 3,
                            }
                        )
                elif var == 2:
                    if geocustomers[0].pwd_google == password:
                        res.update(
                            {
                                'IsGranted': True,
                                'Message': "Conexion exitosa",
                                'ServiceTypes': servicetypes,
                                'CustomerId': geocustomers[0].id,
                                'LoginStatus': 0,
                                'HasCreditCard': appconfig.credit_card,
                                'ConfirmTermsConditions': geocustomers[0].confirm_terms_conditions,
                            }
                        )
                        if geocustomers[0].confirm_terms_conditions == False:
                            res.update(
                                {
                                    'TermsConditions': geocustomers[0].terms_conditions,
                                    'TxtTermsConditions': geocustomers[0].txt_terms_conditions,
                                }
                            )
                    else:
                        res.update(
                            {
                                'IsGranted': False,
                                'Message': "La contraseña es incorrecta",
                                'LoginStatus': 3,
                            }
                        )
                elif var == 3:
                    if geocustomers[0].pwd_facebook == password:
                        res.update(
                            {
                                'IsGranted': True,
                                'Message': "Conexion exitosa",
                                'ServiceTypes': servicetypes,
                                'CustomerId': geocustomers[0].id,
                                'LoginStatus': 0,
                                'HasCreditCard': appconfig.credit_card,
                                'ConfirmTermsConditions': geocustomers[0].confirm_terms_conditions,
                            }
                        )
                        if geocustomers[0].confirm_terms_conditions == False:
                            res.update(
                                {
                                    'TermsConditions': geocustomers[0].terms_conditions,
                                    'TxtTermsConditions': geocustomers[0].txt_terms_conditions,
                                }
                            )
                    else:
                        res.update(
                            {
                                'IsGranted': False,
                                'Message': "La contraseña es incorrecta",
                                'LoginStatus': 3,
                            }
                        )
            elif geocustomers[0].state == 'block':
                res.update(
                    {
                        'IsGranted': False,
                        'Message': "El usuario se encuentra bloqueado",
                        'LoginStatus': 1,
                    }
                )
            elif geocustomers[0].state == 'inactive':
                res.update(
                    {
                        'IsGranted': False,
                        'Message': "El usuario no ha activado su cuenta, revise su cuenta de email",
                        'LoginStatus': 2,
                    }
                )
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "El usuario o contraseña son incorrectos",
                    'LoginStatus': 4,
                }
            )
        return res

    def mobile_confirm_termsconditions(self, cr, uid, customer_id, answer):
        if customer_id:
            self.write(cr, uid, [customer_id], {'confirm_terms_conditions': answer})
            return True

    def mobile_terms_conditions(self, cr, uid, customer_id):
        res = {}
        geocustomerinfoids = self.search(cr, uid, [('id', '=', customer_id)])
        geocustomerinfo = self.browse(cr, uid, geocustomerinfoids)
        if geocustomerinfo:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion exitosa",
                    'TxtTermsConditions': geocustomerinfo[0].txt_terms_conditions,
                }
            )
            return res
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "Error: El campo no es el correcto",
                }
            )
            return res

    def mobile_restore_password(self, cr, uid, user):
        res = {}
        geocustomerids = self.search(cr, uid, [('email', '=', user)])
        geocustomers = self.browse(cr, uid, geocustomerids)
        if not geocustomers:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "El usuario es erróneo"

                }
            )
        else:
            mail_model_pool = self.pool.get('mail.thread')
            post_values = {
                'subject': 'Restablecimiento de contraseña',
                'body':
                    """
                    <p>Estimado {0},</p>
                    <p>Su contraseña actual es: {1}</p>
                    """.format(geocustomers[0].name, geocustomers[0].pwd_customer),
                'partner_ids': [geocustomers[0].partner_id.id],
                'attachments': [],
            }
            msg_id = mail_model_pool.message_post(cr, uid, [0], type='comment', subtype='mail.mt_comment', context=None,
                                                  **post_values)
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Enviaremos la contraseña a su email",
                    'PartnerId': geocustomers[0].id,

                }
            )
        return res

    def mobile_update_password(self, cr, uid, user, password, new_password):
        res = {}
        geocustomerids = self.search(cr, uid, [('email', '=', user), ('pwd_customer', '=', password)])
        geocustomer = self.browse(cr, uid, geocustomerids)
        if not geocustomer:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "Usuario o contraseña erróneos"
                }
            )
        else:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Su contraseña ha sido cambiada exitosamente",
                    'PartnerId': geocustomer[0].id,
                }
            )
            self.write(cr, uid, [geocustomer[0].id], {'pwd_customer': new_password})
        return res

    def mobile_customer_info(self, cr, uid, customer_id):
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener los datos del cliente"
        }
        geocustomerids = self.search(cr, uid, [('id', '=', customer_id)])
        geocustomerinfo = self.browse(cr, uid, geocustomerids)
        if geocustomerinfo:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa",
                    'CustomerName': geocustomerinfo[0].name,
                    'CustomerLastName': geocustomerinfo[0].last_name,
                    'CustomerMobile': geocustomerinfo[0].mobile,
                    'CustomerEmail': geocustomerinfo[0].email,
                    'CustomerAddress': geocustomerinfo[0].street,
                    'CustomerInvoice': geocustomerinfo[0].confirm_invoicing,
                    'IsCompany': geocustomerinfo[0].is_company,
                }
            )
            if geocustomerinfo[0].confirm_invoicing:
                res.update(
                    {
                        'CustomerTypeIdentity': geocustomerinfo[0].type_ced_ruc,
                        'CustomerTypePerson': geocustomerinfo[0].tipo_persona,
                        'CustomerIdentityCard': geocustomerinfo[0].ced_ruc,
                    })

        return res

    def mobile_update_customer_info(self, cr, uid, customer_id, name, last_name, ced_ruc, type_ced_ruc, tipo_persona,
                                    mobile, street, confirm_invoicing):
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo actualizar los datos del cliente",
        }
        service_cutomer = self.browse(cr, uid, customer_id)
        try:
            values = {
                'name': name, 'last_name': last_name, 'mobile': mobile,
                'street': street, 'confirm_invoicing': confirm_invoicing
            }
            if confirm_invoicing:
                values.update({'ced_ruc': ced_ruc, 'type_ced_ruc': type_ced_ruc, 'tipo_persona': tipo_persona,})

            self.write(cr, uid, [customer_id], values)
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Se ha actualizado la información del usuario",
                }
            )
        except Exception, e:
            import traceback
            _logger.warning('ERROR: {0} \n\r'.format(e), exc_info=False)
            res['Message'] = 'NO SE PUDO ACTUALIZAR, YA EXISTE OTRO USUARIO CON LA MISMA IDENTIFICACION'
        finally:
            return res

    def mobile_customer_credit_card(self, cr, uid, customer_id):
        res = {}
        bank = self.pool.get('res.partner.bank')
        geocustomerids = self.search(cr, uid, [('id', '=', customer_id)])
        geocustomerinfo = self.browse(cr, uid, geocustomerids)
        bankids = bank.search(cr, uid, [('partner_id', '=', geocustomerinfo[0].partner_id.id)])
        bankinfo = bank.browse(cr, uid, bankids)
        if not bankinfo:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "Error: No se pudo obtener los datos del cliente",
                    'IsFirsttime': True,
                }
            )
        else:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa",
                    'BankId': bankinfo[0].id,
                    'State': bankinfo[0].state,
                    'CardOwner': bankinfo[0].owner_name,
                    'Bank': bankinfo[0].bank_name,
                    'CcNumber': bankinfo[0].cc_number,
                    'CcEDMonth': bankinfo[0].cc_e_d_month,
                    'CcEDYear': bankinfo[0].cc_e_d_year,
                    'Ccv': bankinfo[0].cc_v,
                    'IsFirstTime': False,
                }
            )
        return res

    def mobile_update_customer_credit_card(self, cr, uid, customer_id, state, cc_number, owner_name, bank_id,
                                           cc_e_d_month, cc_e_d_year, cc_v, bank_name):
        res = {}
        bank = self.pool.get('res.partner.bank')
        geocustomerids = self.search(cr, uid, [('id', '=', customer_id)])
        geocustomerinfo = self.browse(cr, uid, geocustomerids)
        if customer_id:
            if bank_id == 0:
                bank.create(cr, uid, {'partner_id': geocustomerinfo[0].partner_id.id, 'state': state,
                                      'cc_number': cc_number, 'owner_name': owner_name, 'acc_number': cc_number,
                                      'cc_e_d_month': cc_e_d_month, 'cc_e_d_year': cc_e_d_year,
                                      'cc_v': cc_v, 'bank_name': bank_name})
                res.update(
                    {
                        'IsGranted': True,
                        'Message': "Sus datos han sido registrados exitosamente",
                    }
                )
            else:
                bank.write(cr, uid, [bank_id], {'partner_id': geocustomerinfo[0].partner_id.id, 'state': state,
                                                'cc_number': cc_number, 'owner_name': owner_name,
                                                'cc_e_d_month': cc_e_d_month, 'cc_e_d_year': cc_e_d_year,
                                                'cc_v': cc_v, 'bank_name': bank_name})
                res.update(
                    {
                        'IsGranted': True,
                        'Message': "Sus datos han sido registrados exitosamente",
                    }
                )
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "Error: Sus datos no han sido registrados"
                }
            )
        return res

    def mobile_get_ps_details(self, cr, uid, ps_id):
        service_partner_obj = self.pool.get('gt.service.partner')
        service_partner = service_partner_obj.browse(cr, uid, ps_id)
        lng, lat = service_partner_obj.get_geopoint_to_google(cr, uid, service_partner.partner_id.id)
        ProviderServiceName = service_partner.name+' '+service_partner.last_name
        sp_dto = {
            'IsGranted': True,
            'Message': "Conexion exitosa",
            'ProviderServiceId': service_partner.id,
            #TODO Error si tiene una tilde en el campo name o lastname
            'ProviderServiceName': ProviderServiceName,
            'VehicleModel': service_partner.vehicle_ids[0].id_brandvehicles.name,
            'LicensePlate': service_partner.id,
            'PhotoProviderService': service_partner.image_medium,
            'PhotoMotorcycle': service_partner.vehicle_ids[0].photo_vehicle_medium,
            'PhotoLicensePlate': service_partner.vehicle_ids[0].photo_licenseplate_medium,
            'LastPosition': {'Longitude': str(lng), 'Latitude': str(lat)},
        }
        return sp_dto

    def mobile_has_active_route(self, cr, uid, customer_id):
        res = {
            'IsGranted': False,
            'Message': "No tiene rutas activas"
        }
        routeobj = self.pool.get('gt.route')
        routeids = routeobj.search(cr, uid, [('customer_partner_id', '=', customer_id),
                                             ('state', '=', 'inprogress')])
        routes = routeobj.browse(cr, uid, routeids)
        if routes:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Si tiene rutas activas"
                }
            )
        return res

    def mobile_last_origin(self, cr, uid, customer_id):
        res = {
            'IsGranted': False,
            'Message': "No tiene rutas completadas"
        }
        route_obj = self.pool.get('gt.route')
        travel_obj = self.pool.get('gt.travel')
        routeids = route_obj.search(cr, uid, [('customer_partner_id', '=', customer_id),
                                              ('state', 'in', ['done', 'confirmed'])])

        if len(routeids) > 0:
            travel_ids = travel_obj.search(cr, uid, [('route_id', '=', routeids[-1]), ('order', '=', 1)])
            if len(travel_ids) > 0:
                travel = travel_obj.browse(cr, uid, travel_ids[0])
                lng_ori, lat_ori = travel_obj.get_geopoint_to_google(cr, uid, travel.id, 'geo_point_start')
                res = {
                    'IsGranted': True,
                    'Message': "Ultimo Origen",
                    'Longitude': str(lng_ori),
                    'Latitude': str(lat_ori),
                }
        _logger.debug("\n\r mobile_last_origin: res:" + str(res))
        return res

    def mobile_notify_list(self, cr, uid, customer_id):
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener los mensajes"
        }
        notify_obj = self.pool.get('gt.mobile.notify')
        nots_ids = notify_obj.search(cr, uid, [('type', '=', 'US'), ('customer_partner_id', '=', customer_id)])
        nots = []
        if customer_id and len(nots_ids) > 0:
            for line in notify_obj.browse(cr, uid, nots_ids):
                nots.append({
                    'Title': line.title,
                    'Message': line.message,
                    'DateTime': self.to_mobile_datetime(cr, uid, line.date)})

            res.update(
                {
                    'IsGranted': True,
                    'Message': "Lista de mensajes",
                    'TrayNotifications': nots
                }
            )
        return res
