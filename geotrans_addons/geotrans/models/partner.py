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
from vehicle import *
from validate_email import validate_email
from geotrans import *
import re

_BLOODTYPE = [('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'),
              ('O-', 'O-')]

_PARTNERSTATES = [('active', 'Activo'), ('inactive', 'Inactivo'), ('block', 'Bloqueado')]

_WORKZONE = [('north', 'Norte'), ('south', 'Sur'), ('center', 'Centro'), ('peripheras', 'Periféricos')]

_WORKTIME = [('parttime', 'Tiempo Parcial'), ('fulltime', 'Tiempo Completo')]

class BasePartner(osv.osv):
    _inherit = 'res.partner'

    _columns = dict(
        voucher_ids=fields.one2many('account.voucher','partner_id', string="Pagos del Cliente"),
    )


class ServicePartner(osv.osv):
    _name = 'gt.service.partner'
    _description = 'Proveedor de Servicio'
    # _inherits: con esto generamos una nueva tabla con el objeto service partner y se relaciona mediante la columna partner_id
    _inherits = {'res.partner': 'partner_id'}

    def _check_quan_vehicles(self, cr, uid, ids, context={}):
        for obj in self.browse(cr, uid, ids, context=context):
            if len(obj.vehicle_ids) > 1:
                return False
        return True

    def _pico_placa(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        weekday = -1
        for obj in self.browse(cr, uid, ids, context=context):
            if len(obj.vehicle_ids) > 0:
                # obtener vehiculo
                plate_vehicle = obj.vehicle_ids[0].licenseplate_vehicle
                digit_verificaton = str(plate_vehicle[4:-1])
                if digit_verificaton.isdigit():
                    if digit_verificaton == '1' or digit_verificaton == '2':
                        weekday = 0  # lunes
                    elif digit_verificaton == '3' or digit_verificaton == '4':
                        weekday = 1  # martes
                    elif digit_verificaton == '5' or digit_verificaton == '6':
                        weekday = 2  # miercoles
                    elif digit_verificaton == '7' or digit_verificaton == '8':
                        weekday = 3  # jueves
                    elif digit_verificaton == '9' or digit_verificaton == '0':
                        weekday = 4  # viernes
            else:
                # no obtuvo ninguna placa o no hay vehiculo
                result[obj.id] = False
            if weekday != -1:
                now = datetime.today().weekday()
                time = fields.datetime.context_timestamp(cr, uid, datetime.today(), context=context)
                timenow = time.time()
                today7am = timenow.replace(hour=7, minute=0, second=0, microsecond=0)
                today9am = timenow.replace(hour=9, minute=30, second=0, microsecond=0)
                today16pm = timenow.replace(hour=16, minute=0, second=0, microsecond=0)
                today19pm = timenow.replace(hour=19, minute=30, second=0, microsecond=0)
                if weekday == now:
                    if today7am < timenow < today9am or today16pm < timenow < today19pm:
                        result[obj.id] = True
                    else:
                        result[obj.id] = False
                else:
                    result[obj.id] = False
        return result

    def _message_pico_placa(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.pico_placa:
                result[obj.id] = "Esta en pico y placa"
            else:
                result[obj.id] = "No esta en pico y placa"
        return result

    def _get_user(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            res[obj.id] = obj.ced_ruc[0:10]
            return res

    def _compute_age(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        now = datetime.now()
        for r in self.browse(cr, uid, ids, context=context):
            try:
                dob = datetime.strptime(r.date_birth,'%Y-%m-%d')
                delta = relativedelta(now, dob)
            finally:
                result[r.id] = str(delta.years) + "Año(s) " + str(delta.months) + "Mes(es) " + str(delta.days) + "Día(as)" #if you only want date just give delta.years
        return result
    #CALCULA EL SALDO DEL PS

    def _compute_balance(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        voucher_obj= self.pool.get('account.voucher')
        for r in self.browse(cr, uid, ids, context=context):
                balance = 0.0
                #TODO: TOMAR ENCUENTA LOS DEBITOS AL SALDO
                v_ids = voucher_obj.search(cr, uid, [('partner_id', '=', r.partner_id.id)])

                for voucher in voucher_obj.browse(cr, uid, v_ids):
                    balance += voucher.amount

                result[r.id] = balance
        return result

    def _check_ruc_isdigit(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.ced_ruc:
                list_ced_ruc = list(obj.ced_ruc)
                if len(list_ced_ruc) == 13:
                    if obj.ced_ruc.isdigit():
                        return True
        return False

    def _check_mobile(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.mobile:
                list_mobile = list(obj.mobile)
                if len(list_mobile) == 10:
                    if obj.mobile.isdigit():
                        if list_mobile[0:2] == ['0', '9'] or list_mobile[0:2] == ['0', '8']:
                            return True
        return False

    def _validate_email(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.email:
                is_valid = validate_email(obj.email)
                if is_valid:
                    return True
        return False

    def _check_phone(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.phone:
                list_phone = list(obj.phone)
                if len(list_phone) == 9:
                    if obj.phone.isdigit():
                        if list_phone[0:2] == ['0', '2'] or list_phone[0:2] == ['0', '3'] or list_phone[0:2] == ['0', '4'] or \
                           list_phone[0:2] == ['0', '5'] or list_phone[0:2] == ['0', '6'] or list_phone[0:2] == ['0', '7']:
                            return True
        return False

    def _check_pwd(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.pwd_partner:
                list_pwd = list(obj.pwd_partner)
                part_pwd = obj.pwd_partner[0:4]
                if len(list_pwd) <= 8:
                    if part_pwd.isalnum():
                        return True
        return False

    def _get_terms_conditions(self, cr, uid, ids, context={}):
        term_object = self.pool.get('gt.termsconditions.ps')
        term_object_id = term_object.search(cr, uid, [('state', '=', 'active')])
        if term_object_id:
            if len(term_object_id) >0:
                return term_object_id[0]
        return False

    def _compute_ranking(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        unique_route = []
        sum_rank_routes = 0
        count = 0
        travel_obj = self.pool.get('gt.travel')
        route_obj = self.pool.get('gt.route')
        for ps in self.browse(cr, uid, ids, context=None):
            travel_ids = travel_obj.search(cr, uid, [('sp_partner_id', '=', ps.id)])
            travels = travel_obj.browse(cr, uid, travel_ids)
            for travel in travels:
                if travel.route_id.id not in unique_route:
                    unique_route.append(travel.route_id.id)
        routes = route_obj.browse(cr, uid, unique_route)
        if routes:
            for route in routes[-2000:]:
                if 0 < int(route.ps_qualification) and route.travel_ids[0].sp_partner_id.id == ps.id:
                    count += 1
                    sum_rank_routes += float(route.ps_qualification)
            if count > 0:
                average = round(sum_rank_routes/count, 1)
            else:
                average = 0
            result[ps.id] = average
        else:
            result[ps.id] = 0
        return result

    _columns = dict(
        id=fields.integer('res.partner'),
        last_name=fields.char('Apellido', size=32, required=True, help=u'Ingrese el apellido del Ps'),
        ced_ruc=fields.char('Ruc', size=13, required=True, help=u'Número de RUC del Ps'),
        street=fields.char('Dirección', required=True, help=u'Ingrese la dirección del domicilio del Ps'),
        mobile=fields.char('Celular', size=10, required=True, help=u'Número de Celular'),
        phone=fields.char('Teléfono convencional', size=9, required=True, help=u'Número convencional'),
        subscription_date=fields.date('Fecha Inscripción al Servicio', required=True,
                                      help=u'Fecha de Inscripción del proveedor de Servicio'),
        date_birth=fields.date('Fecha Nacimiento', required=True,
                               help=u'Fecha de nacimiento del proveedor de Servicio'),
        license_expiration_date=fields.date('Fecha Caducidad Licencia', required=True,
                                            help=u'Fecha de caducidad de la Licencia'),
        license_points=fields.integer('Puntos Disponibles', required=True, help=u'Puntos disponibles según ANT'),
        blood_type=fields.selection(_BLOODTYPE, 'Tipo de Sangre', help=u'Tipo de sangre según la Licencia'),
        email=fields.char('Email', size=240, required="True", help=u'Ingrese el email del Ps'),
        age=fields.function(_compute_age, method=True, type='char', size=32, string='Edad', help=u'Edad del Ps'),
        vehicle_ids=fields.many2many('gt.vehicle', string='Seleccione Vehículo', help=u'Seleccione su(s) vehículos'),
        user_partner=fields.char('Usuario', size=64),
        pwd_partner=fields.char('Password', size=64, required=True,
                                help=u'Ingrese la contraseña del usuario, '
                                     u'recuerde que solo se permiten caracteres alfanuméricos'),
        partner_active=fields.boolean('Activo', help=u'Indica si el Ps se encuentra activado o desactivado'),
        service_type_ids=fields.many2many('gt.service.type', string="Tipos de Servicio",
                                          help=u"Seleccione el tipo de servicio"),
        token_id=fields.char('Id Dispositivo', readonly=True, size=256, help=u'Id del dispositivo'),
        terms_conditions=fields.char(string='Versión actual', readonly=True),
        txt_terms_conditions=fields.text('Términos y Condiciones Ps', size=8000),
        confirm_terms_conditions=fields.boolean('Acepto', readonly=True,
                                                help=u'Indica si el ps ha aceptado los términos y Condiciones'),
        get_user=fields.function(_get_user, method=True, type='char', size=32, string='Get User Ruc',
                                 help=u'El usuario es el número de cédula'),
        penalty_ids=fields.one2many('gt.penalty.application', 'penalty_partner_id', string="Multas Aplicadas",
                                    help=u"Seleccione las multas"),
        state=fields.selection(_PARTNERSTATES, string='Estado Proveedor', help=u"Indique el estado del proveedor"),
        work_zone=fields.selection(_WORKZONE, string='Zona de trabajo', help=u'Zona de trabajo del Ps'),
        rainwear=fields.boolean(string='Dispone equipo de lluvia', help=u'Elija si dispone equipo de lluvia el Ps'),
        work_time=fields.selection(_WORKTIME, string='Tipo de trabajo (completo/parcial)',
                                   help=u'Elija si va trabajar tiempo completo o parcial'),
        work_time_info=fields.boolean(string='Trabaja como motorizado?', help=u'Trabaja como motorizado?'),
        voucher_ids=fields.related('partner_id', 'voucher_ids', relation="account.voucher", type='one2many',
                               string="Abonos", store=False, readonly=True),
        balance=fields.function(_compute_balance, method=True, type='float', store=True, string='Saldo',
                                help=u'Saldo Actual del Ps'),
        ranking=fields.function(_compute_ranking, method=True, type='float', string='Ranking',
                             help=u'Calificación del Ps'),
        pico_placa=fields.function(_pico_placa, method=True, type='boolean', string='Pico y Placa'),
        message_pico_placa=fields.function(_message_pico_placa, method=True, type='char', size=32, string='Pico y Placa',
                                 help=u'Información pico y placa'),
    )

    _defaults = dict(
        work_time='fulltime',
        rainwear=False,
        partner_active=False,
        confirm_terms_conditions=False,
        subscription_date=fields.datetime.now,
        terms_conditions=_get_terms_conditions,
        type_ced_ruc='ruc',
        tipo_persona='6',
        state='active',
    )

    _constraints = [
        (_check_ruc_isdigit, ('Tipo de dato no válido, recuerde que debe tener 13 digitos y solo se permiten caracteres numericos'), ['Ruc']),
        (_check_mobile, ('Ingrese un número de celular válido, recuerde que debe tener 10 digitos e iniciar con 08 o 09'), ['Celular']),
        (_check_phone, ('Ingrese un número convencional válido, recuerde que debe tener 9 digitos e iniciar con el código de área Ej: 02333222'), ['Telefono Convencional']),
        (_validate_email, ('Ingrese una direccion de correo valido, Ej: email@is.valid'), ['Email']),
        (_check_pwd, ('Ingrese una contraseña correcta, solo se permiten caracteres alfanuméricos'), ['Password']),
        (_check_quan_vehicles, ('Solo puede ingresar un vehículo'), ['Vehiculo']),
        ]

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for ps in self.browse(cr, uid, ids, context=context):
            result[ps.id] = ps.name + " " + ps.last_name
        return result.items()

    def act_inactive(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'inactive'}, context)
        return True

    def act_block(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'block'}, context)
        return True

    def act_active(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'active'}, context)
        return True

    def get_geopoint_to_google(self, cr, uid, id):
        # EN POSTGRES SE ALMACENA 'POINT(-78.476947 -0.182862)' donde "POINT(Longitud Latitud)"
        sql = "select " \
              "ltrim(split_part(substr(ST_AsText(ST_Transform (geo_point,4326)),6),' ',1),'(') as lng, " \
              "rtrim(split_part(substr(ST_AsText(ST_Transform (geo_point,4326)),6),' ',2),')') as lat " \
              "from res_partner where id= {0}".format(id)
        cr.execute(sql)
        res = cr.fetchone()
        if res:
            return res[0], res[1]
        else:
            return False

    #TODO VALIDAR METODO PARA CREAR RECARGAS DE SALDO
    def ws_recharge(self, cr, uid, ci, ammount, date, agent, transaction):

        if not ci:
            return -1, u'IDENTIFICACION NO PUEDE ESTAR VACIA'
        if not ammount or ammount <= 0.0:
            return -1, u'EL MONTO NO PUEDE ESTAR VACIO O SER <= 0.0'
        if not transaction:
            return -1, u'EL NUMERO DE TRANSACCION NO PUEDE ESTAR VACIO'

        return 0, u'RECARGA EXITOSA!'
