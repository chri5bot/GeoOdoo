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
from openerp import tools
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta


class Brand(osv.osv):
    _name = 'gt.brandvehicle'
    _description = 'Marca del vehiculo'

    _columns = dict(
        id_modelvehicles=fields.one2many('gt.modelvehicle', 'brandvehicle_id', string='Modelo de la marca'),
        name=fields.char('Marca del Vehículo', size=64, required=True, help=u'Marca del Vehículo'),
    )


class ModelVehicle(osv.osv):
    _name = 'gt.modelvehicle'
    _description = 'Descripcion del Vehiculo'

    _columns = dict (
        brandvehicle_id=fields.many2one('gt.brandvehicle'),
        name=fields.char('Modelo según la marca', required=True, help=u'Ingrese modelo según la marca')
    )

    def name_get(self, cr, uid, ids, context=None):
        result = {}
        for model in self.browse(cr, uid, ids, context=context):
            if model.brandvehicle_id and model.brandvehicle_id.name:
                result[model.id] = "["+model.brandvehicle_id.name+"] " + model.name
            else:
                result[model.id] = model.name
        return result.items()


class Vehicle(osv.osv):
    _name = 'gt.vehicle'
    _description = 'Vehiculo'

    def _check_unique_insesitive(self, cr, uid, ids, context=None):
        sr_ids = self.search(cr, uid, [], context=context)
        lst = [x.licenseplate_vehicle.lower()
               for x in self.browse(cr, uid, sr_ids, context=context) if x.licenseplate_vehicle and x.id not in ids]
        lst2 = [x.licenseplate_vehicle.upper()
                for x in self.browse(cr, uid, sr_ids, context=context) if x.licenseplate_vehicle and x.id not in ids]
        for self_obj in self.browse(cr, uid, ids, context=context):
            if (self_obj.licenseplate_vehicle and self_obj.licenseplate_vehicle.lower() in lst) \
                    or (self_obj.licenseplate_vehicle and self_obj.licenseplate_vehicle.upper() in lst2):
                return False
            return True

    def _check_licenseplate(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.licenseplate_vehicle:
                licenseplate_vehicle = list(obj.licenseplate_vehicle)
                if len(licenseplate_vehicle) == 6:
                    if obj.licenseplate_vehicle.isalnum():
                        return True
        return False

    def _check_year(self, cr, uid, ids, context=None):
        actual_year = datetime.today().year
        for obj in self.browse(cr, uid, ids, context=None):
            if obj.modelyear_vehicle.isdigit():
                vehicle_year = int(obj.modelyear_vehicle)
                while 1950 < vehicle_year <= actual_year:
                    return True
        return False

    def _get_image_vehicle(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.photo_vehicle,
                                                            medium_name='photo_vehicle_medium',
                                                            avoid_resize_small=True,
                                                            return_small=False)
        return result

    def _set_image_vehicle(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'photo_vehicle': tools.image_resize_image_big(value)}, context=context)

    def _get_image_plate(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.photo_licenseplate_vehicle
                                                            ,medium_name='photo_licenseplate_medium',
                                                            avoid_resize_small=True,
                                                            return_small=False)
        return result

    def _set_image_plate(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'photo_licenseplate_vehicle': tools.image_resize_image_big(value)},
                          context=context)

    _columns = dict(
        id_brandvehicles=fields.many2one('gt.modelvehicle', string='Modelo del Vehículo'),
        cylindercapacity_vehicle=fields.integer('Cilindraje del Vehículo(cm³)', required=True,
                                                help=u'Cilindraje del Vehículo'),
        modelyear_vehicle=fields.char('Año del Vehículo (yyyy)', required=True, size=4,
                                      help=u'Año del modelo vehículo'),
        licenseplate_vehicle=fields.char('Placa del Vehículo', size=6, required=True, help=u'Placa del Vehículo'),
        photo_vehicle=fields.binary('Foto del Vehículo', required=True, help=u'Foto del Vehículo'),
        photo_licenseplate_vehicle=fields.binary('Foto de la Placa', required=True, help=u'Foto de la Placa'),
        photo_vehicle_medium=fields.function(_get_image_vehicle, fnct_inv=_set_image_vehicle,
                                                 string="Medium-sized image", type="binary", multi="_get_image",
                                                 store={
                                                     'gt.vehicle': (
                                                     lambda self, cr, uid, ids, c={}: ids, ['photo_vehicle'], 10),
                                                 },
                                                 help="Imagen hasta 128x128px"),
        photo_licenseplate_medium=fields.function(_get_image_plate, fnct_inv=_set_image_plate,
                                             string="Medium-sized image", type="binary", multi="_get_image",
                                             store={
                                                 'gt.vehicle': (
                                                     lambda self, cr, uid, ids, c={}: ids,
                                                     ['photo_licenseplate_vehicle'], 10),
                                             },
                                             help="Imagen hasta 128x128px"),


    )

    _constraints = [(_check_licenseplate,
                     ('Tipo de dato no válido, recuerde que debe tener 6 caracteres, y solo alfanuméricos.'),
                     ['Placa']),
                    (_check_year,
                    ('El año del vehículo debe estar entre(1950 y el año actual) y debe ser numérico. Ej: 2004'),
                    ['Year']),
                    (_check_unique_insesitive,
                     ('Ya existe, asegurese de ingresar una nueva placa.'),
                     ['Placa']),
                    ]
