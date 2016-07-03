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
from dateutil import parser, rrule
import pytz
from pytz import UTC
import math
from dateutil.relativedelta import relativedelta
from validate_email import validate_email
import re

_STATES = [('draft', 'Borrador'),
           ('inactive', 'Inactivo'),
           ('active', 'Activo')]


class ServiceConfiguration(osv.osv):
    _name = 'gt.service.configuration'
    _description = 'Configuracion de Servicio'

    # def _compute_date(self, cr, uid, ids, context={}):
    #     for r in self.browse(cr, uid, ids, context=context):
    #         if r.validity_start < r.validity_end:
    #             return True
    #     return False

    # def _get_rangeofdates(self, cr, uid, ids, context={}):
    #     all_ids = self.search(cr, uid, [('state', '=', 'active')],  context={})
    #     for id in ids:
    #         if id in all_ids:
    #             all_ids.remove(id)
    #     for stored in self.browse(cr, uid, all_ids, context=context):
    #         stored_date_start = parser.parse(stored.validity_start)
    #         stored_date_end = parser.parse(stored.validity_end)
    #         for current in self.browse(cr, uid, ids, context=context):
    #             date_start = parser.parse(current.validity_start)
    #             date_end = parser.parse(current.validity_end)
    #             if current.service_type.id == stored.service_type.id:
    #                 if stored_date_start <= date_start < stored_date_end or stored_date_start < date_end <= stored_date_end:
    #                      return False
    #     return True

    _columns = dict(
        service_type=fields.many2one('gt.service.type',required=True,string='Tipo de Servicio'),
        apply_wait=fields.boolean(string='Costo por espera?'),
        km_base=fields.integer(string='Kilómetros incluidos', required=True),
        wait_base=fields.integer(string='Paradas incluidas', required=True),
        wait_rate=fields.many2one('gt.rate',required=True, string='Tarifa Espera'),
        base_rate=fields.many2one('gt.rate', required=True, string='Tarifa mínima'),
        diurnal_rate=fields.many2one('gt.rate',required=True, string='Tarifa Diurna'),
        nocturnal_rate=fields.many2one('gt.rate',required=True, string='Tarifa Nocturna'),
        validity_start=fields.date('Inicio Vigencia Tarifa', required=True, help=u'Inicio de la vigencia de la tarifa'),
        validity_end=fields.date('Fin Vigencia Tarifa', required=True, help=u'Fin de la vigencia de la tarifa'),
        sd_ids=fields.one2many('gt.surcharge.discount', 'sd_id', string='Recargo/Descuento',
                               help=u'Seleccione el Recargo/Descuento que aplica'),
        time_begin_diurnal=fields.float('Hora Inicio Diurno', help=u'Hora inicio del Recargo/Descuento'),
        time_end_diurnal=fields.float('Hora Fin Diurno', help=u'Hora inicio del Recargo/Descuento'),
        time_begin_nocturnal=fields.float('Hora Inicio Nocturno', help=u'Hora inicio del Recargo/Descuento'),
        time_end_nocturnal=fields.float('Hora Fin Nocturno', help=u'Hora inicio del Recargo/Descuento'),
        state=fields.selection(_STATES, string='Estado de la configuración', help=u'Estado de la configuración'),

    )

    _defaults = dict(
        state='draft',
    )

    _constraints = [#(_compute_date,
                    #('El fin de vigencia de la tarifa no puede ser menor a la fecha de inicio de la misma'),
                    #['Fecha']),
                    #(_get_rangeofdates,
                    #('Existe otra configuracion, cruze de fechas'),
                    #['Fecha']),
                    ]

    def calculate_quotation(self, cr, uid, waits, route_km, request_date, service_type_id, context=None):
        id = self.search(cr, uid, [('state', '=', 'active'), ('service_type', '=', service_type_id),
                                   ('validity_start', '<=', request_date), ('validity_end', '>', request_date)],
                                    context=context)

        #CONFIGURACION DE ZONA HORARIA OPENERP ALMACENA EN UTC
        local_tz = pytz.timezone('America/Guayaquil')
        if context and "tz" in context.keys():
            local_tz = pytz.timezone(context["tz"])

        fecha_ruta = datetime.strptime(request_date, '%Y-%m-%d %H:%M:%S')
        fecha_ruta = UTC.localize(fecha_ruta, is_dst=False)

        costo=0.0
        costo_ps=0.0
        costo_espera=0.0
        costo_espera_ps = 0.0
        rate=False
        rate_ps=False
        surcharges=[]

        hora_ruta=fecha_ruta.astimezone(local_tz).time();
        hora_ruta_float=hora_ruta.hour + hora_ruta.minute / 60.
        dia_ruta=fecha_ruta.weekday()
        confids = self.search(cr, uid, [('state', '=', 'active')])
        conf_list = self.browse(cr, uid, id, context)
        for conf_obj in conf_list:

            #PRIMERO SE OBTIENE LA TARIFA SEGÚN LA HORA
            if conf_obj.time_begin_diurnal <= hora_ruta_float <= conf_obj.time_end_diurnal:
                rate = conf_obj.diurnal_rate.value_rate
                rate_ps = conf_obj.diurnal_rate.value_rate_internal
            elif conf_obj.time_begin_nocturnal <= hora_ruta_float < 24 or 00 <= hora_ruta_float < conf_obj.time_end_nocturnal:
                rate = conf_obj.nocturnal_rate.value_rate
                rate_ps = conf_obj.nocturnal_rate.value_rate_internal

            #SEGUNDO SE VERIFICA SI APLICA ESPERAS
            if conf_obj.apply_wait and waits > conf_obj.wait_base:
                costo_espera = (waits - conf_obj.wait_base) * conf_obj.wait_rate.value_rate
                costo_espera_ps = (waits - conf_obj.wait_base) * conf_obj.wait_rate.value_rate_internal

            #APLICA EL VALOR BASE
            costo = conf_obj.base_rate.value_rate
            costo_ps = conf_obj.base_rate.value_rate_internal

            #APLICA LA TARIFA A LOS KM ADICIONALES INCLUIDOS EN LA TARIFA BASE
            if route_km > conf_obj.km_base:
                costo += rate * (route_km - conf_obj.km_base)
                costo_ps += rate_ps * (route_km - conf_obj.km_base)

            # SE VERIFICA SI APLICAN DESCUENTOS O RECARGOS POR FECHAS O DIAS DE LA SEMANA
            # LOS RECARGOS/DESCUENTOS
            for sd in conf_obj.sd_ids:

                if sd.type == 'date':
                    date_begin = datetime.strptime(sd.date_begin, '%Y-%m-%d')
                    date_begin = UTC.localize(date_begin, is_dst=False)

                    date_end = datetime.strptime(sd.date_end, '%Y-%m-%d')
                    date_end = UTC.localize(date_end, is_dst=False)
                    if date_begin < fecha_ruta < date_end:
                        surcharges.append(sd.value_sd / 100.)

                if sd.type == 'day' and sd.day == str(dia_ruta):
                    surcharges.append(sd.value_sd / 100.)

            applied_surcharges = []
            for surch in surcharges:
                costo += costo * surch
                costo_espera += costo_espera * surch
                costo_ps += costo_ps * surch
                costo_espera_ps += costo_espera_ps * surch
                applied_surcharges.append(surch*100)

            costo_total = costo + costo_espera
            costo_total_ps = costo_ps + costo_espera_ps

        res = {
            "surcharge": str(applied_surcharges),
            "rate": rate,
            "km_cost": costo,
            "wait_cost": costo_espera,
            "total_cost": costo_total,
            "rate_ps": rate_ps,
            "km_cost_ps": costo_ps,
            "wait_cost_ps": costo_espera_ps,
            "total_cost_ps": costo_total_ps
        }

        return res


    def act_activate(self, cr, uid, ids, context=None):
        date = fields.datetime.context_timestamp(cr, uid, datetime.now(), context=context)
        for obj in self.browse(cr, uid, ids, context=context):
            service_type_actual = obj.service_type.id
            service_lastids = self.search(cr, uid, [('state', '=', 'active'),
                                                    ('service_type', '=', service_type_actual)])
            self.write(cr, uid, service_lastids, {'state': 'inactive', 'validity_end': date}, context)
            self.write(cr, uid, ids, {'state': 'active', 'validity_start': date}, context)
        # date = datetime.now()
        # for obj in self.browse(cr, uid, ids, context=context):
        #     service_type_actual = obj.service_type.id
        #     if service_type_actual:
        #         cr.execute("update gt_service_configuration "
        #                    "set state='inactive' "
        #                    "where service_type = %s",
        #                    (service_type_actual,))
        #         self.write(cr, uid, ids, {'state': 'active', 'validity_start': date}, context)
        return True

    def act_inactivate(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'inactive'}, context)
        return True

    def act_draft(self, cr, uid, ids, context=None):
            self.write(cr, uid, ids, {'state': 'draft'}, context)
            return True

