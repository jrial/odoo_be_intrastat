# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-TODAY OpenERP S.A. <http://www.odoo.com>
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

{
    'name': 'Belgian Intrastat Declaration',
    'version': '1.0',
    'category': 'Reporting',
    'description': """
Generates Intrastat XML report for declaration
    """,
    'author': 'OpenERP SA',
    'depends': ['report_intrastat', 'base_action_rule', 'sale_stock'],
    'data': [
        'data/regions.xml',
        #'data/report.intrastat.code.xml',
        'data/transaction.codes.xml',
        'data/transport.modes.xml',
        'security/ir.model.access.csv',
        'views/cust_invoice.xml',
        'views/res_company.xml',
        'views/stock_warehouse.xml',
        'views/supp_invoice.xml',
        'wizard/l10n_be_intrastat_declaration_xml_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'images': [],
    'css': [],
}
