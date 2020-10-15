import logging

from openupgradelib import openupgrade

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate_tipiregie_to_payfip(cr):
    """Migration v10 -> v11."""
    if openupgrade.is_module_installed(cr, 'payment_tipiregie'):
        _logger.info("The payment_tipiregie addon is detected as installed. Rename it to payment_payfip.")

        # Rename view xmlids
        xmlids_spec = [
            ('payment_tipiregie.acquirer_form_tipiregie', 'payment_payfip.acquirer_form_payfip'),
            ('payment_tipiregie.transaction_form_tipiregie', 'payment_payfip.transaction_form_payfip'),
            ('payment_tipiregie.tipiregie_form', 'payment_payfip.payfip_form'),
            ('payment_tipiregie.payment_acquirer_tipiregie', 'payment_payfip.payment_acquirer_payfip'),
        ]
        openupgrade.rename_xmlids(cr, xmlids_spec)

        # Rename addon from payment_tipiregie to payment_payfip.
        _logger.info("Rename addon from payment_tipiregie to payment_payfip.")
        openupgrade.update_module_names(cr, [('payment_tipiregie', 'payment_payfip')], merge_modules=True)
        _logger.info("End Renaming addon from payment_tipiregie to payment_payfip.")

        env = api.Environment(cr, SUPERUSER_ID, {})

        # Rename old accounting journal for avoid unique code error
        _logger.info("Rename old journal for create new one")
        env['account.journal'].search([('code', '=', 'PAYFI')]).write({'code': 'TIPIR'})

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
