from odoo import http
from odoo.http import request
from odoo import conf, http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import uuid


from odoo.addons.project.controllers.project_sharing_chatter import ProjectSharingChatter

class ChatterPortal(ProjectSharingChatter):

    def _generate_access_token(self):
        return str(uuid.uuid4())

    def _check_sale_access_and_get_token(self, res_model, res_id, token=None):
        sale = request.env[res_model].sudo().with_context(active_test=False).search([('id', '=', res_id)])
        sale[sale._mail_post_token_field] = self._generate_access_token()

        return sale[sale._mail_post_token_field]


    @http.route()
    def portal_message_fetch(self, res_model, res_id, domain=False, limit=10, offset=0, **kw):
        if res_model == 'sale.order':
            token = self._check_sale_access_and_get_token(res_model, res_id, kw.get('token'))
            if token is not None:
                kw['token'] = token  # Update token (either string which contains token value or False)
        return super().portal_message_fetch(res_model, res_id, domain=domain, limit=limit, offset=offset, **kw)

    @http.route()
    def portal_chatter_init(self, res_model, res_id, domain=False, limit=False, **kwargs):
        is_user_public = request.env.user.has_group('base.group_public')
        message_data = self.portal_message_fetch(res_model, res_id, domain=domain, limit=limit, **kwargs)
        display_composer = False
        if res_model == 'sale.order':
            token = self._check_sale_access_and_get_token(res_model, res_id, kwargs.get('token'))
            if token is not None:
                kwargs['token'] = token
        if kwargs.get('allow_composer'):
            display_composer = kwargs.get('token') or not is_user_public
        return {
            'messages': message_data['messages'],
            'options': {
                'message_count': message_data['message_count'],
                'is_user_public': is_user_public,
                'is_user_employee': request.env.user._is_internal(),
                'is_user_publisher': request.env.user.has_group('website.group_website_restricted_editor'),
                'display_composer': display_composer,
                'partner_id': request.env.user.partner_id.id
            }
        }



class SalePortal(CustomerPortal):

    def _prepare_quotations_domain(self, partner):
        return ['|',
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
                ('creator_user','=',request.env.user.id),
            ('state', '=', 'sent')
        ]

    def _prepare_orders_domain(self, partner):
        return [
            '|',
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('creator_user', '=', request.env.user.id),
            ('state', '=', 'sale'),
        ]





    def _prepare_sales_sharing_session_info(self):
        session_info = request.env['ir.http'].session_info()
        user_context = dict(request.env.context) if request.session.uid else {}
        mods = conf.server_wide_modules or []
        if request.env.lang:
            lang = request.env.lang
            session_info['user_context']['lang'] = lang
            # Update Cache
            user_context['lang'] = lang
        lang = user_context.get("lang")
        translation_hash = request.env['ir.http'].get_web_translations_hash(mods, lang)
        cache_hashes = {
            "translations": translation_hash,
        }

        sales_company = request.env.company
        action = request.env['ir.actions.act_window']._for_xml_id('sale_portal.sale_order_create_action')

        session_info.update(
            cache_hashes=cache_hashes,
            action_name=action,
            user_companies={
                'current_company': sales_company.id,
                'allowed_companies': {
                    sales_company.id: {
                        'id': sales_company.id,
                        'name': sales_company.name,
                    },
                },
            },
            # FIXME: See if we prefer to give only the currency that the portal user just need to see the correct information in project sharing
            currencies=request.env['ir.http'].get_currencies(),
        )
        return session_info



    @http.route('/order/create', auth='user',website=True)
    def create_sale_order(self, **kw):
        return request.render("sale_portal.sales_sharing_portal")

    @http.route("/order/sale/sale_sharing", type="http", auth="user", methods=['GET'])
    def render_sales_backend_view(self, **kwargs):
        return request.render(
            'sale_portal.sales_sharing_embed',
            {'session_info': self._prepare_sales_sharing_session_info()},
        )



    # @http.route('/sale_portal/sale_portal/objects', auth='public')
    # def list(self, **kw):
    #     return http.request.render('sale_portal.listing', {
    #         'root': '/sale_portal/sale_portal',
    #         'objects': http.request.env['sale_portal.sale_portal'].search([]),
    #     })
    #
    # @http.route('/sale_portal/sale_portal/objects/<model("sale_portal.sale_portal"):obj>', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('sale_portal.object', {
    #         'object': obj
    #     })

