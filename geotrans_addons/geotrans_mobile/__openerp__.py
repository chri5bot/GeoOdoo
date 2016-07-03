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
{'name': 'GeoTrans Mobile',
 'version': '1.0',
 'author': 'Christian Torres',
 'category': 'Transporte',
 'description': """Módulo backend para interacción con aplicacion mobil Android. Transporte de paquetes, documentos, servicios y personas""",
 'website': 'http://tandicorp.com',
 'license': 'AGPL-3',
 'depends': ["geotrans","tandi_gcmpush"],
 'init_xml': [],
 'data': ["wizard/views/send_message.xml",
          "data/geotrans_jobs.xml",
          ],
 'update_xml': [],
 'installable': True,
 'active': False,
 }
