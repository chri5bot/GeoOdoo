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
import pytz
from pytz import UTC
import openerp.tools as tools
from customer import *
import json
import logging
_logger = logging.getLogger(__name__)


class RouteMobile(osv.osv):
    _name = 'gt.route'
    _inherit = ['gt.route', 'gcm.common']

    def to_mobile_date(self, cr, uid, model_date):
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

    def update_partners_response(self, cr, uid, context=None):
        ps_inrange_obj = self.pool.get('gt.route.psinrange')
        route_ps_tuples = self.check_partners_timeout(cr, uid, seconds_wait=30, context=None)
        _logger.debug('\n\r:RUNJOB-->update_partners_response: check_partners_timeout:{0}'.format(str(route_ps_tuples)))
        for tup in route_ps_tuples:
            ps_inrange_obj.write(cr, uid, tup[0], {'state': 'timeout'})

            _logger.debug('\n\r-------->update_partners_response: act_search %s', tup)
            found = self.act_search(cr, uid, tup[2])
            if found:
                self.mobile_notify_route(cr, uid, tup[2])
                _logger.debug('\n\r-------->update_partners_response: found %s', tup)
            else:
                _logger.debug('\n\r-------->update_partners_response: NOT FOUND %s', tup)

        return True

    def mobile_createroute(self, cr, uid, strdto):
        res = {
                    'IsGranted': False,
                    'Message': "Error: No se pudo calcular la ruta"
                }
        #try:
        dto = json.loads(strdto)
        #except:
        #    dto = False

        if dto and "ListTravelDTOs" in dto.keys():
            travel_count=0
            travel_obj = self.pool.get('gt.travel')
            service_type_ids = self.pool.get('gt.service.type').search(cr, uid, [('code', '=', dto["ServiceTypeId"])])
            route_values = {
                "service_type": service_type_ids[0],
                "customer_partner_id": dto["CustomerId"],
                "request_date": self.to_openerp_date(cr,uid,dto["DateTime"]),
                "length": dto["Kilometers"],
                "state": "new",
                "payment_type": dto["PaymentType"],
            }
            route_id = self.create(cr, uid, route_values)
            orden = 0
            for travel in dto["ListTravelDTOs"]:
                travel_count+=1
                orden += 1
                travel_values = {
                    "route_id": route_id,
                    "sp_partner_id": False,
                    "kilometers_km": travel["TravelKilometers"],
                    "estimated_km": travel["TravelKilometers"],
                    "order": orden,
                }
                if travel["Source"]:
                    lng = travel["Source"]["Longitude"]
                    lat = travel["Source"]["Latitude"]
                    # POSTGRES GUARDA LONGITUD LATITUD
                    # SE ARMA EL TEXTO 'POINT(-78.476947 -0.182862)' donde "POINT(Longitud Latitud)"
                    point_start = travel_obj.parse_geopoint_from_google(cr, uid, "POINT({0} {1})".format(lng, lat))
                    travel_values.update({
                        "reference_begin": travel["Source"]["Reference"],
                        "contact_begin": travel["Source"]["Contact"],
                        "description_begin": travel["Source"]["Instructions"],
                        "geo_point_start": point_start,
                    })

                if travel["Destination"]:
                    lng = travel["Destination"]["Longitude"]
                    lat = travel["Destination"]["Latitude"]
                    # POSTGRES GUARDA LONGITUD LATITUD
                    # SE ARMA EL TEXTO 'POINT(-78.476947 -0.182862)' donde "POINT(Longitud Latitud)"
                    point_end = travel_obj.parse_geopoint_from_google(cr, uid, "POINT({0} {1})".format(lng, lat))
                    travel_values.update({
                        "reference_end": travel["Destination"]["Reference"],
                        "contact_end": travel["Destination"]["Contact"],
                        "description_end": travel["Destination"]["Instructions"],
                        "geo_point_end": point_end,
                    })
                #GUARDO EL VIAJE
                travel_id = travel_obj.create(cr, uid, travel_values)

                # # ACTUALIZO LAS POSICIONES GPS DEL VIAJE
                # if travel["Source"]:
                #     lng = travel["Source"]["Longitude"]
                #     lat = travel["Source"]["Latitude"]
                #     #POSTGRES GUARDA LONGITUD LATITUD
                #     # SE ARMA EL TEXTO 'POINT(-78.476947 -0.182862)' donde "POINT(Longitud Latitud)"
                #     travel_obj.update_geopoint_from_google(cr, uid, travel_id, 'geo_point_start',
                #                                            "POINT({0} {1})".format(lng, lat))
                # if travel["Destination"]:
                #     lng = travel["Destination"]["Longitude"]
                #     lat = travel["Destination"]["Latitude"]
                #     travel_obj.update_geopoint_from_google(cr, uid, travel_id, 'geo_point_end',
                #                                            "POINT({0} {1})".format(lng, lat))

            quote = self.get_quotation(cr, uid, [route_id])
            self.write(cr, uid, [route_id], quote)
            self.distribute_travels_costs(cr, uid, [route_id])
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa",
                    'Cost': str(quote["total_cost"]),
                    'Waits': travel_count+1,
                    'RouteId': route_id,
                }
            )
        _logger.debug('-------->mobile_createroute:%s', res)
        return res

    def mobile_confirmroute(self, cr, uid, routeid, payment_type):
        customer_obj = self.pool.get('gt.customer')
        findpartners=False
        res = {}
        res.update(
            {
                'IsGranted': False,
                'Message': "Error: No se pudo confirmar la ruta"
            })
        if routeid:
            route = self.browse(cr, uid, routeid)
            distances = [2500, 3500, 4500]
            if route:
                for dist in distances:
                    self.write(cr, uid, [routeid], {'payment_type': payment_type})
                    #NOTIFICO QUE EXTIENDO LA BUSQUEDA SOLO DESDE LA SEGUNDA DISTANCIA
                    if dist != distances[0]:
                        self.mobile_notify_extend_search(cr, uid, route.customer_partner_id.id, dist, 'gt.customer')
                    findpartners = self.act_search(cr, uid, route.id, distance=dist)
                    if findpartners:
                        send = self.mobile_notify_route(cr, uid, route.id,)
                        if send:
                            res.update(
                                {
                                    'IsGranted': True,
                                    'Title': "Buscando Proveedor de Servicio en su área",
                                    'Message': "Por favor espere...",
                                }
                            )
                            break
                        else:
                            pass

                if not findpartners:
                    self.mobile_notify_no_partner(cr, uid, route.customer_partner_id.id, 'gt.customer')
        return res

    def mobile_active_routes(self, cr, uid, customer_id):
        res = {}
        active_routes = []
        user = self.pool.get('res.users').browse(cr, uid, uid)
        local_tz = pytz.timezone(user.partner_id.tz)
        routeids = self.search(cr, uid, [('customer_partner_id', '=', customer_id),
                                         ('state', '=', 'inprogress')])
        routes = self.browse(cr, uid, routeids)
        for route in routes:
            routeinfo = {'Id': route.id,
                         'ServiceTypeName': route.service_type.name,
                         'DateTime': self.to_mobile_date(cr, uid, route.request_date),
                         'Kilometers': route.length,
                         'Price': str(round(route.total_cost))
                         }
            active_routes.append(routeinfo.copy())
        if not customer_id:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "Error: No se pudo obtener los datos del cliente"
                }
            )
        else:
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Conexion Exitosa",
                    'RouteList': active_routes,
                }
            )
        return res

    def mobile_last_routes(self, cr, uid, customer_id, number=15):
        res={
                'IsGranted': False,
                'Message': "Error: No se pudo obtener los datos del cliente"
            }

        listroutes = []
        service_partner_obj = self.pool.get('gt.service.partner')
        routeids = self.search(cr, uid, [('customer_partner_id', '=', customer_id)])
        routes = self.browse(cr, uid, routeids)
        i = 0
        for route in routes:
            if i < number:
                hasPS=False
                service_partner = service_partner_obj.browse(cr, uid, route.travel_ids[0].sp_partner_id.id)
                if route.travel_ids[0].sp_partner_id.id:
                    hasPS = True
                routeinfo = {'RouteId': route.id,
                             'HasProviderService': hasPS,
                             'ServiceTypeName': route.service_type.name,
                             'ProviderServicePhoto': service_partner.image_medium,
                             'ProviderServiceRanking': str(service_partner.ranking),
                             'DateTime': self.to_mobile_date(cr, uid, route.request_date),
                             'Kilometers': str(route.length), 'Price': str(route.total_cost)}
                listroutes.append(routeinfo.copy())

        res.update(
            {
                'IsGranted': True,
                'Message': "Conexion Exitosa",
                'HistoricalRoutes': listroutes,
            }
        )
        _logger.debug('-------->mobile_last_routes\n\r %s', res)
        return res

    def mobile_route(self, cr, uid, route_id):
        res = {
                    'IsGranted': False,
                    'Message': "Error: No se pudo obtener los datos del cliente"
                }
        route = self.browse(cr, uid, route_id)
        travel_obj = self.pool.get('gt.travel')
        if route and route.id:
            waits = len(route.travel_ids) + 1
            active_travel = self.get_active_travel(cr, uid, [route.id])
            travels = []
            for travel in route.travel_ids:
                lng_ori, lat_ori = travel_obj.get_geopoint_to_google(cr, uid, travel.id, 'geo_point_start')
                lng_dest, lat_dest = travel_obj.get_geopoint_to_google(cr, uid, travel.id, 'geo_point_end')
                t = {
                    "TravelId": travel.id,
                    "ServicePartnerId": travel.sp_partner_id.id,
                    "Source": {
                        "Address": travel.geocode_begin,
                        "Contact": travel.contact_begin,
                        "Reference": travel.reference_begin,
                        "Instructions": travel.description_begin,
                        "Longitude": str(lng_ori),
                        "Latitude": str(lat_ori)},
                    "Destination": {
                        "Address": travel.geocode_end,
                        "Contact": travel.contact_end,
                        "Reference": travel.reference_end,
                        "Instructions": travel.description_end,
                        "Longitude": str(lng_dest),
                        "Latitude": str(lat_dest)}
                }
                travels.append(t)
                r = {
                    "ServiceTypeId": route.service_type.code,
                    "ServiceTypeName": route.service_type.name,
                    "RouteId": route.id,
                    "Cost": str(route.total_cost),
                    "Waits": waits,
                    "Kilometers": str(route.length),
                    "CustomerId": route.customer_partner_id.id,
                    "DateTime": self.to_mobile_date(cr, uid, route.request_date),
                    "ListTravelDTOs": travels
                }
                if active_travel:
                    r.update(
                        {
                            "ServicePartnerId": active_travel.sp_partner_id.id,
                            "CurrentPSFacePic": active_travel.sp_partner_id.image_medium,
                            "CurrentPSVehiclePic": active_travel.sp_partner_id.vehicle_ids[0].photo_vehicle_medium,
                        }
                    )
                else:
                    done_travel = self.get_done_travel(cr, uid, [route.id])
                    r.update(
                        {
                            "ServicePartnerId": done_travel.sp_partner_id.id,
                            "CurrentPSFacePic": done_travel.sp_partner_id.image_medium,
                            "CurrentPSVehiclePic": done_travel.sp_partner_id.vehicle_ids[0].photo_vehicle_medium,
                        }
                    )
                res.update(
                    {
                        'IsGranted': True,
                        'Message': "Conexion Exitosa",
                        'Route': r
                    }
                )
        return res

    def mobile_notify_route(self, cr, uid, routeid, context=None):
        sended = False
        travel_obj = self.pool.get('gt.travel')
        notification = {}
        travels = []
        route = self.browse(cr, uid, routeid)
        for travel in route.travel_ids:
            lng_ori, lat_ori = travel_obj.get_geopoint_to_google(cr, uid, travel.id, 'geo_point_start')
            lng_end, lat_end = travel_obj.get_geopoint_to_google(cr, uid, travel.id, 'geo_point_end')

            travels.append(
                (travel.reference_begin, travel.contact_begin, travel.description_begin, lng_ori, lat_ori, travel.id)
            )

            travels.append(
                (travel.reference_end, travel.contact_end, travel.description_end, lng_end, lat_end, travel.id)
            )

        notification.update(
            {
                'Type': 2,
                'CollapseKey': "travel",
                'Title': "Nuevo Viaje Solicitado",
                'Message': "Cliente esperando PS",
                'Route': travels,
                'Kilometers': route.length,
                'Price': route.total_cost,
                'ServiceTypes': route.service_type.name,
                'RouteId': route.id,
                'IsSupport': False,
                'SupportId': 0,
            }
        )
        if route.partners_inrange and len(route.partners_inrange)>0:
            pr = route.partners_inrange[0]
            if 'active' == pr.service_partner_id.state and 'wait' == pr.state:
                spobj = self.pool.get('gt.service.partner')
                notification.update(
                    {
                        'PlateRestriction': pr.service_partner_id.pico_placa,
                        'PlateRestrictionMessage': pr.service_partner_id.message_pico_placa,
                    })
                sended = spobj.action_send_message(cr, uid, [pr.service_partner_id.id], notification, context)

        return sended

    def mobile_notify_support(self, cr, uid, supportid, context=None):
        travel_obj = self.pool.get('gt.travel')
        support_obj = self.pool.get('gt.travel.support')
        notification = {}
        travels = []
        support = support_obj.browse(cr, uid, supportid)
        route = self.browse(cr, uid, support.travel_id.route_id.id)
        lng_ori, lat_ori = support_obj.get_geopoint_to_google(cr, uid, support.id, 'geo_point')
        ps_name = support.original_partner_id.name + ' ' + support.original_partner_id.last_name

        travels.append((support.geocode, ps_name, 'Relevar Proveedor', lng_ori, lat_ori, -1, True))
        #travels.append((support.geocode, ps_name, 'Relevar Proveedor', lng_ori, lat_ori, -1, True))
        isfirst = False
        for travel in route.travel_ids:
            if travel.state == 'inprogress':
                lng_ori, lat_ori = travel_obj.get_geopoint_to_google(cr, uid, travel.id, 'geo_point_start')
                travels.append(
                    (travel.reference_begin, travel.contact_begin, travel.description_begin, lng_ori, lat_ori,
                     travel.id)
                )
                if not isfirst:
                    isfirst = True
                    travels.append(
                        (travel.reference_begin, travel.contact_begin, travel.description_begin, lng_ori, lat_ori,
                         travel.id)
                    )

                lng_end, lat_end = travel_obj.get_geopoint_to_google(cr, uid, travel.id, 'geo_point_end')
                travels.append(
                    (travel.reference_end, travel.contact_end, travel.description_end, lng_end, lat_end, travel.id)
                )


        notification.update(
            {
                'Type': 2,
                'CollapseKey': "travel",
                'Title': "Relevo Solicitado",
                'Message': "Proveedor esperando PS",
                'Route': travels,
                'Kilometers': route.length,
                'Price': route.total_cost,
                'ServiceTypes': route.service_type.name,
                'RouteId': route.id,
                'IsSupport': True,
                'SupportId': supportid,
            }
        )
        if route.partners_inrange and len(route.partners_inrange) > 0:
            pr = route.partners_inrange[0]
            if 'active' == pr.service_partner_id.state and 'wait' == pr.state:
                spobj = self.pool.get('gt.service.partner')
                notification.update(
                    {
                        'PlateRestriction': pr.service_partner_id.pico_placa,
                        'PlateRestrictionMessage': pr.service_partner_id.message_pico_placa,
                    }
                )
                spobj.action_send_message(cr, uid, [pr.service_partner_id.id], notification, context)
        return True

    def mobile_getchat(self, cr, uid, routeid):
        res = {
                    'IsGranted': False,
                    'Message': "Error: No se pudo obtener los mensajes"
                }
        route = self.browse(cr, uid, routeid)
        chats = []
        if route.chat_ids and len(route.chat_ids) > 0:
            res = {}
            for line in route.chat_ids:
                chats.append({
                    'ChatType': line.type,
                    'Message': line.message,
                    'DateTime': self.to_mobile_date(cr, uid, line.date)})

            res.update(
                {
                    'IsGranted': True,
                    'Message': "Lista de mensajes",
                    'Chats': chats
                }
            )
        return res

    def mobile_sendchat(self, cr, uid, routeid, ps_id, type, message):
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo crear al mensaje"
        }
        chat_obj = self.pool.get('gt.chat.line')
        chat_value = {
            'route_id': routeid,
            'service_partner_id': ps_id,
            'type': type,
            'message': message,
            'date': self.to_openerp_date(cr, uid, datetime.now()),
        }
        chat_id = chat_obj.create(cr, uid, chat_value)
        try:
            self.mobile_notify_chat(cr, uid, chat_id)
        except:
            print (u'Alerta', u'No hay usuarios disponibles')
        if chat_id:
            res.update(
                    {
                        'IsGranted': True,
                        'Message': "Mensaje creado",
                    }
                )
        return res

    def mobile_notify_chat(self, cr, uid, chat_id, context=None):
        chatline = self.pool.get('gt.chat.line').browse(cr, uid, chat_id)
        if chatline.type == "PS":
            title = "Nuevo chat del proveedor"
        else:
            title = "Nuevo chat del usuario"
        notification = {
            "Type": 6,
            "RouteId": chatline.route_id.id,
            "CollapseKey": "Chat de T-Llevo",
            "Title": title,
            "Message": chatline.message,
            "ChatType": chatline.type,
        }
        ids = []
        if chatline.type == "US":
            ids.append(chatline.service_partner_id.id)
            self.pool.get('gt.service.partner').action_send_message(cr, uid, ids, notification, context)
        else:
            ids.append(chatline.route_id.customer_partner_id.id)
            self.pool.get('gt.customer').action_send_message(cr, uid, ids, notification, context)
        return True

    def mobile_receive_chat_message(self, cr, uid, route_id, chat_type, message, date_time):
        ids = []
        res = {
            'IsGranted': False,
            'Message': "Error: el mensaje no ha sido registrado"
        }
        chatobj = self.pool.get('gt.chat.line')
        travelobj = self.pool.get('gt.travel')
        travelids = travelobj.search(cr, uid, [('route_id', '=', route_id)])
        travel = travelobj.browse(cr, uid, travelids)
        if travel:
            chat_id = chatobj.create(cr, uid, {'route_id': route_id, 'type': chat_type,
                                               'service_partner_id': travel[0].sp_partner_id.id,
                                               'message': message, 'date': date_time})
            chatline = chatobj.browse(cr, uid, chat_id)
            if chatline.type == "PS":
                title = "Nuevo chat del proveedor"
            else:
                title = "Nuevo chat del usuario"
            notification = {
                "Type": 6,
                "RouteId": chatline.route_id.id,
                "CollapseKey": "Chat de T-Llevo",
                "Title": title,
                "Message": chatline.message,
                "ChatType": chatline.type,
            }
            if chatline.type == "US":
                ids.append(chatline.service_partner_id.id)
                self.pool.get('gt.service.partner').action_send_message(cr, uid, ids, notification, context=None)
            else:
                ids.append(chatline.route_id.customer_partner_id.id)
                self.pool.get('gt.customer').action_send_message(cr, uid, ids, notification, context=None)
            res.update(
                {
                    'IsGranted': True,
                    'Message': "El mensaje ha sido registrado exitosamente"
                }
            )
        return res

    def mobile_getmessage_binnacle(self, cr, uid, routeid):
        res = {
            'IsGranted': False,
            'Message': "Error: No se pudo obtener los mensajes de la bitácora"
        }
        route = self.browse(cr, uid, routeid)
        binnacles = []
        if route.binnacle_ids and len(route.binnacle_ids) > 0:
            for binnacle in route.binnacle_ids:
                binnacles.append({
                    'BinnacleType': binnacle.type,
                    'Message': binnacle.message,
                    'DateTime': self.to_mobile_date(cr, uid, binnacle.date)})

            res.update(
                {
                    'IsGranted': True,
                    'Message': "Bitácora",
                    'Binnacles': binnacles,
                }
            )
        return res

    def mobile_write_binnacle(self, cr, uid, travel_id, message, code):
        res = {
            'IsGranted': True,
            'Message': "Se ha registrado en la bitácora"
        }
        binnacle = self.pool.get('gt.binnacle')
        travelobj = self.pool.get('gt.travel')
        # TRAVEL -1 ES CUANDO ES EL PRIMER VIAJE DE RELEVO
        if travel_id != -1:
            travel = travelobj.browse(cr, uid, travel_id)
            if travel:
                binnacle.create(cr, uid, {'route_id': travel.route_id.id, 'type': 'PS',
                                          'service_partner_id': travel.sp_partner_id.id,
                                          'message': message})
                if code == 2:
                    travelobj.write(cr, uid, [travel.id], {'state': 'done'})
                if code == 3:
                    travelobj.write(cr, uid, [travel.id], {'state': 'done'})
                    self.write(cr, uid, [travel.route_id.id], {'state': 'done'})
            else:
                res.update({
                    'IsGranted': False,
                    'Message': "Error: No existen viajes con esa identificación"
                })
        return res

    def mobile_notify_ps_route(self, cr, uid, dest_id, ps_id, route_id, model):
        notification = {
            "Type": 5,
            "CollapseKey": "route_notify",
            "Title": "Notificacion de Ruta",
            "Message": "Hemos encontrado un Proveedor de Servicio",
            "ProviderServiceId": ps_id,
            "RouteId": route_id,
        }
        _logger.debug('DEBUG-----> {0} \n\r'.format(notification), exc_info=False)
        self.pool.get(model).action_send_message(cr, uid, [dest_id], notification)
        return True

    def mobile_notify_extend_search(self, cr, uid, dest_id, distance, model):
        notification = {
            "Type": 7,
            "CollapseKey": "route_notify",
            "Title": "Extendiendo Rango de Busqueda",
            "Message": "En {0} KM".format(distance / 1000.),
        }
        _logger.debug('DEBUG-----> {0} \n\r'.format(notification), exc_info=False)
        self.pool.get(model).action_send_message(cr, uid, [dest_id], notification)
        return True

    def mobile_notify_no_partner(self, cr, uid, dest_id, model):
        notification = {
            "Type": 8,
            "CollapseKey": "route_notify",
            'Title': "No encontramos un Proveedor de Servicio en su área",
            'Message': "Por favor intente mas tarde",
        }
        _logger.debug('DEBUG-----\n\r{0} '.format(notification), exc_info=False)
        self.pool.get(model).action_send_message(cr, uid, [dest_id], notification)
        return True

    def qualify_route(self, cr, uid, route_id, qualification):
        res = {
            'IsGranted': False,
            'Message': "No se ha conseguido la ruta o la calificación"
        }
        route = self.browse(cr, uid, route_id)
        if route:
            self.write(cr, uid, [route_id], {'ps_qualification': qualification})
            res.update(
                {
                    'IsGranted': True,
                    'Message': "Se ha calificado satisfactoriamente"
                }
            )
        else:
            res.update(
                {
                    'IsGranted': False,
                    'Message': "No existe esa ruta"
                }
            )
        return res
