import logging
import pprint

import werkzeug

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PayFIPController(http.Controller):
    @http.route('/payment/payfip/pay', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def payfip_pay(self, **post):
        reference = post.pop('reference', False)
        amount = float(post.pop('amount', 0))
        return_url = post.pop('return_url', '/payment/process')
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference), ('amount', '=', amount)])
        if tx and tx.provider_id.name == 'payfip':
            # PayFIP doesn't accept two attempts with the same operation identifier, we check if transaction has
            # already sent and recreate it in this case.
            if tx.payfip_sent_to_webservice:
                tx = tx.copy(
                    {
                        'reference': request.env['payment.transaction']._compute_reference(tx.provider_code),
                    }
                )

            tx.write(
                {
                    'payfip_return_url': return_url,
                    'payfip_sent_to_webservice': True,
                }
            )
            return werkzeug.utils.redirect(
                '{url}?idop={idop}'.format(
                    url=tx.provider_id.payfip_form_action_url,
                    idop=tx.payfip_operation_identifier,
                )
            )
        else:
            return werkzeug.utils.redirect('/')

    @http.route('/payment/payfip/ipn/', type='http', auth='none', methods=['POST'], csrf=False)
    def payfip_ipn(self, **post):
        """Process PayFIP IPN."""
        _logger.debug("Beginning PayFIP IPN form_feedback with post data %s", pprint.pformat(post))
        if not post or not post.get('idop'):
            raise Exception("No idOp found for transaction on PayFIP")

        request.env['payment.transaction'].sudo()._handle_notification_data('payfip', post)

        return ''

    @http.route('/payment/payfip/dpn', type='http', auth='none', methods=['POST', 'GET'], csrf=False)
    def payfip_dpn(self, **post):
        """Process PayFIP DPN."""
        _logger.debug("PayFIP DPN form_feedback with post data %s", pprint.pformat(post))
        if not post or not post.get('idop'):
            raise Exception("No idOp found for transaction on PayFIP")

        request.env['payment.transaction'].sudo()._handle_notification_data('payfip', post)
        return request.redirect('/payment/status')
