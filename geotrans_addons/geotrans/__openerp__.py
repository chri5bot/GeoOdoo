# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Copyright (c) 2016 Tandicorp - http://www.tandicorp.com/
#    All Rights Reserved.
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
{'name': 'GeoTrans',
 'version': '1.0',
 'author': 'Tandicorp',
 'category': 'Transporte',
 'description': """Módulo backend para interacción con aplicacion mobil Android. Transporte de paquetes, documentos, servicios y personas""",
 'website': 'http://www.tandicorp.com',
 'license': 'AGPL-3',
 'depends': ["base", "account", "base_geoengine"],
 'init_xml': [],
 'demo_xml': [],
 'data': [
     'views/account_view.xml',
     'views/binnacle_view.xml',
     'views/customer_view.xml',
     'views/geotrans_view.xml',
     'views/rate_view.xml',
     'views/mobilesetting_view.xml',
     'views/partner_view.xml',
     'views/penalty_view.xml',
     'views/route_view.xml',
     'views/vehicle_view.xml',
     'views/termsconditions_view.xml',
     'views/surcharge_discount_view.xml',
     'views/service_configuration_view.xml',
     'views/reason_rejection_view.xml',
     'views/predefined_message_view.xml',
     'views/chat_view.xml',
     'wizard/pay_fines_view.xml',
 ],
 'installable': True,
 'active': False,}
