import logging

from openupgradelib import openupgrade

__name__ = 'V11 Migration'
_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Rename fields from tipiregie_* to payfip_*."""
    if not version:
        return

    if openupgrade.is_module_installed(env.cr, 'payment_tipiregie'):
        _logger.info("The payment_tipiregie addon is detected as installed. Rename it to payment_payfip.")

        # Rename addon from payment_tipiregie to payment_payfip.
        _logger.info("Rename addon from payment_tipiregie to payment_payfip.")
        namespec = [('payment_tipiregie', 'payment_payfip')]
        openupgrade.update_module_names(env.cr, namespec)

        # _logger.info("Rename fields from tipiregie_* to payfip_*")
        # # Rename fields
        # field_spec = [
        #     ('payment.acquirer', 'payment_acquirer', 'tipiregie_customer_number', 'payfip_customer_number'),
        #     ('payment.acquirer', 'payment_acquirer', 'tipiregie_form_action_url', 'payfip_form_action_url'),
        #     ('payment.acquirer', 'payment_acquirer', 'tipiregie_activation_mode', 'payfip_activation_mode'),
        #     ('payment.transaction', 'payment_transaction', 'tipiregie_operation_identifier',
        #      'payfip_operation_identifier'),
        #     ('payment.transaction', 'payment_transaction', 'tipiregie_return_url', 'payfip_return_url'),
        #     ('payment.transaction', 'payment_transaction', 'tipiregie_sent_to_webservice', 'payfip_sent_to_webservice'),
        # ]
        # openupgrade.rename_fields(env, field_spec)