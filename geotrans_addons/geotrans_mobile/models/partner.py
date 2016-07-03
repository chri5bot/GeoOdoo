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


class ServicePartnerMobile(osv.osv):
    _name = 'gt.service.partner'
    _description = 'Proveedor de Servicio'
    # _inherits: con esto generamos una nueva tabla con el objeto service partner y se relaciona mediante la columna partner_id
    _inherit = ['gt.service.partner','gcm.common']

    def set_params(self, cr, uid):
        app_config_pool = self.pool.get('gt.mobilesetting.ps')
        id=app_config_pool.search(cr, 1, [])[0]
        config=app_config_pool.browse(cr,1,id)
        self.set_apikey(config.api_key)
        self.set_package(config.package)
        print("______>setparams:"+str(config.package))

        return True

    def action_send_message(self, cr, uid, ids, notification,context=None):
        self.set_params(cr, uid)
        res=False
        gcm_obj = self.pool.get('gcm.common')
        partner_obj = self.browse(cr, uid, ids)
        registration_ids = []
        for p_id in partner_obj:
            if p_id.token_id:
                registration_ids.append(p_id.token_id)
        if len(registration_ids)>0:
            res = self.gcm_disp_send(cr, uid, registration_ids, notification,context)
        else:
            raise osv.except_osv(u'Alera', u'Ningún Proveedor de Servicio se encuentra disponible')

        return res

    def action_send_topic_message(self, cr, uid, ids, conext):

        notification = {
            "Title": "Notificación masiva",
            "Message": "Notificación de un tópico",
        }

        gcm_obj = self.pool.get('gcm.common')
        topic = "geotrans"

        self.gcm_topic_send(cr, uid, topic, notification, conext)

        return True

    def to_mobile_date(self, cr, uid, model_date):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        local_tz = pytz.timezone(user.partner_id.tz)
        fecha = datetime.strptime(model_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
        fecha = UTC.localize(fecha, is_dst=False)
        fecha = fecha.astimezone(local_tz)
        return fecha.strftime('%d/%m/%Y')

    def to_mobile_hour(self, cr, uid, model_date):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        local_tz = pytz.timezone(user.partner_id.tz)
        fecha = datetime.strptime(model_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
        fecha = UTC.localize(fecha, is_dst=False)
        fecha = fecha.astimezone(local_tz)
        return fecha.strftime('%H:%M:%S')

    def to_mobile_datetime(self, cr, uid, model_date):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        local_tz = pytz.timezone(user.partner_id.tz)
        fecha = datetime.strptime(model_date, tools.DEFAULT_SERVER_DATETIME_FORMAT)
        fecha = UTC.localize(fecha, is_dst=False)
        fecha = fecha.astimezone(local_tz)
        return fecha.strftime('%d/%m/%Y %H:%M:%S')

    def to_openerp_date(self, cr, uid, dto_date):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        local_tz = pytz.timezone(user.partner_id.tz)
        fecha = datetime.strptime(dto_date, '%d/%m/%Y %H:%M:%S')
        fecha = local_tz.localize(fecha, is_dst=False)
        fecha = fecha.astimezone(UTC)
        return fecha.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)

    def gcm_remove_tokens(self, cr, uid, token, conext=None):
        partner_id = self.search(cr, uid, [('token_id','=',token)])
        _logger.debug("Eliminado el token:{0}".format(token), exc_info=False)
        #self.write(cr, uid, partner_id, {'token_id': False})
        return True

    def mobile_login(self, cr, uid, user, password):#este metodo es el de login, obtiene user y pwd como parametro
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener el Proveedor, ingrese correctamente los campos"
        }
        geopartnersids = self.search(cr, uid, [('user_partner', '=', user), ('pwd_partner', '=', password)])
        geopartners = self.browse(cr, uid, geopartnersids)
        if geopartners:
            res = self.mobile_ps_status(cr, uid, geopartners[0].id)
            #SI EL METODO DEVUELVE IsGranted:False RETORNO res {'IsGranted': False,'Message':'.....'}
            if not res['IsGranted']:
                return res

            res.update(
                    {
                        'PartnerPhoto': geopartners[0].image_medium,
                        'ConfirmTermsConditions': geopartners[0].confirm_terms_conditions,
                    }
                )
            if not geopartners[0].confirm_terms_conditions:
                res.update(
                    {
                        'TermsConditions': geopartners[0].terms_conditions,
                        'TxtTermsConditions': geopartners[0].txt_terms_conditions,

                    }
                )
        return res

    def mobile_ps_status(self, cr, uid, ps_id):  # este metodo devuelve el estado actual del PS en Openerp
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener estatus del Proveedor"
        }
        geopartner = self.browse(cr, uid, ps_id)
        if geopartner and ps_id > 0:
            fullname = geopartner.name + ' ' + geopartner.last_name
            res = {}
            papplicationobj = self.pool.get('gt.penalty.application')
            papplicationids = papplicationobj.search(cr, uid, [('penalty_partner_id', '=', geopartner.id),
                                                               ('state', '=', 'confirmed')])
            papplications = papplicationobj.browse(cr, uid, papplicationids)
            if papplications:
                balance = 0
                for papplication in papplications:
                    balance += papplication.value
                res.update(
                    {
                        'CashPenalty': balance,
                    }
                )
            else:
                res.update(
                    {
                        'CashPenalty': 0.00,
                    }
                )
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion exitosa",
                    'PartnerId': geopartner.id,
                    'PartnerName': fullname,
                    'HasInvoices': True,
                    'HasPenalties': True,
                    'PartnerActive': geopartner.partner_active,
                    'CashBalance': geopartner.balance,
                }
            )
        return res

    def confirm_termsconditions(self, cr, uid, partner_id, answer):
        if partner_id:
            self.write(cr, uid, [partner_id], {'confirm_terms_conditions': answer})
            return True

    def terms_conditions(self, cr, uid, partner_id):
        res = {}
        geopartnersinfoids = self.search(cr, uid, [('id', '=', partner_id)])
        geopartnersinfo = self.browse(cr, uid, geopartnersinfoids)
        if partner_id:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion exitosa",
                    'TxtTermsConditions': geopartnersinfo[0].txt_terms_conditions,
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

    def mobile_partner_info(self, cr, uid, partner_id):#este metodo obtiene la informacion del partner, obtiene como parametro un partner id
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener el partner"
        }
        geopartnersinfoids = self.search(cr, uid, [('id', '=', partner_id)])
        geopartnersinfo = self.browse(cr, uid, geopartnersinfoids)
        if geopartnersinfo:
            servicetypes = {}
            for service_type in geopartnersinfo[0].service_type_ids:
                servicetypes.update(
                    {
                        service_type.code: service_type.name,
                    }
                )
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa",
                    'PartnerMobile': geopartnersinfo[0].mobile,
                    'PartnerPhone': geopartnersinfo[0].phone,
                    'PartnerEmail': geopartnersinfo[0].email,
                    'PartnerAddress': geopartnersinfo[0].street,
                    'PartnerRanking': geopartnersinfo[0].ranking,
                    'ServiceTypes': servicetypes,
                }
            )
        return res

    def mobile_activated(self, cr, uid, partner_id, var_active):
        res = {}
        if var_active:
            partner = self.browse(cr, uid, partner_id)
            if partner.vehicle_ids > 0:
                self.write(cr, uid, [partner_id], {'partner_active': var_active})
                res.update({
                    'IsGranted': True,
                    'Message': "Activado exitosamente",
                }
                )
            else:
                res.update({
                    'IsGranted': False,
                    'Message': "No se pudo activar, no tiene vehículo registrado",
                }
                )
        else:
            self.write(cr, uid, [partner_id], {'partner_active': var_active})
            res.update({
                'IsGranted': True,
                'Message': "Desactivado exitosamente",
            }
            )
        return True

    def update_servicepartner(self, cr, uid, partner_id, street, mobile, phone, email):
        self.write(cr, uid, [partner_id], {'street': street, 'mobile': mobile, 'phone': phone, 'email': email})
        return True

    def mobile_invoice_partner(self, cr, uid, partner_id):
        #TODO
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener el partner"
        }
        invoices = [('01', '2015/10/07', '200.00'), ('02', '2015/10/07', '300.00'), ('03', '2015/10/07', '500.00')]
        if partner_id:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa",
                    'Invoices': invoices,
                    #'invoice_id': invoice['id'],
                    #'invoice_date': invoice['fecha'],
                    #'invoice_total': invoice['valor'],

                }
            )
        return res

    def update_password(self, cr, uid, user, password, new_password):
        res = {
            'IsGranted': False,
            'Message': "Usuario o contraseña erróneos"
        }
        geopartnersids = self.search(cr, uid, [('user_partner', '=', user), ('pwd_partner', '=', password)])
        geopartners = self.browse(cr, uid, geopartnersids)
        if geopartners:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Su contraseña ha sido cambiada exitosamente",
                }
            )
            self.write(cr, uid, [geopartners[0].id], {'pwd_partner': new_password})
        return res

    def restore_password(self, cr, uid, user):
        res = {
            'IsGranted': False,
            'Message': "El usuario es erróneo"
        }
        geopartnersids = self.search(cr, uid, [('user_partner','=', user)])
        geopartners = self.browse(cr, uid, geopartnersids)
        if geopartners:
            mail_model_pool = self.pool.get('mail.thread')
            post_values = {
                'subject': 'Restablecimiento de contraseña',
                'body':
                    """
                    <p>Estimado {0},</p>
                    <p>Su contraseña actual es: {1}</p>
                    """.format(geopartners[0].name, geopartners[0].pwd_partner),
                'partner_ids': [geopartners[0].partner_id.id],
                'attachments': [],
            }
            msg_id = mail_model_pool.message_post(cr, uid, [0], type='comment', subtype='mail.mt_comment', context=None,
                                                  **post_values)
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Enviaremos la contraseña a su email",
                }
            )
        return res

    def mobile_invoice_detail(self, cr, uid, invoice_id):
        #TODO
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener el partner"
        }
        invoices = [('01', '2015/10/07', '11H30', '200.00'), ('02', '2015/10/07', '12H00', '300.00'), ('03', '2015/10/07', '15H00', '500.00')]
        if invoice_id:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa",
                    'Invoices': invoices,

                }
            )
        return res

    def mobile_checkinvoice(self, cr, uid, invoice_id):
        #TODO
        res = {
            'IsGranted': False,
            'Message': "Error: No se puede facturar"
        }
        if invoice_id:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa, se puede facturar",
                }
            )
        return res

    def mobile_unbilledinvoices(self, cr, uid, partner_id):
        #TODO
        res = {
            'IsGranted': False,
            'Message': "Error: No se puede obtener las facturas"
        }
        invoices = [('01', '2015/10/07', '11H30', '200.00'), ('02', '2015/10/07', '12H00', '300.00'),
                    ('03', '2015/10/07', '15H00', '500.00'), ('04', '2015/10/07', '13H00', '500.00'),
                    ('05', '2015/10/07', '15H00', '800.00')]
        if partner_id:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa, obtendra las facturas sin cobrar",
                    'UnBilledInvoices': invoices
                }
            )
        return res

    def mobile_travels_by_date(self, cr, uid, partner_id, date_begin, date_end):
        travels_by_date = []
        res = {
            'IsGranted': False,
            'Message': "Error: No se puede obtener las facturas"
        }
        date_start_t = parser.parse(date_begin)
        date_end_t = parser.parse(date_end)
        travelobj = self.pool.get('gt.travel')
        travelids = travelobj.search(cr, uid, [('sp_partner_id', '=', partner_id)])
        travels = travelobj.browse(cr, uid, travelids)
        for travel in travels:
            travel_in_range = parser.parse(travel.route_id.request_date)
            if date_start_t <= travel_in_range <= date_end_t:
                travelinfo = {
                    'InvoiceId': travel.id,
                    'InvoiceDate': self.to_mobile_date(cr, uid, travel.route_id.request_date),
                    'InvoiceHour': self.to_mobile_hour(cr, uid, travel.route_id.request_date),
                    'InvoiceKm': travel.estimated_km,
                    #TODO hacer calculos de viajes
                    'InvoiceValue': str(80),
                }
                travels_by_date.append(travelinfo.copy())
        res.update(
            {
                'IsGranted': True,
                'Message': "Conexion Exitosa",
                'UnbilledInvoices': travels_by_date,
            }
        )
        return res

    def mobile_set_token(self, cr, uid, partner_id, token_id):
        self.write(cr, uid, [partner_id], {'token_id': token_id})
        return True

    def mobile_penalties(self, cr, uid, partner_id):
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener los datos del cliente"
        }
        confirm_penalties = []
        user = self.pool.get('res.users').browse(cr, uid, uid)
        local_tz = pytz.timezone(user.partner_id.tz)
        penaltyapplicationobj = self.pool.get('gt.penalty.application')
        penaltyids = penaltyapplicationobj.search(cr, uid, [('penalty_partner_id', '=', partner_id),
                                                            ('state', '=', 'confirmed')])
        penalties = penaltyapplicationobj.browse(cr, uid, penaltyids)
        if penalties:
            for penalty in penalties:
                penealtyinfo = {
                    'PenaltyId': penalty.penalty_id.id,
                    'PenaltyDate': self.to_mobile_date(cr, uid, penalty.date),
                    'PenaltyHour': self.to_mobile_hour(cr, uid, penalty.date),
                    'PenaltyValue': str(penalty.value),
                }
                confirm_penalties.append(penealtyinfo.copy())
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa",
                    'Penalties': confirm_penalties,
                }
            )
        return res

    def mobile_partner_position(self, cr, uid, ps_id, lng, lat):
        res = {}
        try:
            servicepartner = self.browse(cr, uid, ps_id)
            if not servicepartner.partner_id:
                raise Exception('No se recibe: ps_id!')
            lat = lat.replace(",",".")
            lng = lng.replace(",", ".")
            sql = " UPDATE res_partner set " \
                  " geo_point=ST_Transform(ST_GeomFromText('Point({0} {1})',4326),900913), write_uid = {2} " \
                  " WHERE id={3}".format(lng, lat, uid, servicepartner.partner_id.id)
            cr.execute(sql)
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa, obtendra las multas",
                }
            )
        except Exception, e:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "Conexion Fallida",
                }
            )
        return res


    def mobile_reason_rejection(self, cr, uid, ps_id, code_reason, route_id):
        res = {
            'IsGranted': False,
            'Message': "Debe enviar una descripcion o el proveedor no existe",
        }
        route_obj = self.pool.get('gt.route')
        reasonobj = self.pool.get('gt.reason')
        routerejectionobj = self.pool.get('gt.route.rejection')
        reason_ids = reasonobj.search(cr, uid, [('code', '=', code_reason)])
        psinrange_object = self.pool.get('gt.route.psinrange')
        if code_reason and reason_ids and len(reason_ids) > 0:
            reason = reasonobj.browse(cr, uid, reason_ids[0])
            route_rejection_id = routerejectionobj.create(cr, uid, {'service_partner_id': ps_id,
                                                                    'route_id': route_id,
                                                                    'reason_id': reason.id,
                                                                    'support': False})
            routerejection = routerejectionobj.browse(cr, uid, route_rejection_id)
            psinrange_ids = psinrange_object.search(cr, uid, [
                ('route_id', '=', routerejection.route_id.id),
                ('service_partner_id', '=', routerejection.service_partner_id.id)
            ])
            psinrange_object.unlink(cr, uid, psinrange_ids)
            route_obj.act_search(cr, uid, route_id)

            res.update(
                {
                    'IsGranted': True,
                    'Message': "Ha rechazado una carrera",
                }
            )
        return res

    def mobile_accept_route(self, cr, uid, ps_id, route_id):
        res = {
                'IsGranted': False,
                'Message': "Debe enviar una descripcion o el proveedor no existe",
        }
        route_obj = self.pool.get('gt.route')
        customer_obj = self.pool.get('gt.customer')
        travel_obj = self.pool.get('gt.travel')
        psinrange_obj = self.pool.get('gt.route.psinrange')
        route = route_obj.browse(cr, uid, route_id)
        if route:
            route_obj.write(cr, uid, route.id, {'state': 'inprogress'})
            prids = []
            for pr in route.partners_inrange:
                prids.append(pr.id)
            psinrange_obj.unlink(cr, uid, prids)
            if route.travel_ids and len(route.travel_ids) > 0:
                tids = []
                for tid in route.travel_ids:
                    tids.append(tid.id)

                travel_obj.write(cr, uid, tids, {'sp_partner_id': ps_id, 'state': 'inprogress'})

                route_obj.mobile_notify_ps_route(cr, uid, route.customer_partner_id.id, ps_id, route.id, 'gt.customer')
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Ha aceptado una ruta satisfactoriamente",
                }
            )
        return res

    def mobile_ask_support(self, cr, uid, ps_id, travel_id, lng, lat, geocode):
        res = {
            'IsGranted': False,
            'Message': u"No se pudo pedir relevo, por favor comuníquese con oficinas",
        }
        route_obj = self.pool.get('gt.route')
        support_obj = self.pool.get('gt.travel.support')
        partner_obj = self.pool.get('gt.service.partner')
        if travel_id and ps_id:
            geopoint_openerp = support_obj.parse_geopoint_from_google(cr, uid, "POINT({0} {1})".format(lng, lat))
            support_id = support_obj.create(cr, uid,
                                            {'travel_id': travel_id,
                                             'original_partner_id': ps_id,
                                             'geo_point': geopoint_openerp,
                                             'geocode': geocode})


            support_obj.act_support_search(cr, uid, [support_id], ps_id, distance=2500)
            if support_id:
                support = support_obj.browse(cr, uid, support_id)
                distances = [2500, 3500, 4500]
                if support:
                    for dist in distances:
                        # NOTIFICO QUE EXTIENDO LA BUSQUEDA SOLO DESDE LA SEGUNDA DISTANCIA
                        if dist != distances[0]:
                            route_obj.mobile_notify_extend_search(cr, uid, ps_id, dist, 'gt.service.partner')
                        findpartners = support_obj.act_support_search(cr, uid, [support.id], ps_id, distance=dist)
                        if findpartners:
                            route_obj.mobile_notify_support(cr, uid, support.id)
                            res.update(
                                {
                                    'IsGranted': True,
                                    'Title': "Buscando Proveedor de Servicio para relevo",
                                    'Message': "Por favor espere...",
                                }
                            )
                            break
                    if not findpartners:
                        route_obj.mobile_notify_no_partner(cr, uid, ps_id, 'gt.service.partner')
            return res

        return res

    def mobile_accept_support(self, cr, uid, ps_id, support_id):
        res = {
            'IsGranted': False,
            'Message': "El relevo no existe o ya fue tomado",
        }
        support_obj = self.pool.get('gt.travel.support')
        travel_obj = self.pool.get('gt.travel')
        route_obj = self.pool.get('gt.route')
        psinrange_obj = self.pool.get('gt.route.psinrange')
        support = support_obj.browse(cr, uid, support_id)
        if support:
            support_obj.write(cr, uid, support_id, {'state': 'confirmed', 'support_partner_id': ps_id})

            #ELIMINO LOS REGISTROS DE LA TABLA TEMPORAL PS_INRANGE
            prids = []
            for pr in support.travel_id.route_id.partners_inrange:
                prids.append(pr.id)
            psinrange_obj.unlink(cr, uid, prids)

            # ACTUALIZO LOS VIAJES POSTERIORES AL VIAJE DE RELEVO AL NUEVO PS
            travels = []
            for t in support.travel_id.route_id.travel_ids:
                if t.id > support.travel_id.id:
                    travels.append(t.id)
            travel_obj.write(cr, uid, travels, {'sp_partner_id': ps_id})

            route_obj.mobile_notify_ps_route(cr, uid, support.original_partner_id.id, ps_id,
                                             support.travel_id.route_id.id, 'gt.service.partner')
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Ha aceptado un relevo satisfactoriamente",
                }
            )
        return res

    def mobile_notify_list(self, cr, uid, ps_id):
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener los mensajes"
        }
        notify_obj = self.pool.get('gt.mobile.notify')
        nots_ids=notify_obj.search(cr, uid, [('type','=','PS'),('service_partner_id','=',ps_id)])
        nots=[]
        if ps_id and len(nots_ids) > 0:
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



