from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    from_portal = fields.Boolean(default=False)
    creator_user = fields.Many2one('res.users',compute='_compute_user',store=True)
    message_follower_ids = fields.One2many(
        'mail.followers', 'res_id', string='Followers', groups='base.group_user,base.group_portal')

    @api.depends('partner_id')
    def _compute_user(self):
        for rec in self:
            rec.creator_user = self.env.user












