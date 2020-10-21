import logging

from openupgradelib import openupgrade

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate_tipiregie_to_payfip(cr):
    """Migration v10 -> v11."""
    if openupgrade.is_module_installed(cr, 'payment_tipiregie'):
        _logger.info("The payment_tipiregie addon is detected as installed. Rename it to payment_payfip.")

        # Rename addon from payment_tipiregie to payment_payfip.
        _logger.info("Rename addon from payment_tipiregie to payment_payfip.")
        openupgrade.update_module_names(cr, [('payment_tipiregie', 'payment_payfip')], merge_modules=True)
        _logger.info("End Renaming addon from payment_tipiregie to payment_payfip.")

        # Rename view xmlids
        xmlids_spec = [
            ('payment_payfip.acquirer_form_tipiregie', 'payment_payfip.acquirer_form_payfip'),
            ('payment_payfip.transaction_form_tipiregie', 'payment_payfip.transaction_form_payfip'),
            ('payment_payfip.tipiregie_form', 'payment_payfip.payfip_form'),
            # Mise à l'écart des données chargée depuis les data.xml afin de les restaurer en post
            ('payment_payfip.payment_acquirer_tipiregie',
             'payment_tipiregie_tmp.payment_acquirer_payfip'),
            ('payment_payfip.cron_check_draft_payment_transactions',
             'payment_tipiregie_tmp.cron_check_draft_payment_transactions'),
        ]
        openupgrade.rename_xmlids(cr, xmlids_spec)

        env = api.Environment(cr, SUPERUSER_ID, {})

        # Rename old accounting journal for avoid unique code error
        _logger.info("Rename old journal for create new one")

        default_payfip_journal = env['account.journal'].search([('code', '=', 'PAYFI'), ('name', '=ilike', 'PayFIP')])
        if default_payfip_journal:
            default_payfip_journal.write({'name': '__original_PayFIP'})

        field_spec = [
            # Rename acquirer fields
            ('payment.acquirer', 'payment_acquirer', 'tipiregie_customer_number', 'payfip_customer_number'),
            ('payment.acquirer', 'payment_acquirer', 'tipiregie_form_action_url', 'payfip_form_action_url'),
            ('payment.acquirer', 'payment_acquirer', 'tipiregie_activation_mode', 'payfip_activation_mode'),
            # Rename transaction fields
            ('payment.transaction', 'payment_transaction', 'tipiregie_operation_identifier',
             'payfip_operation_identifier'),
            ('payment.transaction', 'payment_transaction', 'tipiregie_return_url', 'payfip_return_url'),
            ('payment.transaction', 'payment_transaction', 'tipiregie_sent_to_webservice', 'payfip_sent_to_webservice'),
        ]

        _logger.info("Rename old field to new one")
        openupgrade.rename_fields(env, field_spec)
