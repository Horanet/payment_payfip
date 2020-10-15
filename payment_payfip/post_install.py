import logging

from odoo import api, SUPERUSER_ID

from odoo.addons.payment.models.payment_acquirer import create_missing_journal_for_acquirers

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Create new journal."""

    # Create journal for the new acquirer
    create_missing_journal_for_acquirers(cr, registry)

    # If migrate from old tipiregie acquirer
    env = api.Environment(cr, SUPERUSER_ID, {})
    # If old tipi journal exist we change the new journal for the old one
    tipiregie_journal = env['account.journal'].search([('code', '=', 'TIPIR')])
    if tipiregie_journal:
        _logger.info("Assign old journal to the new aquirer")
        env.ref('payment_payfip.payment_acquirer_payfip').write({'journal_id': tipiregie_journal.id})
        _logger.info("Delete new journal")
        env['account.journal'].search([('code', '=', 'PAYFI')]).unlink()
        _logger.info("Reset correct code for the old journal")
        tipiregie_journal.write({'code': 'PAYFI'})