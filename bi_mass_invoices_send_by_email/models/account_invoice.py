# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) BrowseInfo (http://browseinfo.in)
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

from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class wiz_mass_invoice(models.TransientModel):
    _name = 'wiz.mass.invoice'
    
    @api.multi 
    def mass_invoice_email_send(self):
        context = self._context
        active_ids = context.get('active_ids')
        super_user = self.env['res.users'].browse(SUPERUSER_ID)
        for a_id in active_ids:
            account_invoice_brw = self.env['account.invoice'].browse(a_id)
            for partner in account_invoice_brw.partner_id:
                partner_email = partner.email
                if not partner_email:
                    raise UserError(_('%s customer has no email id please enter email address')
                            % (account_invoice_brw.partner_id.name)) 
                else:
                    template_id = self.env['ir.model.data'].get_object_reference(
                                                                      'account', 
                                                                      'email_template_edi_invoice')[1]
                    email_template_obj = self.env['mail.template'].browse(template_id)
                    if template_id:
                        values = email_template_obj.generate_email(a_id, fields=None)
                        #values['email_from'] = super_user.email
                        values['email_to'] = partner.email
                        values['res_id'] = a_id
                        ir_attachment_obj = self.env['ir.attachment']
                        
                        vals = {
                                'name' : account_invoice_brw,
                                'type' : 'binary',
                                'datas' : values['attachments'][0][1],
                                'res_id' : a_id,
                                'res_model' : 'account.invoice',
                        }
                        attachment_id = ir_attachment_obj.create(vals)
                        mail_mail_obj = self.env['mail.mail']
                        msg_id = mail_mail_obj.create(values)
                        msg_id.attachment_ids=[(6,0,[attachment_id.id])]
                        if msg_id:
                            mail_mail_obj.send([msg_id])
                                                     
        return True
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
