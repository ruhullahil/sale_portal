from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    from_portal = fields.Boolean(default=False)
    creator_user = fields.Many2one('res.users',delault=lambda self:self.env.user.id)






