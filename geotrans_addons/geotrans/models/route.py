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
from base_geoengine import geo_model
import pytz
from pytz import UTC
from openerp.tools.float_utils import float_round as round
from geotrans import *
from rate import *
from partner import *
import logging
_logger = logging.getLogger(__name__)

_STATEROUTE = [('new', 'Solicitado'), ('searching', 'Buscando'), ('confirmed', 'Aceptado'), ('inprogress', 'En Curso'),
               ('done', 'Realizado'), ('cancel', 'Cancelado')]

_STATETRAVEL = [('new', 'Solicitado'),('searching', 'Buscando'), ('confirmed', 'Confirmado'), ('inprogress', 'En Curso'),
                ('done', 'Realizado'), ('invoiced', 'Facturado'), ('cancel', 'Cancelado')]

_STATESUPPORT = [('new', 'Solicitado'), ('searching', 'Buscando'), ('confirmed', 'Confirmado'), ('cancel', 'Cancelado')]

_PAYMEMTTYPE = [('cash', 'Efectivo'), ('credit_card', 'Tarjeta de crédito')]

_QUALIFICATIONTRAVEL = [('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')]


class RoutePsInrange(osv.osv):
    _name = 'gt.route.psinrange'
    _description = 'Proveedores de servicio en rango'
    _columns = dict(
        route_id=fields.many2one('gt.route', string='Ruta', help="Ruta"),
        service_partner_id=fields.many2one('gt.service.partner', string='Proveedor', required=True,
                                           help=u'Proveedor de servicio en rango de la ruta'),
        state=fields.selection([('wait', 'Espera'), ('timeout', 'Tiempo Agotado'), ('invalid', 'Inválido'),
                                ('acepted', 'Aceptado')], 'Estado', readonly=False, track_visibility='onchange',
                               help=u'Estado actual del PS en la ruta'),
    )


class Route(osv.osv):
    _name = 'gt.route'
    _description = 'Ruta que agrupa viajes'
    _inherit = ['gt.geoutils']

    def _get_total(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = obj.km_cost + obj.wait_cost
        return res

    def _get_length(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            km=0.0
            for tvl in obj.travel_ids:
                if tvl.estimated_km:
                    km = km+tvl.estimated_km
            res[obj.id] = km
        return res

    _columns = dict(
        service_type=fields.many2one('gt.service.type', required=True, string='Tipo de Servicio'),
        customer_partner_id=fields.many2one('gt.customer', string='Cliente', required=True,
                                            help=u'Cliente que solicita la ruta'),
        request_date=fields.datetime('Fecha Solicitud', required=True, help=u'Fecha de solicitud de Ruta'),
        travel_ids=fields.one2many('gt.travel', 'route_id', string='Viaje', help=u'Seleccione el viaje'),
        payment_type=fields.selection(_PAYMEMTTYPE, string='Tipo de pago', help=u'Seleccione el tipo de pago'),
        state=fields.selection(_STATEROUTE, 'Estado de Ruta', readonly=False, track_visibility='onchange',
                             help=u'Estado actual de la ruta'),
        rate=fields.float(string='Tarifa Usuario', readonly=True, help=u'Tarifa aplicada en la ruta'),
        rate_ps=fields.float(string='Tarifa PS', readonly=True, help=u'Tarifa aplicada en el servicio'),
        surcharge=fields.char('Recargo o descuento %', readonly=True,
                               help=u'Recargos o descuentos aplicados a la ruta en la cotización'),
        length=fields.function(_get_length, method=True,type='float', string='Longitud de la Ruta',
                               help=u'Longitud de la ruta en kilómetros'),
        km_cost=fields.float('Precio de Kms', readonly=True, help=u'Precio de la ruta según la tarifa aplicada'),
        wait_cost=fields.float('Precio de las esperas', readonly=True,
                               help=u'Precio de la ruta según la tarifa aplicada'),
        km_cost_ps=fields.float('Costo Servicio Kms', readonly=True, help=u'Costo de la ruta según la tarifa aplicada'),
        wait_cost_ps=fields.float('Costo Servicio esperas', readonly=True,
                                  help=u'Costo de la ruta según la tarifa aplicada'),
        total_cost_ps=fields.float(string='Costo Total PS', help=u'Costo Total del servicio de la compañía al PS'),
        total_cost=fields.float(string='Precio Total', help=u'Precio Total de la Ruta'),
        chat_ids=fields.one2many('gt.chat.line', 'route_id', string='Chat'),
        binnacle_ids=fields.one2many('gt.binnacle', 'route_id', string='Bitácora'),
        rejection_ids=fields.one2many('gt.route.rejection', 'route_id', string='Rechazos'),
        partners_inrange=fields.one2many('gt.route.psinrange','route_id', string='Proveedores en Rango'),
        ps_qualification=fields.selection(_QUALIFICATIONTRAVEL, string='Calificación de la ruta',
                                          help=u'Ingrese la calificación del viaje'),
    )

    _defaults = dict(
        state='new'
    )

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        local_tz = pytz.timezone('America/Guayaquil')
        if context and "tz" in context.keys():
            local_tz = pytz.timezone(context["tz"])

        for route in self.browse(cr, uid, ids, context=context):
            if route.customer_partner_id and route.request_date:
                fecha_ruta = datetime.strptime(route.request_date, '%Y-%m-%d %H:%M:%S')
                fecha_ruta = UTC.localize(fecha_ruta, is_dst=False)
                result[route.id] = route.customer_partner_id.name_get()[0][1] + "[" + fecha_ruta.astimezone(local_tz).strftime('%Y-%m-%d %H:%M:%S')+ "]"
            else:
                result[route.id] = "Ruta:"+route.id
        return result.items()

    def get_active_travel(self, cr, uid, ids, context=None):
        for route in self.browse(cr, uid, ids, context):
            for travel in route.travel_ids:
                if 'inprogress' == travel.state:
                    return travel
        return False

    def get_done_travel(self, cr, uid, ids, context=None):
        travels = []
        for route in self.browse(cr, uid, ids, context):
            for travel in route.travel_ids:
                if 'done' == travel.state:
                    travels.append(travel)
            return travels[-1]
        return False

    def distribute_travels_costs(self, cr, uid, ids, context=None):
        travel_obj = self.pool.get('gt.travel')
        km_cost_ps = wait_cost_ps = total_cost_ps = 0.0

        if isinstance(ids, int) or isinstance(ids, long):
            ids = [ids]
        for route in self.browse(cr, uid, ids):
            if route.length > 0:
                for travel in route.travel_ids:

                    factor = travel.estimated_km/route.length
                    km_cost_ps += round(route.km_cost_ps * factor, 2)
                    wait_cost_ps += round(route.wait_cost_ps * factor, 2)
                    total_cost_ps += round(route.total_cost_ps * factor, 2)

                    values = {
                        'km_cost_ps': round(route.km_cost_ps * factor, 2),
                        'wait_cost_ps': round(route.wait_cost_ps * factor, 2),
                        'total_cost_ps': round(route.total_cost_ps * factor, 2),
                    }
                    travel_obj.write(cr, uid, [travel.id], values)


                # AJUSTO EN EL ULTIMO VIAJE PARA QUE CUADREN CENTAVOS
                dif_km_cost_ps = round(route.km_cost_ps, 2)-km_cost_ps
                dif_wait_cost_ps = round(route.wait_cost_ps, 2)-wait_cost_ps
                dif_total_cost_ps = round(route.total_cost_ps, 2)-total_cost_ps
                values = {
                    'km_cost_ps': round(route.km_cost_ps * factor, 2)+dif_km_cost_ps,
                    'wait_cost_ps': round(route.wait_cost_ps * factor, 2)+dif_wait_cost_ps,
                    'total_cost_ps': round(route.total_cost_ps * factor, 2)+dif_total_cost_ps,
                }
                travel_obj.write(cr, uid, [travel.id], values)
        return True

    def act_quote(self, cr, uid, ids, context=None):
        if isinstance(ids, int) or isinstance(ids, long):
            ids = [ids]
        for route in self.browse(cr, uid, ids):
            quote = self.get_quotation(cr, uid, [route.id], context)
            if quote:
                self.write(cr, uid, [route.id], quote, context)
                self.distribute_travels_costs(cr, uid, [route.id])
            else:
                raise osv.except_osv('Error!', u"No se pudo actualizar la cotización")
        return True

    def act_search(self, cr, uid, ids, distance=2500, context=None):
        travel_obj = self.pool.get('gt.travel')
        psinrange_obj = self.pool.get('gt.route.psinrange')
        res = {}
        if isinstance(ids, int) or isinstance(ids, long):
            ids = [ids]
        for route in self.browse(cr, uid, ids, context=context):
            travels = []
            for travel in route.travel_ids:
                travels.append(travel.id)
            #travel_obj.write(cr, uid, [route.travel_ids[0].id], {'state': 'searching'}, context)
            sp_ids = travel_obj.find_partners_inrange(cr, uid, route.travel_ids[0].id, route.id, distance=distance, context=context)
            #VERIFICA SALDO SOLO TOMO EL PS MAS CERCANO (EL PRIMERO)
            if len(sp_ids) > 0:
                psinrange_obj.create(cr, uid, {'route_id': route.id, 'service_partner_id': sp_ids[0], 'state': 'wait'})
                res.update({str(route.id): sp_ids[0]})
            else:
                return False
            self.write(cr, uid, ids, {'state': 'searching'}, context)

        return res

    def get_quotation(self, cr, uid, ids, context=None):
        result = {}
        obj_service_conf = self.pool.get('gt.service.configuration')
        for routeobj in self.browse(cr, uid, ids, context):
            result = obj_service_conf.calculate_quotation(cr, uid, len(routeobj.travel_ids)+1,
                                                          routeobj.length,
                                                          routeobj.request_date,
                                                          routeobj.service_type.id,
                                                          context=context)

        return result

    def check_partners_timeout(self, cr, uid, seconds_wait=30, context=None):

        res = []
        sql = " SELECT pr.id,sp.id,pr.route_id FROM gt_service_partner sp  LEFT JOIN res_partner p ON p.id=sp.partner_id" \
              " LEFT JOIN gt_route_psinrange pr ON sp.id = pr.service_partner_id " \
              " LEFT JOIN gt_route r ON r.id=pr.route_id  WHERE r.state='searching' AND pr.state='wait' " \
              " AND EXTRACT(EPOCH FROM ((now() AT TIME ZONE 'UTC')::timestamp)-pr.write_date)>{0}" \
              " AND sp.id not in (select service_partner_id from gt_route_rejection where route_id=pr.route_id)" \
              "".format(seconds_wait)
        cr.execute(sql)
        reslist = cr.fetchall()
        for l in reslist:
            res.append(l)
        return res


class Travel(geo_model.GeoModel):
    _name = 'gt.travel'
    _description = 'Viajes'
    _inherit = ['gt.geoutils']

    _columns = dict(
        route_id=fields.many2one('gt.route', string='Ruta', help="Ruta a la que pertenece el viaje"),
        geo_point_start=fields.geo_point('Posición Inicial'),
        geo_point_end=fields.geo_point('Posición Final'),
        sp_partner_id=fields.many2one('gt.service.partner', string='Proveedor de Servicio',
                                      help=u'Proveedor de servicio que iniciara el viaje'),
        kilometers_km=fields.float('Kilometros Recorridos', required=True,
                                   help=u'Kilometros recorridos del viaje'),
        estimated_km=fields.float('Kilometros Estimados', required=True,
                                  help=u'Kilometros estimados del viaje'),
        geocode_begin=fields.char('Geocode Origen', required=False,
                                      help=u'Geocode inicial del viaje'),
        geocode_end=fields.char('Geocode Destino', required=False,
                                    help=u'Geocode destino del viaje'),
        description_begin=fields.text('Instrucción Origen', required=False, size=100,
                                      help=u'Instrucción inicial del viaje'),
        description_end=fields.text('Instrucción Destino', required=False, size=100,
                                    help=u'Instrucción en destino del viaje'),
        reference_begin=fields.char('Referencia Origen', required=False, size=100,
                                    help=u'Referencia de direccion del origen'),
        reference_end=fields.char('Referencia Destino', required=False, size=100,
                                  help=u'Referencia de direccion del destino'),
        contact_begin=fields.char('Contacto Origen', required=False, size=100,
                                    help=u'Persona de contacto en direccion origen'),
        contact_end=fields.char('Contacto Destino', required=False, size=100,
                                  help=u'Persona de contacto en direccion destino'),
        ps_observation=fields.text('Observación del PS', required=False, size=100,
                                   help=u'Observación por parte del PS'),
        state=fields.selection(_STATETRAVEL, 'Estado del Viaje', readonly=False, track_visibility='onchange',
                               help=u'Estado actual del viaje'),
        km_cost_ps=fields.float('Costo Servicio Kms', readonly=True, help=u'Costo del viaje, según la tarifa aplicada'),
        wait_cost_ps=fields.float('Costo Servicio esperas', readonly=True,
                                  help=u'Costo de esperas del viaje según la tarifa aplicada'),
        total_cost_ps=fields.float(string='Costo Total PS', help=u'Costo Total del servicio de la compañía al PS'),
        order=fields.integer(string='Orden', help=u'Orden del viaje dentro de la ruta')

    )
    _defaults = dict(
        state='new'
    )

    def act_confirm(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'confirmed'}, context)
        return True

    def act_inprogress(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'inprogress'}, context)
        return True

    def act_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context)
        return True

    def act_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'}, context)
        return True

    def act_invoiced(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'invoiced'}, context)
        return True

    def find_partners_inrange(self, cr, uid, id, route_id, distance=2500, context=None):
        res = []
        if distance == 3500:
            pass
        sql = " SELECT sp.id FROM gt_service_partner sp LEFT JOIN res_partner p ON p.id=sp.partner_id" \
              " LEFT JOIN gt_travel t ON ST_DWithin(p.geo_point, t.geo_point_start, {0})" \
              " WHERE t.id={1} AND sp.partner_active = TRUE" \
              " AND sp.id not in (select service_partner_id from gt_route_rejection where route_id= {2}) " \
              " AND sp.id not in (select service_partner_id from gt_route_psinrange where route_id= {2} and state='timeout') " \
              " ORDER BY ST_Distance(p.geo_point, t.geo_point_start)".format(distance, id, route_id)
        cr.execute(sql)
        list = cr.fetchall()
        for l in list:
            res.append(l[0])
        return res


class Support(geo_model.GeoModel):
    _name = 'gt.travel.support'
    _description = 'Relevo de Viaje'
    _inherit = ['gt.geoutils']

    _columns = dict(
        travel_id=fields.many2one('gt.travel', string='Viaje', help=u"Viaje al que se realiza el soporte"),
        geo_point=fields.geo_point('Posición Solicitud'),
        geocode=fields.char('Geocode', required=False,
                            help=u'Geocode del punto de solicitud del relevo'),
        original_partner_id=fields.many2one('gt.service.partner', string='Proveedor de Servicio Original',
                                            help=u'Proveedor de servicio que inicia el viaje'),
        support_partner_id=fields.many2one('gt.service.partner', string='Proveedor de Servicio Relevo',
                                           help=u'Proveedor de servicio que realiza el relevo el viaje'),
        state=fields.selection(_STATETRAVEL, 'Estado del Viaje', readonly=False, track_visibility='onchange',
                               help=u'Estado actual del viaje'),
    )

    def act_support_search(self, cr, uid, ids, ps_id, distance=2500, context=None):
        psinrange_obj = self.pool.get('gt.route.psinrange')
        res = {}
        if isinstance(ids, int) or isinstance(ids, long):
            ids = [ids]
        for support in self.browse(cr, uid, ids, context=context):
            sp_ids = self.find_partners_inrange(cr, uid,
                                                support.id,
                                                support.travel_id.route_id.id,
                                                ps_id,
                                                distance=distance,
                                                context=context)
            #TODO VERIFICA SALDO
            # SOLO TOMO EL PS MAS CERCANO (EL PRIMERO)
            if len(sp_ids) > 0:
                psinrange_obj.create(cr, uid,
                                     {'route_id': support.travel_id.route_id.id,
                                      'service_partner_id': sp_ids[0],
                                      'state': 'wait'})
                res.update({str(support.travel_id.route_id.id): sp_ids[0]})
            else:
                return False
            self.write(cr, uid, ids, {'state': 'searching'}, context)

        return res

    def find_partners_inrange(self, cr, uid, id, route_id, ps_id, distance=2500, context=None):
        res = []
        sql = " SELECT sp.id FROM gt_service_partner sp LEFT JOIN res_partner p ON p.id=sp.partner_id" \
              " LEFT JOIN gt_travel_support t ON ST_DWithin(p.geo_point, t.geo_point, {0})" \
              " WHERE t.id={1} AND sp.id<>{2} AND sp.partner_active = TRUE" \
              " AND sp.id not in (select service_partner_id from gt_route_rejection where route_id= {3}) " \
              " AND sp.id not in (select service_partner_id from gt_route_psinrange where route_id= {3} and state='timeout') " \
              " ORDER BY ST_Distance(p.geo_point, t.geo_point)".format(distance, id, ps_id, route_id)
        cr.execute(sql)
        list = cr.fetchall()
        for l in list:
            res.append(l[0])
        return res
