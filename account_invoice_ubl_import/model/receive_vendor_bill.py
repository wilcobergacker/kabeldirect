# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import base64
import xmltodict
import logging
import datetime
from email.utils import getaddresses
from bs4 import BeautifulSoup
from odoo.exceptions import UserError
from odoo.tools import pycompat
import re
import tempfile
import pdfkit
import os

_logger = logging.getLogger(__name__)


class ReceiveVendorBill(models.Model):
    _name = 'receive.vendor.bill'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Received UBL bills'
    _order = 'id desc'

    seq_name = fields.Char('Sequence', default="/")
    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner',
                                 string='Vendor', track_visibility='onchange')
    # set default expense account base on compnay depend.
    default_account_expense = fields.Many2one(
        'account.account',
        string='Default expense account',
        help='Default counterpart account for purchases')
    # set value while record create from receive incoming mail
    original_partner_id = fields.Many2one(
        'res.partner', string='Original Sender')
    process_ubl_type = fields.Selection(
        [('no', 'Do Not Process the Vendor Bill'),
         ('process_pdf', 'Create Vendor Bill from PDF'),
         ('process_ubl', 'Send Vendor Bill to UBL Porvider or process XML')],
        string='Process Vendor Bill')
    email_address = fields.Char(string='Email Address', size=64)
    email_from = fields.Char(string='From', size=64)
    date_time = fields.Datetime(string='Date time',
                                default=fields.Datetime.now)
    data_pdf = fields.Binary(string='Data PDF')
    file_name_pdf = fields.Char(string='From',
                                compute="_get_pdf_filename", size=64)
    data_xml = fields.Binary(string='Data XML')
    file_name_xml = fields.Char(string='From',
                                compute="_get_xml_filename", size=64)
    vendor_bill_ref = fields.Char(string='Vendor Bill reference', size=64)
    state = fields.Selection(
        [
            ('received', 'Received'),
            ('fwd_to_ubl_provider', 'Forwarded to UBL provider'),
            ('rec_back_from_ubl_provider', 'Received back from UBL provider'),
            ('vendor_bill_pro', 'Vendor Bill Processed'),
            ('not_process', 'Not Process'),
            ('exception', 'Exception'),
            ('cancel', 'Canceled')
        ],
        default='received',
        string='State',
        copy=False,
        track_visibility='always',
    )
    exception_description = fields.Text(string='Exception description')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get())
    is_process_xml = fields.Boolean(string="Process XML")

    # res.partner.bank details
    vendor_acc_account = fields.Char(string='Account Number', size=64)
    bic_code = fields.Char(string='Bank Identifier Code', size=64)

    # xml data basic invoice details
    issuedate = fields.Date(string='Issue Date')
    duedate = fields.Date(string='Due Date', copy=False)
    documentcurrencycode = fields.Char(
        string='Document Currency Code',
        size=64,
    )
    invoice_type_code = fields.Char(string='Invoice Type Code', size=64)
    currency_id = fields.Many2one('res.currency', string='Currency')

    # xml AccountingSupplierParty details
    partyidentification = fields.Char(string='Party Identification', size=64)
    party_vat = fields.Char(string='Party Tin', size=64)
    scheme_agency_id = fields.Char(string='@scheme Agency ID', size=64)
    partyname_supplier = fields.Char(string='Party Name', size=64)
    # postal address supplier
    streetname_postal_supplier = fields.Char(string='Street', size=64)
    cityname_postal_supplier = fields.Char(string='City', size=64)
    postalzone_postal_supplier = fields.Char(string='Postal Zone', size=64)

    # country_postal_supplier = fields.Char(string='Country', size=64)
    country_supplier_postal_id = fields.Many2one(
        'res.country',
        string='Country',
    )
    country_identificationcode_postal_supplier = fields.Char(
        string='Identification Code',
        size=64,
    )
    # physical address supplier
    streetname_physical_supplier = fields.Char(string='Street', size=64)
    cityname_physical_supplier = fields.Char(string='City', size=64)
    postalzone_physical_supplier = fields.Char(string='Postal Zone', size=64)

    # Country_physical_supplier = fields.Char(string='Country', size=64)
    country_supplier_physical_id = fields.Many2one(
        'res.country',
        string='Country',
    )
    country_identificationcode_physical_supplier = fields.Char(
        string='Identification Code',
        size=64,
    )
    # PartyTaxScheme supplier
    tax_registration_name_supplier = fields.Char(string='Registration Name')
    tax_id_supplier = fields.Char(string='Party Tax Scheme ID', size=64)
    tax_code_supplier = fields.Char(
        string='Party Tax Scheme Taxcode Type',
        size=64,
    )
    # PartyLegalEntity supplier
    legal_entity_registration_name_supplier = fields.Char(
        string='Registration Name',
        size=64,
    )
    company_id_supplier = fields.Char(string='Company ID')
    # contact supplier
    contact_supplier_phone = fields.Char(string='Phone', size=64)
    contact_supplier_email = fields.Char(string='Email', size=64)

    # Xml AccountingCustomerParty details
    supplier_assigned_account_id = fields.Char(
        string='Supplier Assigned Account ID',
    )
    partyname_customer = fields.Char(string='Party Name', size=64)
    # postal address customer
    streetname_postal_customer = fields.Char(string='Street', size=64)
    cityname_postal_customer = fields.Char(string='City', size=64)
    postalzone_postal_customer = fields.Char(string='Postal Zone', size=64)

    # Country_postal_customer = fields.Char(string='Country', size=64)
    country_customer_postal_id = fields.Many2one(
        'res.country',
        string='Country',
    )
    country_identificationcode_postal_customer = fields.Char(
        string='Identification Code',
        size=64,
    )
    # PartyLegalEntity customer
    legal_entity_registration_name_customer = fields.Char(
        string='Registration Name',
        size=64,
    )
    company_id_customer = fields.Char(string='Company ID')
    contact_customer = fields.Char(string='Contact', size=64)

    log_entries = fields.Text(string='Log', default="--show log---")
    # LegalMonetaryTotal
    line_extension_amount = fields.Float(string='Line Extension Amount')
    tax_exclusive_amount = fields.Float(string='Tax Exclusive Amount')
    tax_inclusive_amount = fields.Float(string='Tax Inclusive Amount')
    payable_amount = fields.Float(string='Payable Amount')
    total_tax_amount = fields.Float(string='Total Tax Amount')

    receive_vendor_bill_line_ids = fields.One2many(
        'receive.vendor.bill.line',
        'receive_vendor_bill_id',
        string='Invoice Line',
        copy=True,
    )
    account_invoice_id = fields.Many2one('account.invoice', string='Invoiced')
    journal_id = fields.Many2one('account.journal', string='Journal')

    @api.onchange('partner_id')
    def set_default_account_expense(self):
        ''' base on company set default expense account'''
        # base on company check from company ir.property
        if self.partner_id:
            self.partner_id.with_context(force_company=self.company_id.id)
            self.default_account_expense = self.partner_id.with_context(
                force_company=self.company_id.id).property_account_expense.id
            if not self.email_address:
                self.email_address = self.partner_id.email
            if not self.email_from:
                self.email_from = self.partner_id.name
            if not self.original_partner_id:
                self.original_partner_id = self.partner_id.id

    @api.one
    def _get_xml_filename(self):
        """ get xml file name """
        self.file_name_xml = self.seq_name + '.xml'

    @api.one
    def _get_pdf_filename(self):
        """ get pdf file name """
        self.file_name_pdf = self.seq_name + '.pdf'

    def set_attachment_to_vendor_bill(self, res_id):
        """ set attachment pdf and xml file if attachment exists
            while invoice create. """
        attch_pdf = {
            'res_id': res_id,
            'res_model': 'account.invoice',
            'datas': self.data_pdf,
            'datas_fname': self.file_name_pdf,
            'name': self.file_name_pdf
        }
        # create attachment while pdf
        attachment = self.env['ir.attachment'].create(attch_pdf)
        if self.data_xml:
            attch_xml = {
                'res_id': res_id,
                'res_model': 'account.invoice',
                'datas': self.data_xml,
                'datas_fname': self.file_name_xml,
                'name': self.file_name_xml
            }
            # cretae attachment while xml
            self.env['ir.attachment'].create(attch_xml)
        invoice = self.env['account.invoice'].browse(res_id)
        invoice.message_post(attachment_ids=attachment.ids)

    @api.model
    def create(self, vals):
        """ create a sequence while create R.V.B Record """
        vals['seq_name'] = self.env['ir.sequence'].next_by_code(
            'receive.vendor.bill')
        res = super(ReceiveVendorBill, self).create(vals)
        # when record create prevent to add message follower
        res.message_follower_ids.sudo().unlink()
        return res

    @api.model
    def _process_ubl_email(self, msg_dict, custom_values=None):
        """ while xml file receieve from ubl then that xml file append to
            respective res_id. compare filename and res_id sequence no """
        rec_name = False
        XML = False
        if not msg_dict.get('attachments', []):
            return False
        # check attachment for xml
        for attachment in msg_dict['attachments']:
            if len(attachment) == 2:
                name, content = attachment
            elif len(attachment) == 3:
                name, content, info = attachment
            else:
                continue
            if isinstance(content, pycompat.text_type):
                content = content.encode('utf-16')
            if name.lower().endswith('.xml'):
                XML = content
                rec_name = name
                continue
        if not rec_name or not XML:
            return False
        # check record while xml  file check search record base file name to sequence number
        # if search id get write xml file and state change to rec_back_from_ubl_provider
        search_ids = self.search([('seq_name', '=', rec_name[:-4])], limit=1)
        if search_ids:
            search_ids.write({'data_xml': base64.b64encode(bytes(XML)),
                              'state': 'rec_back_from_ubl_provider'})
            return search_ids
        return False

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification',
                     subtype=None, parent_id=False, attachments=None,
                     content_subtype='html', **kwargs):
        """ No follower is added while receive massage post in respective
            record """
        ctx = self._context.copy()
        ctx.update({'mail_create_nosubscribe': True})
        return super(ReceiveVendorBill, self.with_context(ctx)).message_post(
            body=body, subject=subject,
            message_type=message_type, subtype=subtype,
            parent_id=parent_id, attachments=attachments,
            content_subtype=content_subtype,
            **kwargs
        )

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ get new mail base on that create record or receive xml file
            for exsiting record """
        original_id = self._process_ubl_email(msg_dict, custom_values)
        if original_id:
            return original_id
        ctx = self._context.copy()
        ctx.update({'mail_create_nosubscribe': True})

        sender = msg_dict.get('from', '')

        for addr in getaddresses([sender]):
            sender = addr[0] if addr[0] else addr[1]
            sender_email = addr[1]

        # return if mail is blacklisted
        receive_vendor_bill_blacklist = self.env[
            'receive.vendor.bill.blacklist'].search(
                [('email', '=', sender_email)])
        if receive_vendor_bill_blacklist:
            _logger.warning(
                _("The email '%s' is ignored because the email address is on the blacklist."), sender_email)
            return False
        res = super(ReceiveVendorBill, self.with_context(
            ctx)).message_new(msg_dict, custom_values=custom_values)

        partner_id = msg_dict.get('author_id', '')
        # get value and attachment form receive mail base on that write in record
        if msg_dict.get('attachments', []):
            XML = False
            PDF = False
            rec_name = False
            # check attachment for xml and pdf file
            for attachment in msg_dict['attachments']:
                if len(attachment) == 2:
                    name, content = attachment
                elif len(attachment) == 3:
                    name, content, info = attachment
                else:
                    continue
                if isinstance(content, pycompat.text_type):
                    content = content.encode('utf-16')
                if name.lower().endswith('.xml'):
                    XML = content
                    rec_name = name
                    continue
                if name.lower().endswith('.pdf'):
                    PDF = content
                    rec_name = name
                    continue
            # if pdf write pdf file in record also set partner_id from author_id
            if PDF:
                res.write({'data_pdf':  base64.b64encode(bytes(PDF)),
                           'name': '%s - %s' % (res.name, rec_name),
                           'state': 'received'})
                res.write({
                    'email_from': sender, 'email_address': sender_email,
                    'original_partner_id': partner_id})
            # if xml write xml file in record and state change rec_back_from_ubl_provider.
            if XML:
                res.write({'data_xml': base64.b64encode(bytes(XML)),
                           'name': '%s - %s' % (res.name, rec_name),
                           'state': 'rec_back_from_ubl_provider'})

        else:
            # set vendor details when there is no attachment in received mail
            if 'body' in msg_dict:
                body = "<html><body>"+msg_dict['body']+"</body></html>"
                temp_html = tempfile.NamedTemporaryFile(delete=False)
                path = temp_html.name + '.html'
                os.unlink(temp_html.name)
                temp_html_file = open(path, 'w', encoding='utf-16')
                temp_html_file.write(body)
                temp_html_file.close()
                temp_pdf = tempfile.NamedTemporaryFile(delete=False)
                temp_pdf_file = temp_pdf.name + '.pdf'
                os.unlink(temp_pdf.name)
                pdfkit.from_file(temp_html_file.name, temp_pdf_file)
                os.unlink(temp_html_file.name)
                new_pdf = open(temp_pdf_file, 'rb').read()
                res.write({'data_pdf': base64.b64encode(bytes(new_pdf)),
                           'name': '%s - %s' % (res.name,
                                                "Mail Attachment"),
                           'state': 'received'})
                attachment_created = self.env['ir.attachment'].create({
                    'res_id': res.id,
                    'res_model': 'receive.vendor.bill',
                    'datas': res.data_pdf,
                    'datas_fname': res.file_name_pdf,
                    'name': res.file_name_pdf})
                # res.message_post(attachment_ids=attachment_created.ids)
                os.unlink(temp_pdf_file)
                res.write({
                    'email_from': sender, 'email_address': sender_email,
                    'original_partner_id': partner_id})
                msg_dict.update({'attachment_ids': attachment_created.ids})

            if partner_id:
                # if vendor not set then set vendor and also default expense account
                if not res.partner_id:
                    res.partner_id = partner_id
                res.set_default_account_expense()

        return res

    @api.multi
    def name_get(self):
        # set name_get based on sequence number and name field
        ret_val = []
        for rec in self:
            name = '[%s]' % rec.seq_name
            if rec.name:
                name += ' %s' % rec.name
            ret_val.append((rec.id, name))
        return ret_val

    @api.multi
    def set_lang(self):
        """ pass context for language NL """
        self.ensure_one()
        load_lang = self.env['res.lang'].search([('code', '=', 'nl_NL')])
        if load_lang:
            ctx = self._context.copy()
            ctx['lang'] = 'nl_NL'
            return ctx

    @api.one
    def record_log(self, msg, type='info', raise_error=False):
        """ Record log for warning or info """
        getattr(_logger, type)(msg)
        self.log_entries = 'Log: %s: %s\n%s' % (type.upper(), msg, self.log_entries)

    # set or create bank in res partner bank based on account no and bank set or create base on bic code
    @api.multi
    def set_vendor_bank(self, partner):
        """ set Bank for vendor base on vendor account number """
        for rec in self:
            bank_id = False
            if partner.bank_ids:
                return False
            if rec.vendor_acc_account:
                ac_id = self.env['res.partner.bank'].search([
                    ('acc_number', '=', rec.vendor_acc_account), '|',
                    ('company_id', '=', rec.company_id.id),
                    ('company_id', '=', False)])
                if ac_id:
                    # skip new creation of new bank account when account number already exists in record
                    self.record_log(
                        _("The bank account number '%s' already exists for another vendor. So we skipped creating the new bank account.") % (rec.vendor_acc_account), 'info')
                    return False
                # create partner bank based on vendor account no and partne_id
                ac_id = self.env['res.partner.bank'].create({
                    'acc_number': rec.vendor_acc_account,
                    'partner_id': partner.id})
                # if bic code than search if exist or create bank and add bank in partner bank
                if rec.bic_code:
                    bank_id = self.env['res.bank'].search([(
                        'bic', '=', rec.bic_code)])
                # if get bank_id set to partner bank or create bank and set to partner bank
                if bank_id:
                    ac_id.write({'bank_id': bank_id.id})
                elif rec.bic_code:
                    bank_id = self.env['res.bank'].create({
                        'name': rec.bic_code, 'bic': rec.bic_code})
                    ac_id.write({'bank_id': bank_id.id})

    @api.multi
    def create_vendor(self):
        res_obj = self.env['res.partner']
        ctx = self.set_lang()
        if ctx:
            self = self.with_context(ctx)
        for rec in self:
            res_id = False
            if not rec.data_xml or not rec.partyname_supplier:
                self.record_log(
                    _('Please Process the XML file First.'), 'warning')
                continue
            """ check several condition based on that search if exist or create vendor as per
                respective value given in xml file after process """
            # if partyidentification than search vendor based on company_registry
            if rec.partyidentification:
                res_id = res_obj.search(
                    [('company_registry', '=', rec.partyidentification)],
                    limit=1)
            # if not get search based on vat with party_vat
            if not res_id and rec.party_vat:
                res_id = res_obj.search([('vat', '=', rec.party_vat)], limit=1)
            # if not get search based on email with contact_supplier_email
            if not res_id and rec.contact_supplier_email:
                res_id = res_obj.search(
                    [('email', '=',  rec.contact_supplier_email)], limit=1)
            if res_id:
                rec.partner_id = res_id.id
                if rec.partner_id.company_id:
                    # if both partner and self obj comapny not same than partner comapny_id  false
                    if rec.partner_id.company_id != rec.company_id:
                        rec.partner_id.write({'company_id': False})
                self.record_log(_('Vendor is added successfully.'))
                # set vendor bank base account number and bic code
                rec.set_vendor_bank(rec.partner_id)
                # set default_account_expense base company ir.property
                rec.set_default_account_expense()
            else:
                # if vendor not found than create vendor base on below value
                # if PartyIdentification and party_vat is exist than create vendor
                if rec.partyidentification or rec.party_vat:
                    res_val = {
                        'name': rec.partyname_supplier,
                        'street': rec.streetname_postal_supplier or rec.streetname_physical_supplier or '',
                        'city': rec.cityname_postal_supplier or rec.cityname_physical_supplier or '',
                        'zip': rec.postalzone_postal_supplier or rec.postalzone_physical_supplier or '',
                        'country_id': rec.country_supplier_postal_id.id or rec.country_supplier_physical_id.id or '',
                        'phone': rec.contact_supplier_phone or '',
                        'email': rec.contact_supplier_email or '',
                        'supplier': True,
                        'customer': False,
                        'company_registry': rec.partyidentification or '',
                        'is_company': True,
                        'vat': rec.party_vat or '',
                        'company_id': rec.company_id.id,
                    }
                    rec.partner_id = rec.partner_id.create(res_val)
                else:
                    # we partner get while record create set partner_id set from it
                    if rec.original_partner_id:
                        if rec.process_ubl_type not in ['no', 'process_pdf']:
                            rec.partner_id = rec.original_partner_id.id
                if rec.partner_id:
                    # set vendor bank base on account no and bic code
                    rec.set_vendor_bank(rec.partner_id)
                    # set default_account_expense base on company ir.property
                    rec.set_default_account_expense()
                    self.record_log(_("Vendor created successfully."))
                else:
                    self.record_log(_('While processing XML file Party Identification or Party Tin or Original Sender is not set. So Vendor is not created.'), 'warning')
                    continue
        return True

    @api.multi
    def create_invoice(self, auto=False):
        """ create invoice based on vendor and process ubl type """
        self.ensure_one()
        # raise error when no vendor selected
        if not self.partner_id:
            if auto and (not self.data_xml) and (not self.data_pdf):
                return False
            if not auto:
                raise UserError(_('Please select the vendor for creating invoice.'))

        # confirmation for invoice creation when no attachment found
        if self.state == 'received' and (not self.data_pdf) and (not self.data_xml) and (not self._context.get('with_confirmation')) and not auto:
            confirm_action = self.env.ref(
                'account_invoice_ubl_import.action_view_invoice_confirmation')
            confirm_wiz = self.env['invoice.confirmation'].create({})
            return {
                'type': confirm_action.type,
                'name': _('Create Invoice?'),
                'res_model': 'invoice.confirmation',
                'view_mode': 'form',
                'target': 'new',
                'context': self._context,
                'res_id': confirm_wiz.id,
            }

        ctx = self.set_lang()
        # if process ubl type is not set it not process
        if self.process_ubl_type == 'no':
            self.state = 'not_process'
        if ctx:
            self = self.with_context(ctx)
        journal_domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', self.company_id.id),
        ]
        # get dafault jounal account  of pruchase base on company
        if self.journal_id:
            default_journal_id = self.journal_id
        else:
            default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
            if not default_journal_id:
                self.record_log(_("Please define an accounting purchase journal for '%s' company.") % (
                    self.company_id.name), 'warning')
                return False
        values = {}
        # if it process xml than create invoice base on xml process
        if self.is_process_xml:
            if not self.data_xml:
                self.record_log(_('First process the XML file'), 'warning')
            if self.account_invoice_id:
                self.record_log(_('Invoice is already created.'))
                return False
            if not self.partner_id:
                self.create_vendor()
            if not self.partner_id:
                self.record_log(
                    _("Please select the partner for creating invoice."))
                return False
            if not self.process_ubl_type == 'process_ubl':
                self.record_log(_("Invoice is created manually without configured Process Vendor Bill."), 'info')
            values = {
                'partner_id': self.partner_id.id,
                'type': 'in_refund' if self.payable_amount < 0 else 'in_invoice',
                'date_invoice': self.issuedate or datetime.datetime.today(),
                'date_due': self.duedate or False,
                'reference': self.vendor_bill_ref or '',
                'journal_id': default_journal_id.id,
                'company_id': self.company_id.id,
                'ubl_import_process_id': self.id,
                'invoice_line_ids': []
            }
            invoice_line = self.env['account.invoice.line']
            fpos = self.partner_id.property_account_position_id
            for rec in self.receive_vendor_bill_line_ids:
                # get tax id of tax percent 'Tax mapping' config from company
                tax_id = self.company_id.get_tax(rec.tax_percent_invoice_line)[0]
                # create invoice it contain invoice line
                account_id = self.default_account_expense
                if not account_id:
                    account_id = self.env['account.account'].browse(
                        invoice_line.with_context
                        ({
                            'partner_id': self.partner_id.id, 'type': 'in_invoice',
                            'journal_id': default_journal_id.id
                        })._default_account()
                    )
                if not tax_id and rec.tax_percent_invoice_line:
                    self.record_log(_("Please configure the Tax in 'Tax Configuration' page at company level"), 'warning')
                if fpos:
                    account_id = fpos.map_account(account_id)
                if tax_id:
                    # according to fiscal position of partner set tax_id
                    if fpos:
                        tax_id_val = fpos.map_tax(tax_id)
                        tax_id = tax_id_val

                if values.get('type') == 'in_refund':
                    inv_line_price_unit = (rec.price_amount * -1) if rec.price_amount and rec.price_amount < 0 else ''
                else:
                    inv_line_price_unit = rec.price_amount or ''

                if tax_id:
                    values['invoice_line_ids'].append((0, 0, {
                        'name': rec.name or '/',
                        'quantity': rec.invoiced_quantity,
                        'account_id': account_id.id,
                        'price_unit': inv_line_price_unit,
                        'invoice_line_tax_ids': [(6, 0, [tax_id.id])]
                    }))
                else:
                    values['invoice_line_ids'].append((0, 0, {
                        'name': rec.name or '/',
                        'quantity': rec.invoiced_quantity,
                        'account_id': account_id.id,
                        'price_unit': inv_line_price_unit,
                    }))
                    if rec.tax_percent_invoice_line > 0:
                        self.record_log(_('Invoice line is creating without Tax Id.'), 'warning')
                values.update()
            if not values['invoice_line_ids']:
                self.record_log(_('There is no invoice line. So no invoice is created.'))
                return False
        # if state in received and xml is not process than check for pdf process
        if self.state == 'received' and not self.is_process_xml:
            if not self.data_pdf:
                self.record_log(_('PDF data file is not uploaded.'), 'warning')
            # prepare values for invoice even when no attachment found
            values = {
                'partner_id': self.partner_id.id,
                'type': 'in_invoice',
                'date_invoice': datetime.datetime.today(),
                'date_due': self.duedate or False,
                'journal_id': default_journal_id.id,
                'company_id': self.company_id.id,
                'ubl_import_process_id': self.id,
            }

        if not values:
            return False
        # create invoice base on process ubl type
        self.account_invoice_id = self.env['account.invoice'].create(values)
        if self.account_invoice_id:
            # After invoice create check tax amount of tax line in invoice and update tax line amount
            for invoice_tax in self.account_invoice_id.tax_line_ids:
                amount = 0.00
                for xml_invoice in self.receive_vendor_bill_line_ids.search([('receive_vendor_bill_id', '=', self.id), ('tax_percent_invoice_line', '=', invoice_tax.tax_id.amount)]):
                    amount += xml_invoice.tax_amount_invoice_line
                if amount > 0.00:
                    if self.account_invoice_id.amount_tax != self.total_tax_amount:
                        invoice_tax.write({'amount': float(amount)})

        if self.data_pdf:
            # add attachment to invoice  if pdf file is their
            self.set_attachment_to_vendor_bill(self.account_invoice_id.id)
        # create invoice update log and add ref in record
        self.vendor_bill_ref = self.account_invoice_id.reference
        if self.account_invoice_id:
            self.state = 'vendor_bill_pro'
            self.record_log(_('Invoice create successfully.'))

        # set amount to positive value for record log when invoice is of refund type
        tax_inclusive_amount = self.tax_inclusive_amount
        tax_exclusive_amount = self.tax_exclusive_amount
        if self.account_invoice_id.type == 'in_refund':
            tax_inclusive_amount = (self.tax_inclusive_amount * -1) if self.tax_inclusive_amount < 0 else self.tax_inclusive_amount
            tax_exclusive_amount = (self.tax_exclusive_amount * -1) if self.tax_exclusive_amount < 0 else self.tax_exclusive_amount
        tax_value = tax_inclusive_amount - tax_exclusive_amount

        # check tax amount and untax amount and only tax amount if their is diffrence than update log
        tax_value = tax_inclusive_amount - tax_exclusive_amount
        if tax_exclusive_amount and tax_inclusive_amount:
            if round(self.account_invoice_id.amount_untaxed, 3) != round(tax_exclusive_amount, 3):
                self.record_log(_("A created invoice of amount without Tax '%s' is not match with the value of amount without Tax '%s' in XML file") % (self.account_invoice_id.amount_untaxed, tax_exclusive_amount), 'warning')
            if round(self.account_invoice_id.amount_tax, 3) != round(tax_value, 3):
                self.record_log(_("A created invoice of tax amount '%s' is not match with the value of tax amount '%s' in XML file") % (self.account_invoice_id.amount_tax, tax_value), 'warning')
            if round(self.account_invoice_id.amount_total, 3) != round(tax_inclusive_amount, 3):
                self.record_log(_("A created invoice of amount with tax '%s' is not match with the value of amount with tax '%s' in XML file") % (self.account_invoice_id.amount_total, tax_inclusive_amount), 'warning')
        imd = self.env['ir.model.data']
        # redirect to new create invoice
        list_view_id = imd.xmlid_to_res_id('account.invoice_supplier_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_supplier_form')
        result = {
            "type": "ir.actions.act_window",
            "res_model": "account.invoice",
            "views": [[list_view_id, "tree"], [form_view_id, "form"]],
            "domain": [["id", "=", self.account_invoice_id.id]],
            "context": {"create": False},
            "name": _("Invoices"),
        }
        return result

    @api.multi
    def resend_btn(self):
        # if mail not send to ubl than we can resend mail from form view
        # mail send only when xml file not their and pdf file their.
        ctx = self.set_lang()
        if ctx:
            self = self.with_context(ctx)
        for rec in self:
            # if data xml no need to send mail
            if rec.data_xml:
                self.record_log(_("XML file already exists. So you are not able to do further process for forward to ubl provider."), 'warning')
                continue
            if not rec.data_pdf:
                self.record_log(_("No PDF or UBL XML file received from vendor."), 'warning')
                continue
            # send to ubl also send pdf attachment
            rec.send_pdf_mail_to_ubl()

    @api.multi
    def cancel_btn(self):
        # state chnage to cnacel
        for rec in self:
            rec.state = 'cancel'

    @api.multi
    def reset_btn(self):
        # reset to receive state
        for rec in self:
            if rec.data_xml:
                rec.state = 'rec_back_from_ubl_provider'
                continue
            rec.state = 'received'

    @api.multi
    def process_pdf(self):
        # process ub type is process pdf than can manully process pdf
        for rec in self:
            if rec.process_ubl_type == 'no':
                rec.state = 'not_process'
            # if not original partner than create base on below value
            if rec.data_pdf and rec.email_address and not rec.original_partner_id:
                rec.original_partner_id = rec.original_partner_id.create(
                    {
                        'name': rec.email_from,
                        'email': rec.email_address,
                        'is_company': True,
                        'supplier': True,
                        'customer': False,
                        'company_id': rec.company_id.id,
                    }
                )
            # if vendor not set than set vendor as original partner also default expense account
            if not rec.partner_id:
                rec.partner_id = rec.original_partner_id.id
                rec.set_default_account_expense()

    # create record according to xml file
    @api.multi
    def process_xml(self):
        """ process xml as per value given xml file """
        ctx = self.set_lang()
        if ctx:
            self = self.with_context(ctx)
        for rec in self:
            if not rec.data_xml:
                rec.record_log(_('XML data file is not uploaded.'), 'warning')
                continue
            try:
                data = base64.decodestring(rec.data_xml)
                data_dict = xmltodict.parse(data)
                invoice_data = False
                if data_dict.get('Invoice'):
                    invoice_data = data_dict['Invoice']
                if not invoice_data and data_dict.get('doc:Invoice'):
                    invoice_data = data_dict['doc:Invoice']
                if invoice_data:
                    # set vendor bill reference,issuedate,duedate,currency,invoice type code
                    rec.vendor_bill_ref = invoice_data.get('cbc:ID', '')
                    rec.issuedate = invoice_data.get('cbc:IssueDate', '')
                    rec.duedate = invoice_data.get('cbc:DueDate', '')
                    rec.documentcurrencycode = invoice_data.get('cbc:DocumentCurrencyCode', '')
                    # set value for invoice type code
                    if invoice_data.get('cbc:InvoiceTypeCode'):
                        rec.invoice_type_code = invoice_data.get('cbc:InvoiceTypeCode', '')
                        if not isinstance(invoice_data.get('cbc:InvoiceTypeCode'), (bytes, int, float, str)):
                            rec.invoice_type_code = invoice_data.get('cbc:InvoiceTypeCode')['#text']
                    # set currency code
                    if rec.documentcurrencycode:
                        rec.currency_id = rec.env['res.currency'].search([('name', '=', rec.documentcurrencycode)])
                    # set supplier data
                    accounting_supplier = False
                    if invoice_data.get('cac:AccountingSupplierParty') or invoice_data.get('AccountingSupplierParty'):
                        accounting_supplier = invoice_data.get('AccountingSupplierParty') or invoice_data.get('cac:AccountingSupplierParty')
                        # set supplier party name
                        if accounting_supplier:
                            accounting_supplier = accounting_supplier.get('cac:Party') or accounting_supplier.get('Party')
                    # vendor personal details
                    if accounting_supplier:
                        # set party indenty number
                        PartyIdentification = accounting_supplier.get('cac:PartyIdentification', '') or accounting_supplier.get('PartyIdentification', '')
                        if not PartyIdentification:
                            PartyIdentification = accounting_supplier.get('cac:PartyLegalEntity', '') or accounting_supplier.get('PartyLegalEntity', '')
                        if PartyIdentification:
                            if not len(PartyIdentification) > 1:
                                PartyIdentification = [PartyIdentification]
                            if not isinstance(PartyIdentification, (list)):
                                PartyIdentification = [PartyIdentification]
                            for party_id in PartyIdentification:
                                data_id = party_id.get('cbc:ID', '') or party_id.get('cbc:CompanyID', '')
                                if data_id:
                                    if not isinstance(data_id, (bytes, int, float, str)):
                                        if data_id.get('@schemeAgencyName', '').lower() == 'kvk' or data_id.get('@schemeID', '').lower() == 'kvk' or data_id.get('@schemeID', '').split(':')[-1].lower() == 'kvk':
                                            rec.partyidentification = re.sub(r'[,.]', '', data_id.get('#text', ''))
                                            rec.scheme_agency_id = data_id.get('@schemeAgencyID', '')
                                        if data_id.get('@schemeAgencyName') == 'BTW' or data_id.get('@schemeID') == 'BTW':
                                            rec.party_vat = re.sub(r'[,.]', '', data_id.get('#text', ''))
                                            rec.scheme_agency_id = data_id.get('@schemeAgencyID', '')
                                    else:
                                        rec.partyidentification = re.sub(r'[,.]', '', data_id)
                        if accounting_supplier.get('cac:PartyName'):
                            rec.partyname_supplier = accounting_supplier['cac:PartyName'].get('cbc:Name', '')
                        if accounting_supplier.get('PartyName'):
                            rec.partyname_supplier = accounting_supplier['PartyName'].get('cbc:Name', '')
                        # postal address supplier
                        if accounting_supplier.get('cac:PostalAddress') or accounting_supplier.get('PostalAddress'):
                            PostalAddress = accounting_supplier.get('cac:PostalAddress') or accounting_supplier.get('PostalAddress')
                            rec.streetname_postal_supplier = PostalAddress.get('cbc:StreetName', '')
                            rec.cityname_postal_supplier = PostalAddress.get('cbc:CityName', '')
                            rec.postalzone_postal_supplier = PostalAddress.get('cbc:PostalZone', '')

                            if PostalAddress.get('cac:Country') or PostalAddress.get('Country'):
                                Country = PostalAddress.get('cac:Country') or PostalAddress.get('Country')
                                if Country.get('cbc:IdentificationCode'):
                                    rec.country_identificationcode_postal_supplier = Country.get('cbc:IdentificationCode', '')
                                if Country.get('cbc:Name'):
                                    country_id = rec.env['res.country'].search([
                                        ('name', 'like', str(Country.get('cbc:Name'))[:2]),
                                        ('currency_id', '=', rec.currency_id.id)
                                    ])
                                    if country_id:
                                        rec.country_supplier_postal_id = country_id
                                        rec.country_identificationcode_postal_supplier = country_id.code
                                if Country.get('cbc:IdentificationCode'):
                                    if not isinstance(Country.get('cbc:IdentificationCode'), (bytes, int, float, str)):
                                        rec.country_identificationcode_postal_supplier = Country.get('cbc:IdentificationCode')['#text']
                        if rec.country_identificationcode_postal_supplier and not rec.country_supplier_postal_id:
                            rec.country_supplier_postal_id = rec.env['res.country'].search([('code', '=', rec.country_identificationcode_postal_supplier)])

                        # physical address supplier
                        if accounting_supplier.get('cac:PhysicalLocation') or accounting_supplier.get('PhysicalLocation'):
                            PhysicalLocation = accounting_supplier.get('cac:PhysicalLocation') or accounting_supplier.get('PhysicalLocation')
                            physical_address = PhysicalLocation.get('cac:Address') or PhysicalLocation.get('Address')
                            if physical_address:
                                rec.streetname_physical_supplier = physical_address.get('cbc:StreetName', '')
                                rec.cityname_physical_supplier = physical_address.get('cbc:CityName', '')
                                rec.postalzone_physical_supplier = physical_address.get('cbc:PostalZone', '')
                                if physical_address.get('cac:Country') or physical_address.get('Country'):
                                    country = physical_address.get('cac:Country') or physical_address.get('Country')
                                    rec.country_identificationcode_physical_supplier = country.get('cbc:IdentificationCode', '')
                                # get street value from address line tag
                                if not rec.streetname_physical_supplier:
                                    if physical_address.get('cac:AddressLine') or physical_address.get('AddressLine'):
                                        physical_address_line = physical_address.get('cac:AddressLine') or physical_address.get('AddressLine')
                                        rec.streetname_physical_supplier = physical_address_line.get('cbc:Line', '')
                        if rec.country_identificationcode_physical_supplier:
                            rec.country_supplier_physical_id = rec.env['res.country'].search(
                                [('code', '=', rec.country_identificationcode_physical_supplier)]
                            )

                        # PartyTaxScheme supplier
                        if accounting_supplier.get('cac:PartyTaxScheme') or accounting_supplier.get('PartyTaxScheme'):
                            PartyTaxScheme = accounting_supplier.get('cac:PartyTaxScheme') or accounting_supplier.get('PartyTaxScheme')
                            rec.tax_registration_name_supplier = PartyTaxScheme.get('cbc:RegistrationName', '')
                            if PartyTaxScheme.get('cac:TaxScheme') or PartyTaxScheme.get('TaxScheme'):
                                TaxScheme = PartyTaxScheme.get('cac:TaxScheme') or PartyTaxScheme.get('TaxScheme')
                                rec.tax_id_supplier = TaxScheme.get('cbc:ID', '')
                                rec.tax_code_supplier = TaxScheme.get('cbc:TaxTypeCode', '')
                            if not rec.party_vat:
                                if PartyTaxScheme.get('cbc:CompanyID'):
                                    if not isinstance(PartyTaxScheme.get('cbc:CompanyID'), (bytes, int, float, str)):
                                        rec.party_vat = re.sub(r'[,.]', '', PartyTaxScheme['cbc:CompanyID'].get('#text', ''))
                                    else:
                                        rec.party_vat = re.sub(r'[,.]', '', PartyTaxScheme.get('cbc:CompanyID', ''))
                        # PartyLegalEntity supplier
                        if accounting_supplier.get('cac:PartyLegalEntity') or accounting_supplier.get('PartyLegalEntity'):
                            PartyLegalEntity = accounting_supplier.get('cac:PartyLegalEntity') or accounting_supplier.get('PartyLegalEntity')
                            rec.legal_entity_registration_name_supplier = PartyLegalEntity.get('cbc:RegistrationName', '')
                            if PartyLegalEntity.get('cbc:CompanyID'):
                                if not isinstance(PartyLegalEntity.get('cbc:CompanyID'), (bytes, int, float, str)):
                                    rec.company_id_supplier = re.sub(r'[,.]', '', PartyLegalEntity.get('cbc:CompanyID')['#text'])
                                else:
                                    rec.company_id_supplier = re.sub(r'[,.]', '', PartyLegalEntity.get('cbc:CompanyID', ''))
                        if accounting_supplier.get('cac:Contact') or accounting_supplier.get('Contact'):
                            contact = accounting_supplier.get('cac:Contact') or accounting_supplier.get('Contact')
                            rec.contact_supplier_phone = contact.get('cbc:Telephone', '')
                            rec.contact_supplier_email = contact.get('cbc:ElectronicMail', '')

                    # set customer data
                    accounting_customer = False
                    if invoice_data.get('cac:AccountingCustomerParty') or invoice_data.get('AccountingCustomerParty'):
                        AccountingCustomerParty = invoice_data.get('cac:AccountingCustomerParty') or invoice_data.get('AccountingCustomerParty')
                        rec.supplier_assigned_account_id = AccountingCustomerParty.get('cbc:SupplierAssignedAccountID', '')
                        accounting_customer = AccountingCustomerParty.get('cac:Party', '') or AccountingCustomerParty.get('Party', '')
                    if accounting_customer:
                        # set customer personal details
                        if accounting_customer.get('cac:PartyName') or accounting_customer.get('PartyName'):
                            PartyName = accounting_customer.get('cac:PartyName') or accounting_customer.get('PartyName')
                            rec.partyname_customer = PartyName.get('cbc:Name', '')

                        # customer postal Address
                        if accounting_customer.get('cac:PostalAddress') or accounting_customer.get('PostalAddress'):
                            PostalAddress = accounting_customer.get('cac:PostalAddress') or accounting_customer.get('PostalAddress')
                            rec.streetname_postal_customer = PostalAddress.get('cbc:StreetName', '')
                            rec.cityname_postal_customer = PostalAddress.get('cbc:CityName', '')
                            rec.postalzone_postal_customer = PostalAddress.get('cbc:PostalZone', '')
                            # set country
                            if PostalAddress.get('cac:Country') or PostalAddress.get('Country'):
                                Country = PostalAddress.get('cac:Country') or PostalAddress.get('Country')
                                rec.country_identificationcode_postal_customer = Country.get('cbc:IdentificationCode', '')
                                if not isinstance(Country.get('cbc:IdentificationCode'), (bytes, int, float, str)):
                                    rec.country_identificationcode_postal_customer = Country.get('cbc:IdentificationCode')['#text']
                            if rec.country_identificationcode_postal_customer:
                                rec.country_customer_postal_id = rec.env['res.country'].search([('code', '=', rec.country_identificationcode_postal_customer)])

                        # PartyLegalEntity customer
                        if accounting_customer.get('cac:PartyLegalEntity') or accounting_customer.get('PartyLegalEntity'):
                            PartyLegalEntity = accounting_customer.get('cac:PartyLegalEntity') or accounting_customer.get('PartyLegalEntity')
                            rec.legal_entity_registration_name_customer = PartyLegalEntity.get('cbc:RegistrationName', '')
                            rec.company_id_customer = PartyLegalEntity.get('cbc:CompanyID', '')

                            if PartyLegalEntity.get('cbc:CompanyID'):
                                if not isinstance(PartyLegalEntity.get('cbc:CompanyID'), (bytes, int, float, str)):
                                    if PartyLegalEntity['cbc:CompanyID'].get('#text'):
                                        rec.company_id_customer = PartyLegalEntity.get('cbc:CompanyID')['#text']
                        if accounting_customer.get('cac:Contact') or accounting_customer.get('Contact'):
                            Contact = accounting_customer.get('cac:Contact') or accounting_customer.get('Contact')
                            if isinstance(Contact, (bytes, int, float, str)):
                                rec.contact_customer = Contact
                            else:
                                rec.contact_customer = Contact.get('cbc:Telephone', '')

                    # vendor Bank details:
                    paymentMeans = invoice_data.get('cac:PaymentMeans', '') or invoice_data.get('PaymentMeans', '')
                    if paymentMeans:
                        payee_financial_account = paymentMeans.get('cac:PayeeFinancialAccount', '') or paymentMeans.get('PayeeFinancialAccount', '')
                        if payee_financial_account:
                            if payee_financial_account.get('cbc:ID'):
                                # set vendor account number
                                if not isinstance(payee_financial_account.get('cbc:ID'), (bytes, int, float, str)):
                                    rec.vendor_acc_account = payee_financial_account['cbc:ID'].get('#text', '')
                                else:
                                    rec.vendor_acc_account = payee_financial_account.get('cbc:ID', '')
                            financial_institution_branch = payee_financial_account.get('cac:FinancialInstitutionBranch', '') or payee_financial_account.get('FinancialInstitutionBranch', '')
                            if financial_institution_branch:
                                financial_institution = financial_institution_branch.get('cac:FinancialInstitution', '') or financial_institution_branch.get('FinancialInstitution', '')
                                if financial_institution:
                                    # set bic code
                                    if financial_institution.get('cbc:ID'):
                                        if not isinstance(financial_institution.get('cbc:ID'), (bytes, int, float, str)):
                                            rec.bic_code = financial_institution['cbc:ID'].get('#text', '')
                                        else:
                                            rec.bic_code = financial_institution.get('cbc:ID', '')

                    # LegalMonetaryTotal
                    legal_mobetary_total = invoice_data.get('cac:LegalMonetaryTotal', '') or invoice_data.get('LegalMonetaryTotal', '')
                    if legal_mobetary_total:
                        # set without tax amount
                        if legal_mobetary_total.get('cbc:LineExtensionAmount'):
                            rec.line_extension_amount = legal_mobetary_total['cbc:LineExtensionAmount'].get('#text', '')
                        # set amount with tax
                        if legal_mobetary_total.get('cbc:TaxExclusiveAmount'):
                            rec.tax_exclusive_amount = legal_mobetary_total['cbc:TaxExclusiveAmount'].get('#text', '')
                            if rec.tax_exclusive_amount <= 0.00:
                                rec.tax_exclusive_amount = rec.line_extension_amount
                        # set total amount
                        if legal_mobetary_total.get('cbc:PayableAmount'):
                            rec.payable_amount = legal_mobetary_total['cbc:PayableAmount'].get('#text', '')
                        # set total amount include tax
                        if legal_mobetary_total.get('cbc:TaxInclusiveAmount'):
                            rec.tax_inclusive_amount = legal_mobetary_total['cbc:TaxInclusiveAmount'].get('#text', '')
                            if rec.tax_inclusive_amount <= 0.00:
                                rec.tax_inclusive_amount = rec.payable_amount

                    # Total tax amount
                    total_tax_amount = invoice_data.get('cac:TaxTotal', '') or invoice_data.get('TaxTotal', '')
                    if total_tax_amount:
                        if total_tax_amount.get('cbc:TaxAmount'):
                            rec.total_tax_amount = total_tax_amount['cbc:TaxAmount'].get('#text', '')
                    if rec.total_tax_amount <= 0.00:
                        rec.total_tax_amount = rec.tax_inclusive_amount - rec.tax_exclusive_amount

                    # Invoice line
                    invoice_line_data_dict = invoice_data.get('cac:InvoiceLine', '') or invoice_data.get('InvoiceLine', '')
                    invoice_line_dict = {}
                    if invoice_line_data_dict:
                        if rec.receive_vendor_bill_line_ids:
                            rec.receive_vendor_bill_line_ids.unlink()
                        if type(invoice_line_data_dict) is not list:
                            invoice_line_data_dict = [invoice_line_data_dict]
                        for line in invoice_line_data_dict:
                            invoice_line_dict = {}
                            # vendor_rec_bill ref ,invoice qty
                            invoice_line_dict.update({
                                'receive_vendor_bill_id': rec.id,
                                'invoiced_quantity': line.get('cbc:InvoicedQuantity', '')
                            })
                            if not isinstance(invoice_line_dict['invoiced_quantity'], (bytes, int, float, str)):
                                invoice_line_dict['invoiced_quantity'] = invoice_line_dict['invoiced_quantity']['#text']
                            if line.get('cac:TaxTotal') or line.get('TaxTotal'):
                                # invoice line taxtotal,taxsubtotal
                                Taxtotal = line.get('cac:TaxTotal') or line.get('TaxTotal')
                                if Taxtotal.get('cbc:TaxAmount'):
                                    invoice_line_dict.update(
                                        {
                                            'tax_amount_invoice_line': Taxtotal['cbc:TaxAmount'].get('#text', '')
                                        }
                                    )
                                if Taxtotal.get('cac:TaxSubtotal') or Taxtotal.get('TaxSubtotal'):
                                    TaxSubtotal = Taxtotal.get('cac:TaxSubtotal') or Taxtotal.get('TaxSubtotal')
                                    # set tax amount
                                    if TaxSubtotal.get('cbc:TaxableAmount'):
                                        invoice_line_dict.update(
                                            {
                                                'tax_subtotal_invoice_line': TaxSubtotal['cbc:TaxableAmount'].get('#text', '')
                                            }
                                        )
                                    # set tax percent
                                    if TaxSubtotal.get('cbc:Percent'):
                                        invoice_line_dict.update({'tax_percent_invoice_line': TaxSubtotal.get('cbc:Percent', '')})
                                    else:
                                        if TaxSubtotal.get('cac:TaxCategory') or TaxSubtotal.get('TaxCategory'):
                                            TaxCategory = TaxSubtotal.get('cac:TaxCategory', '') or TaxSubtotal.get('TaxCategory', '')
                                            invoice_line_dict.update({'tax_percent_invoice_line': TaxCategory.get('cbc:Percent', '')})
                            if line.get('cbc:LineExtensionAmount'):
                                invoice_line_dict.update({'line_extension_amount_invoice_line': line['cbc:LineExtensionAmount'].get('#text', '')})
                            # invoice description
                            if line.get('cac:Item') or line.get('Item'):
                                invoice_item = line.get('cac:Item') or line.get('Item')
                                b_desc = invoice_item.get('cbc:Description', '') and BeautifulSoup(invoice_item.get('cbc:Description', ''))
                                b_name = invoice_item.get('cbc:Name', '') and BeautifulSoup(invoice_item.get('cbc:Name', ''))
                                invoice_line_dict.update({'description': b_desc and b_desc.get_text(), 'name': b_name and b_name.get_text()})
                                # get quantity from PackQuantity if invoiced quantity is 0
                                if invoice_item.get('cbc:PackQuantity'):
                                    invoiced_quantity = invoice_line_dict['invoiced_quantity']
                                    if invoiced_quantity.isdigit():
                                        invoiced_quantity = int(invoiced_quantity)
                                        if invoiced_quantity <= 0:
                                            if not isinstance(invoice_item.get('cbc:PackQuantity'), (bytes, int, float, str)):
                                                invoice_line_dict.update({'invoiced_quantity':
                                                                          invoice_item['cbc:PackQuantity'].get('#text', '')})
                                            else:
                                                invoice_line_dict.update({'invoiced_quantity':
                                                                          invoice_item.get('cbc:PackQuantity', '')})

                            # invoice line unit price
                            if line.get('cac:Price') or line.get('Price'):
                                item_price = line.get('cac:Price') or line.get('Price')
                                if item_price.get('cbc:PriceAmount'):
                                    invoice_line_dict.update({'price_amount': item_price['cbc:PriceAmount'].get('#text', ''), 'currency_id': rec.currency_id.id or False})
                            rec.receive_vendor_bill_line_ids.create(invoice_line_dict)
                    # from xml file data is added than it bool true is process xml
                    # Update log
                    rec.is_process_xml = True
                    rec.record_log(_('Xml file is successfully loaded.'))
                    rec.receive_vendor_bill_line_ids.update_price_amount_base_total_amount()
                else:
                    rec.record_log(_('Xml file does not contain valid data.'))
            # if it is any  tag mismatch or other issue while read data from xml file or
            # not valid file raise exception and update chatter
            except Exception as e:
                rec.state = 'exception'
                rec.record_log(_("Please upload a valid xml file for processing a UBL invoice '%s'.") % (e), 'warning')
        return True

    @api.one
    def send_pdf_mail_to_ubl(self):
        ctx = self.set_lang()
        if ctx:
            self = self.with_context(ctx)
        mail_pool = self.env['mail.mail']
        # send pdf to xml file base on ubl config mail.
        config_ubl_provider_email_address = self.company_id.company_email_address_fwd_vendor_bill_to
        ctx = {}
        # if not config mail and mail not send and update log
        if not config_ubl_provider_email_address:
            self.record_log(_("Please configure the email address of UBL Provider for company '%s'.") % (self.company_id.name), 'warning')
            return False
        # if not pdf update log mail not send
        if not self.data_pdf:
            self.record_log(_('There is no PDF file for sending to UBL Provider.'), 'warning')
            return False
        # if xml file is already exist than no need to send pdf and update chatter
        if self.data_xml:
            self.record_log(
                _("XML file already exists. So you are not able to do further process for forward to ubl provider.")
            )
            self.state = 'rec_back_from_ubl_provider'
            return True
        # send pdf to ubl provider
        ctx.update({
            'email_to': config_ubl_provider_email_address or '',
            'email_from': self.env.user.company_id.email or '',
        })
        template = self.env['ir.model.data'].get_object(
            'account_invoice_ubl_import', 'ubl_provider_email')
        # check mail send and add attachment
        # state change  forward to ubl provider and update log
        mail_id = template.with_context(ctx).send_mail(self.id, force_send=False)
        if mail_id:
            vals = {'model': 'receive.vendor.bill'}
            vals['attachment_ids'] = [
                (0, 0, {'name': '%s.pdf' % self.seq_name or 'Attachment',
                        'datas_fname': '%s.pdf' % self.seq_name or 'File_pdf',
                        'datas': self.data_pdf})]
            the_mailmessage = mail_pool.browse(mail_id).mail_message_id
            if the_mailmessage:
                the_mailmessage.write(vals)
            mail_pool.browse(mail_id).send()
            mail_obj = mail_pool.search([('id', '=', mail_id)])
            if mail_obj:
                self.record_log(_('Mail not send,Please send again.'), 'warning')
            else:
                self.record_log(_('PDF file is successfully send to Ubl Provider.'))
                self.state = 'fwd_to_ubl_provider'

    @api.one
    def check_process_ubl(self):
        # check process ubl base on ubl configuration from supplier do further process
        # if process_ubl than send mail to ubl provider.
        # if process pdf than set vendor as original partner and create invoice without invoice line
        # if process type not set than state change to not process
        if self.data_pdf:
            if not self.original_partner_id and self.email_address:
                self.original_partner_id = self.env['res.partner'].search([
                    ('email', '=', self.email_address),
                    ('company_id', '=', self.company_id.id)], limit=1)
            if not self.original_partner_id and self.email_address:
                self.original_partner_id = self.original_partner_id.create(
                    {
                        'name': self.email_from,
                        'email': self.email_address,
                        'is_company': True,
                        'supplier': True,
                        'customer': False,
                        'company_id': self.company_id.id,
                    }
                )
            # if process ubl type than perform as per below given
            if self.process_ubl_type:
                # if partner company not  same to record company  unlink partner company
                if self.original_partner_id and self.original_partner_id.company_id != self.company_id:
                    self.original_partner_id.write({'company_id': False})
                if self.process_ubl_type == 'no':
                    self.state = 'not_process'
                elif self.process_ubl_type == 'process_pdf':
                    if not self.partner_id and self.original_partner_id:
                        self.partner_id = self.original_partner_id.id
                    # set default accouynt and create invoice
                    self.set_default_account_expense()
                    self.create_invoice()
                else:
                    self.send_pdf_mail_to_ubl()
            self._cr.commit()

    # Cron_job function
    @api.model
    def send_pdf_to_ubl_provider(self):
        # send pdf to ubl provider if state received
        for rec in self.env['receive.vendor.bill'].search([('state', '=', 'received')]):
            rec.check_process_ubl()

    @api.model
    def vendor_process_bill(self):
        # vendor bill process through cron check all possible condition mention in above method
        for rec in self.env['receive.vendor.bill'].search([('state', '=', 'rec_back_from_ubl_provider'), ('data_xml', '!=', False), ('is_process_xml', '=', False)]):
            try:
                # process xml file  and create invoice
                rec.process_xml()
                rec.create_invoice(auto=True)
                if rec.account_invoice_id:
                    rec.state = 'vendor_bill_pro'
                self._cr.commit()
            except Exception as e:
                # while run cron any issue reaise exception
                self.record_log(_("Error From Cron Something went wrong: '%s'.") % (e), 'warning')


class receive_vendor_bill_line(models.Model):
    _name = 'receive.vendor.bill.line'

    receive_vendor_bill_id = fields.Many2one(
        'receive.vendor.bill', ondelete='cascade',
        string='Received Vendor Bill')
    invoiced_quantity = fields.Float(string='Invoiced Quantity')
    tax_amount_invoice_line = fields.Float(string='Tax Amount')
    tax_subtotal_invoice_line = fields.Float(string='Tax Subtotal')
    tax_percent_invoice_line = fields.Float(string='Percent')
    line_extension_amount_invoice_line = fields.Float(
        string='Line Extension Amount')
    # product
    description = fields.Text(string='Description')
    name = fields.Char(string='Name')
    price_amount = fields.Float(string='Price Amount')
    currency_id = fields.Many2one('res.currency', string='Currency')

    @api.multi
    def update_price_amount_base_total_amount(self):
        # if price amount not given than calculate base on quantity and total line amount
        for rec in self:
            if rec.price_amount == 0.0 and rec.invoiced_quantity:
                if rec.invoiced_quantity > 0:
                    rec.price_amount = rec.line_extension_amount_invoice_line/rec.invoiced_quantity


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model
    def message_route_process(self, message, message_dict, routes):
        self = self.with_context(attachments_mime_plainxml=True)
        # import XML attachments as text
        # postpone setting message_dict.partner_ids after message_post, to avoid double notifications
        original_partner_ids = message_dict.pop('partner_ids', [])
        thread_id = False
        for model, thread_id, custom_values, user_id, alias in routes or ():
            if model:
                Model = self.env[model]
                if not (thread_id and hasattr(Model, 'message_update') or hasattr(Model, 'message_new')):
                    raise ValueError(
                        "Undeliverable mail with Message-Id %s, model %s does not accept incoming emails" %
                        (message_dict['message_id'], model)
                    )

                # disabled subscriptions during message_new/update to avoid having the system user running the
                # email gateway become a follower of all inbound messages
                MessageModel = Model.sudo(user_id).with_context(mail_create_nosubscribe=True, mail_create_nolog=True)
                if thread_id and hasattr(MessageModel, 'message_update'):
                    thread = MessageModel.browse(thread_id)
                    thread.message_update(message_dict)
                else:
                    # if a new thread is created, parent is irrelevant
                    message_dict.pop('parent_id', None)
                    thread = MessageModel.message_new(message_dict, custom_values)
                    # customization to get thread_id from thread
                    thread_id = thread.id
            else:
                if thread_id:
                    raise ValueError("Posting a message without model should be with a null res_id, to create a private message.")
                thread = self.env['mail.thread']
            if not hasattr(thread, 'message_post'):
                thread = self.env['mail.thread'].with_context(thread_model=model)

            # replies to internal message are considered as notes, but parent message
            # author is added in recipients to ensure he is notified of a private answer
            partner_ids = []
            if message_dict.pop('internal', False):
                subtype = 'mail.mt_note'
                if message_dict.get('parent_id'):
                    parent_message = self.env['mail.message'].sudo().browse(message_dict['parent_id'])
                    partner_ids = [(4, parent_message.author_id.id)]
            else:
                subtype = 'mail.mt_comment'
            new_msg = thread.message_post(subtype=subtype, partner_ids=partner_ids, **message_dict)

            if original_partner_ids:
                # postponed after message_post, because this is an external message and we don't want to create
                # duplicate emails due to notifications
                new_msg.write({'partner_ids': original_partner_ids})

        return thread_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
