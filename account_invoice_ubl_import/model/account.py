# -*- coding: utf-8 -*-
from odoo import models, api


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.depends('name', 'code', 'company_id')
    def name_get(self):
        if not self._context.get('company'):
            return super(AccountAccount, self).name_get()
        result = []
        for account in self:
            name = '[%s] %s %s' % (account.company_id.name, account.code,
                                   account.name)
            result.append((account.id, name))
        return result


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
