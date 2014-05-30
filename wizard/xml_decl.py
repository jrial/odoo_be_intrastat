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
import time
import base64
import xml.etree.ElementTree as ET
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.report import report_sxw


class xml_decl(osv.osv_memory):
    """
    Intrastat XML Declaration
    """
    _name = "l10n_be_intrastat_declaration_xml.xml_decl"
    _description = 'Intrastat XML Declaration'

    def _get_tax_code(self, cr, uid, context=None):
        obj_tax_code = self.pool.get('account.tax.code')
        obj_user = self.pool.get('res.users')
        company_id = obj_user.browse(cr, uid, uid, context=context).company_id.id
        tax_code_ids = obj_tax_code.search(cr, uid, [('company_id', '=', company_id), ('parent_id', '=', False)], context=context)
        return tax_code_ids and tax_code_ids[0] or False

    def _get_xml_data(self, cr, uid, context=None):
        if context.get('file_save', False):
            return base64.encodestring(context['file_save'].encode('utf8'))
        return ''

    _columns = {
        'name': fields.char('File Name', size=32),
        'month': fields.char('Month',size = 2,required = True),
        'year': fields.char('Year',size = 4,required = True),
        'tax_code_id': fields.many2one('account.tax.code', 'Company', domain=[('parent_id', '=', False)],
                                           help="Keep empty to use the user's company", required=True),
        'arrivals': fields.selection([(0, 'Exempt'),
                                      (1, 'Standard'),
                                      (2, 'Extended')], 'Arrivals', required=True),
        'dispatches': fields.selection([(0, 'Exempt'),
                                      (1, 'Standard'),
                                      (2, 'Extended')], 'Dispatches', required=True),
        'decl_xml': fields.boolean('Intrastat XML file', help="Sets the XML output"),
        'msg': fields.text('File created', size=14, readonly=True),
        'file_save' : fields.binary('Save File', readonly=True),
        'comments': fields.text('Comments'),
        }

    _defaults = {
        'arrivals': 1,
        'dispatches': 1,
        'file_save': _get_xml_data,
        'name': 'intrastat.xml',
        'tax_code_id': _get_tax_code,
    }

    def create_xml(self, cr, uid, ids, context=None):
        """Creates xml that is to be exported and sent to estate for partner vat intra.
        :return: Value for next action.
        :rtype: dict
        """
        obj_mod = self.pool.get('ir.model.data')
        obj_user = self.pool.get('res.users')

        decl_datas = self.browse(cr, uid, ids[0])
        if decl_datas.tax_code_id:
            obj_company = decl_datas.tax_code_id.company_id
        else:
            obj_company = obj_user.browse(cr, uid, uid, context=context).company_id
        vat_no = obj_company.partner_id.vat
        if not vat_no:
            raise osv.except_osv(_('Insufficient Data!'), _('No VAT number associated with your company.'))
        vat_no = vat_no.replace(' ','').upper()
        vat = vat_no[2:]
        if len(decl_datas.month) != 2:
            decl_datas.month = "0%s" % decl_datas.month
        if int(decl_datas.month)<1 or int(decl_datas.month)>12:
            raise osv.except_osv(_('Incorrect Data!'), _('Month is a number between 1 and 12.'))
        if len(decl_datas.year) != 4:
            raise osv.except_osv(_('Incorrect Data!'), _('Year is a number of 4 digits.'))

        #Create root declaration
        decl = ET.Element('DeclarationReport')
        decl.set('xmlns', 'http://www.onegate.eu/2010-01-01')

        #Add Administration elements
        admin = ET.SubElement(decl, 'Administration')
        fromtag = ET.SubElement(admin, 'From')
        fromtag.text = vat
        fromtag.set('declarerType', 'KBO')
        ET.SubElement(admin, 'To').text = "NBB"
        ET.SubElement(admin, 'Domain').text = "SXX"
        if decl_datas.arrivals == 1:
            decl.append(self._get_arrivals_simple(cr, uid, ids, decl_datas, context))
        elif decl_datas.arrivals == 2:
            decl.append(self._get_arrivals_extended(cr, uid, ids, decl_datas, context))
        if decl_datas.dispatches == 1:
            decl.append(self._get_dispatch_simple(cr, uid, ids, decl_datas, context))
        elif decl_datas.dispatches == 2:
            decl.append(self._get_dispatch_extended(cr, uid, ids, decl_datas, context))

        #Get xml string with declaration
        data_file = ET.tostring(decl, encoding='UTF-8', method='xml')
        context['file_save'] = data_file

        model_data_ids = obj_mod.search(cr, uid,[('model','=','ir.ui.view'),('name','=','view_intrastat_declaration_xml_save')], context=context)
        resource_id = obj_mod.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']

        return {
            'name': _('Save'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'l10n_be_intrastat_declaration_xml.xml_decl',
            'views': [(resource_id,'form')],
            'view_id': 'view_intrastat_declaration_xml_save',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def _get_arrivals_simple(self, cr, uid, ids, decl_datas, context=None):
        decl = ET.Element('Report')
        decl.set('code','EX19S')
        datas = ET.SubElement(decl, 'Data')
        datas.set('form', 'EXF19S')
        datas.set('close', 'true')
        numlgn = 0

        if numlgn == 0:
            #no datas
            datas.set('action', 'nihil')
        return decl

    def _get_arrivals_extended(self, cr, uid, ids, decl_datas, context=None):
        decl = ET.Element('Report')
        decl.set('code','EX19E')
        datas = ET.SubElement(decl, 'Data')
        datas.set('form', 'EXF19E')
        datas.set('close', 'true')
        numlgn = 0

        if numlgn == 0:
            #no datas
            datas.set('action', 'nihil')
        return decl

    def _get_dispatch_simple(self, cr, uid, ids, decl_datas, context=None):
        decl = ET.Element('Report')
        decl.set('code','EX29S')
        datas = ET.SubElement(decl, 'Data')
        datas.set('form', 'EXF29S')
        datas.set('close', 'true')
        numlgn = 0

        if numlgn == 0:
            #no datas
            datas.set('action', 'nihil')
        return decl

    def _get_dispatch_extended(self, cr, uid, ids, decl_datas, context=None):
        decl = ET.Element('Report')
        decl.set('code','EX29E')
        datas = ET.SubElement(decl, 'Data')
        datas.set('form', 'EXF29E')
        datas.set('close', 'true')
        numlgn = 0

        if numlgn == 0:
            #no datas
            datas.set('action', 'nihil')
        return decl
