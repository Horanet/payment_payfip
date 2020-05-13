import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate v10 to v11.

    - Set tipiregie_form as view_template_id for all existing tipiregie acquirers
    """
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})

        tipiregie_form = env.ref('payment_tipiregie.tipiregie_form')
        tipiregie_acquirers = env['payment.acquirer'].with_context(active_test=False).search([
            ('provider', '=', 'tipiregie')
        ])
        tipiregie_acquirers.write({'view_template_id': tipiregie_form.id})
