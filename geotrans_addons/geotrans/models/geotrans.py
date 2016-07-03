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
from base_geoengine import geo_model
from partner import *

_SERVICETYPES = [('DOC01', 'Documentos'), ('PAQ02', 'Paquetes'), ('PEP03', 'Personas'), ('SER04', 'Servicios'),
                 ('CUSTOM', 'Perzonalizado')]

class GeoUtils(orm.AbstractModel):
    # CLASE CON METODOS UTILES DE GEOLOCALIZACION PARA RUTAS, VIAJES, RELEVOS
    _name = 'gt.geoutils'

    def parse_geopoint_from_google(self, cr, uid, value):
        # INGRESA: 'POINT(-78.476947 -0.182862)' donde "POINT(Longitud Latitud)"
        # RETORNA: 'POINT(-22012 -15418)' donde "POINT(Longitud Latitud) EN FORMATO 900913 DE POSTGIS "
        sql = "SELECT ST_AsText(ST_Transform (ST_GeomFromText ('{0}',4326),900913))".format(value)
        cr.execute(sql)
        res = cr.fetchone()
        return res[0]


    def update_geopoint_from_google(self, cr, uid, id, field, value):
        # EN POSTGRES SE ALMACENA 'POINT(-78.476947 -0.182862)' donde "POINT(Longitud Latitud)"
        # SE RECIBE EL TEXTO: POINT(-78.476947 -0.182862)
        sql = " UPDATE {0} " \
              " set {1}=ST_Transform (ST_GeomFromText ('{2}',4326),900913), write_uid = {3}" \
              " WHERE id={4}".format(self._name.replace('.', '_'), field, value, uid, id)
        cr.execute(sql)
        return True

    def get_geopoint_to_google(self, cr, uid, id, field):
        # EN POSTGRES SE ALMACENA 'POINT(-78.476947 -0.182862)' donde "POINT(Longitud Latitud)"
        sql = "select " \
              "ltrim(split_part(substr(ST_AsText(ST_Transform ({0},4326)),6),' ',1),'(') as lng, " \
              "rtrim(split_part(substr(ST_AsText(ST_Transform ({0},4326)),6),' ',2),')') as lat " \
              "from {1} where id= {2}".format(field, self._name.replace('.', '_'), id)
        cr.execute(sql)
        res = cr.fetchone()
        if res:
            return res[0], res[1]
        else:
            return False


class ServiceType(osv.osv):
    _name = 'gt.service.type'
    _description = 'Tipos de Servicio'

    _columns = dict(
        code=fields.selection(_SERVICETYPES, string='Codigo de Servicio', required=True, size=16,
                              help=u'Codigo del servicio'),
        name=fields.char('Nombre para Mostrar', size=64, required=True, help=u'Ingrese el nombre del servicio'),
        active=fields.boolean('Activo', help=u'Indica si el servicio se encuentra activo')
    )

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for st in self.browse(cr, uid, ids, context=context):
            names=[item for item in _SERVICETYPES if item[0] == st.name]
            if len(names) > 0:
                result[st.id] = names[0][1]
            else:
                result[st.id] = st.name
        return result.items()

    def get_active_services(self, cr, uid, context=None):
        servicetypes = {}
        service_object_ids = self.search(cr, uid, [('active', '=', 'True')])
        services = self.browse(cr, uid, service_object_ids)
        for service_type in services:
            servicetypes.update(
                {
                            service_type.code: service_type.name,
                }
            )
        return servicetypes
