import logging
from openupgradelib import openupgrade

from odoo import api, SUPERUSER_ID

from odoo.addons.payment.models.payment_acquirer import create_missing_journal_for_acquirers

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Create new journal."""

    # Create journal for the new acquirer
    create_missing_journal_for_acquirers(cr, registry)

    # If migrate from old tipiregie acquirer
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Suppression des nouveaux objets créés depuis les data.xml pour restaurer les anciens
    old_payfip_aquirer = env.ref('payment_tipiregie_tmp.payment_acquirer_payfip', False)
    new_payfip_aquirer = env.ref('payment_payfip.payment_acquirer_payfip', False)
    old_payfip_aquirer_cron = env.ref('payment_tipiregie_tmp.cron_check_draft_payment_transactions', False)
    new_payfip_aquirer_cron = env.ref('payment_payfip.cron_check_draft_payment_transactions', False)

    if old_payfip_aquirer_cron or old_payfip_aquirer:
        if old_payfip_aquirer:
            new_payfip_aquirer.journal_id.unlink()
            new_payfip_aquirer.unlink()
            old_payfip_aquirer.provider = 'payfip'

        if old_payfip_aquirer_cron:
            new_payfip_aquirer_cron.unlink()
            old_payfip_aquirer_cron.write({
                'code': old_payfip_aquirer_cron.code.replace(
                    'tipiregie_cron_check_draft_payment_transactions',
                    'payfip_cron_check_draft_payment_transactions'),
                'name': "Cron to check PayFIP draft payment transactions",
            })

        openupgrade.rename_xmlids(cr, [
            ('payment_tipiregie_tmp.payment_acquirer_payfip',
             'payment_payfip.payment_acquirer_payfip'),
            ('payment_tipiregie_tmp.cron_check_draft_payment_transactions',
             'payment_payfip.cron_check_draft_payment_transactions'),
        ])

    # If old tipi journal exist we change the new journal for the old one
    default_payfip_journal = env['account.journal'].search([
        ('code', '=', 'PAYFI'),
        ('name', '=ilike', '__original_PayFIP')])
    if default_payfip_journal:
        default_payfip_journal.write({'name': 'PayFIP'})
