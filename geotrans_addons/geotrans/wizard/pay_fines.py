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
import time
from lxml import etree
from openerp.osv import fields, osv
from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.float_utils import float_compare
import openerp.addons.decimal_precision as dp
import xlrd
import base64
import logging
import tempfile
from openerp.tools.translate import _
from openerp import tools
from openerp.tools.sql import drop_view_if_exists

_logger = logging.getLogger(__name__)


class wizard_penalty_invoice(osv.osv_memory):
    _name = 'wizard.penalty.invoice'
    _description = 'Facturar multas'

    _columns = dict(
        wizard_date=fields.date(string='Fecha de facturación'),
        penalty_line_ids=fields.many2many('gt.penalty.application', string='Lista de multas'),
    )

    _defaults = dict(
        wizard_date=fields.datetime.now,
    )

class wizard_penalty_line(osv.osv):
    _name = "wizard.penalty.line"
    _description = "Vista de multas en el wizard"
    _auto = False
    _columns = dict(
        name=fields.char('Nombre', size=128, readonly=True),
        total=fields.float('Total de multas', readonly=True),
        num=fields.integer('Cantidad de las multas', readonly=True),
        )

    def init(self, cr):
        drop_view_if_exists(cr, 'wizard_penalty_line')
        cr.execute("""
            CREATE OR REPLACE VIEW wizard_penalty_line AS (
            SELECT DISTINCT CONCAT(rp.name,' ',gsp.last_name) as name,
                gsp.id as id,
                sum(pt.list_price) as total,
                count(gpa.id) as num
            FROM gt_penalty_application as gpa
                INNER JOIN gt_penalty as gp ON gpa.penalty_id=gp.id
                INNER JOIN product_product as pp ON gp.product_id=pp.id
			    INNER JOIN product_template as pt on pp.product_tmpl_id=pt.id
			    INNER JOIN gt_service_partner as gsp
                INNER JOIN res_partner as rp on gsp.partner_id=rp.id
                on gpa.penalty_partner_id=gsp.id
            WHERE gpa.state='confirmed'
            GROUP BY gsp.id, gpa.penalty_partner_id, gpa.state, gsp.last_name, rp.name
            )""")
