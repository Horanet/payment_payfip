import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request

from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class PayFIPController(http.Controller):
    @http.route('/payment/tipiregie/pay', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def tipiregie_pay(self, **post):
        reference = post.pop('reference', False)
        amount = float(post.pop('amount', 0))
        return_url = post.pop('return_url', '/')
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference), ('amount', '=', amount)])
        if tx and tx.acquirer_id.provider == 'tipiregie':
            # PayFIP doesn't accept two attempts with the same operation identifier, we check if transaction has
            # already sent and recreate it in this case.
            if tx.tipiregie_sent_to_webservice:
                tx = tx.copy({
                    'reference': request.env['payment.transaction'].get_next_reference(tx.reference),
                })

            tx.write({
                'tipiregie_return_url': return_url,
                'tipiregie_sent_to_webservice': True,
            })
            return werkzeug.utils.redirect('{url}?idop={idop}'.format(
                url=tx.acquirer_id.tipiregie_form_action_url,
                idop=tx.tipiregie_operation_identifier,
            ))
        else:
            return werkzeug.utils.redirect('/')

    @http.route('/payment/tipiregie/ipn/', type='http', auth='none', methods=['POST'], csrf=False)
    def tipiregie_ipn(self, **post):
        """Process PayFIP IPN."""
        _logger.debug('Beginning PayFIP IPN form_feedback with post data %s', pprint.pformat(post))
        if not post or not post.get('idop'):
            raise ValidationError("No idOp found for transaction on PayFIP")

        idop = post.get('idop', False)
        request.env['payment.transaction'].form_feedback(idop, 'tipiregie')

        return ''

    @http.route('/payment/tipiregie/dpn', type='http', auth="none", methods=['POST', 'GET'], csrf=False)
    def tipiregie_dpn(self, **post):
        """Process PayFIP DPN."""
        _logger.debug('Beginning PayFIP DPN form_feedback with post data %s', pprint.pformat(post))
        if not post or not post.get('idop'):
            raise ValidationError("No idOp found for transaction on PayFIP")

        # idop = post.get('idop', False)
        # request.env['payment.transaction'].form_feedback(idop, 'tipiregie')
        _logger.critical(str(request.cookies))


        url = '/'
        tx = request.env['payment.transaction']._tipiregie_form_get_tx_from_data(idop)
        if tx and tx.tipiregie_return_url:
            url = tx.tipiregie_return_url
        return werkzeug.utils.redirect(url)
