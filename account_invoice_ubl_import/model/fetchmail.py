# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.


import logging

from odoo import api, fields, models, _


_logger = logging.getLogger(__name__)
MAX_POP_MESSAGES = 50
MAIL_TIMEOUT = 60


class FetchmailServer(models.Model):
    _inherit = "fetchmail.server"

    company_id = fields.Many2one('res.company', string='Company')
    journal_id = fields.Many2one('account.journal', 
                string='Journal')
    config_process_ubl = fields.Selection(
        [
            ('process_pdf', 'Process the PDF Vendor Bill'),
            ('process_ubl', 'Process the UBL Vendor Bill')
        ],
        string='Process Vendor Bill'
    )

    @api.onchange('config_process_ubl')
    def _onchange_config_process_ubl(self):
        # set object action on change of Process Vendor Bill option
        value = {'value': {}}
        if self.config_process_ubl:
            object_id = self.env['ir.model'].search([
                ('model', '=', 'receive.vendor.bill')])
            if object_id:
                value.update({'value': {'object_id': object_id.id}})
        return value

    @api.multi
    def fetch_mail(self):
        """ while fetch mail than accoding to company set in incoming mail server
            receive vendor bill  is  create on basis of respective company """

        """ WARNING: meant for cron usage only - will commit() after each email! """
        additionnal_context = {
            'fetchmail_cron_running': True
        }
        MailThread = self.env['mail.thread']
        for server in self:
            _logger.info('start checking for new emails on %s server %s', server.type, server.name)
            additionnal_context['fetchmail_server_id'] = server.id
            additionnal_context['server_type'] = server.type
            count, failed = 0, 0
            imap_server = None
            pop_server = None
            if server.type == 'imap':
                try:
                    imap_server = server.connect()
                    imap_server.select()
                    result, data = imap_server.search(None, '(UNSEEN)')
                    for num in data[0].split():
                        res_id = None
                        result, data = imap_server.fetch(num, '(RFC822)')
                        imap_server.store(num, '-FLAGS', '\\Seen')
                        try:
                            res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, data[0][1], save_original=server.original, strip_attachments=(not server.attach))
                            if res_id:
                                # Ubl Customization set process ubl type and company
                                if server.object_id.model == 'receive.vendor.bill':
                                    res_obj = self.env['receive.vendor.bill'].browse(res_id)
                                    res_vals = {}
                                    # set process ubl type if set
                                    res_vals.update({
                                        'process_ubl_type': server.config_process_ubl if server.config_process_ubl else 'no',
                                        'journal_id': server.journal_id.id
                                    })
                                    # set company if set
                                    if server.company_id:
                                        res_vals.update({'company_id': server.company_id.id})
                                    res_obj.write(res_vals)
                                    # ubl custamization complete
                        except Exception:
                            _logger.info('Failed to process mail from %s server %s.', server.type, server.name, exc_info=True)
                            failed += 1
                        if res_id and server.action_id:
                            server.action_id.with_context({
                                'active_id': res_id,
                                'active_ids': [res_id],
                                'active_model': self.env.context.get("thread_model", server.object_id.model)
                            }).run()
                        imap_server.store(num, '+FLAGS', '\\Seen')
                        self._cr.commit()
                        count += 1
                    _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", count, server.type, server.name, (count - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.type, server.name, exc_info=True)
                finally:
                    if imap_server:
                        imap_server.close()
                        imap_server.logout()
            elif server.type == 'pop':
                try:
                    while True:
                        pop_server = server.connect()
                        (num_messages, total_size) = pop_server.stat()
                        pop_server.list()
                        for num in range(1, min(MAX_POP_MESSAGES, num_messages) + 1):
                            (header, messages, octets) = pop_server.retr(num)
                            message = b'\n'.join(messages)
                            res_id = None
                            try:
                                res_id = MailThread.with_context(**additionnal_context).message_process(server.object_id.model, message, save_original=server.original, strip_attachments=(not server.attach))
                                if res_id:
                                    # Ubl Customization start
                                    if server.object_id.model == 'receive.vendor.bill':
                                        res_obj = self.env['receive.vendor.bill'].browse(res_id)
                                        res_vals = {}
                                        # set process ubl type
                                        res_vals.update({
                                            'process_ubl_type': server.config_process_ubl if server.config_process_ubl else 'no',
                                            'journal_id' : server.journal_id.id
                                        })
                                        # set company
                                        if server.company_id:
                                            res_vals.update({'company_id': server.company_id.id})

                                        res_obj.write(res_vals)
                                        # ubl customization complete
                                pop_server.dele(num)
                            except Exception:
                                _logger.info('Failed to process mail from %s server %s.', server.type, server.name, exc_info=True)
                                failed += 1
                            if res_id and server.action_id:
                                server.action_id.with_context({
                                    'active_id': res_id,
                                    'active_ids': [res_id],
                                    'active_model': self.env.context.get("thread_model", server.object_id.model)
                                }).run()
                            self.env.cr.commit()
                        if num_messages < MAX_POP_MESSAGES:
                            break
                        pop_server.quit()
                        _logger.info("Fetched %d email(s) on %s server %s; %d succeeded, %d failed.", num_messages, server.type, server.name, (num_messages - failed), failed)
                except Exception:
                    _logger.info("General failure when trying to fetch mail from %s server %s.", server.type, server.name, exc_info=True)
                finally:
                    if pop_server:
                        pop_server.quit()
            server.write({'date': fields.Datetime.now()})
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
