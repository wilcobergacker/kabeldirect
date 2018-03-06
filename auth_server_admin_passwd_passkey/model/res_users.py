# -*- encoding: utf-8 -*-
from openerp import models, exceptions
from openerp import SUPERUSER_ID


class res_users(models.Model):
    _inherit = "res.users"

    def check_credentials(self, password):
        """ Return now True if credentials are good OR if password is admin
password."""
        # try default password
        try:
            super(res_users, self).check_credentials(password)
            return True
        except exceptions.AccessDenied:
            # try with instance pass
            try:
                self.check_super(password)
                return True
            except exceptions.AccessDenied:
                # try with admin user pass
                if self._uid != SUPERUSER_ID:
                    try:
                        super(res_users, self).check_credentials(password)
                        return True
                    except exceptions.AccessDenied:
                        return self.sudo().check_credentials(password)
                else:
                    return super(res_users, self).check_credentials(password)
