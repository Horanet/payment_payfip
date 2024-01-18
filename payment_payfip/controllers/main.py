import logging
import pprint
import werkzeug

from odoo import _, http
from odoo.http import request

from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class PayFIPController(http.Controller):
    @http.route('/payment/payfip/pay', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def payfip_pay(self, **post):
        reference = post.pop('reference', False)
        amount = float(post.pop('amount', 0))
        return_url = post.pop('return_url', '/payment/process')
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference), ('amount', '=', amount)])
        if tx and tx.acquirer_id.provider == 'payfip':
            # PayFIP doesn't accept two attempts with the same operation identifier, we check if transaction has
            # already sent and recreate it in this case.
            if tx.payfip_sent_to_webservice:
                tx = tx.copy({
                    'reference': request.env['payment.transaction'].get_next_reference(tx.reference),
                })

            tx.write({
                'payfip_return_url': return_url,
                'payfip_sent_to_webservice': True,
            })
            return werkzeug.utils.redirect('{url}?idop={idop}'.format(
                url=tx.acquirer_id.payfip_form_action_url,
                idop=tx.payfip_operation_identifier,
            ))
        else:
            return werkzeug.utils.redirect('/')

    @http.route('/payment/payfip/ipn/', type='http', auth='none', methods=['POST'], csrf=False)
    def payfip_ipn(self, **post):
        """Process PayFIP IPN."""
        _logger.debug('Beginning PayFIP IPN form_feedback with post data %s', pprint.pformat(post))
        if not post or not post.get('idop'):
            raise ValidationError("No idOp found for transaction on PayFIP")

        idop = post.get('idop', False)
        result = request.env['payment.transaction'].form_feedback(idop, 'payfip')

        return _('Accepted payment, order has been updated.') if result \
            else _('Payment failure, order has been cancelled.')

    @http.route('/payment/payfip/dpn', type='http', auth="none", methods=['POST', 'GET'], csrf=False)
    def payfip_dpn(self, **post):
        """Process PayFIP DPN."""
        _logger.debug('Beginning PayFIP DPN form_feedback with post data %s', pprint.pformat(post))
        if not post or not post.get('idop'):
            raise ValidationError("No idOp found for transaction on PayFIP")

        idop = post.get('idop', False)
        request.env['payment.transaction'].form_feedback(idop, 'payfip')

        tx = request.env['payment.transaction']._payfip_form_get_tx_from_data(idop)
        url = tx.payfip_return_url if tx and tx.payfip_return_url else '/shop/cart'
        return werkzeug.utils.redirect(url)
