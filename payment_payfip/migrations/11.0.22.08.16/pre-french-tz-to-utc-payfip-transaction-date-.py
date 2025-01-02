import logging
import pytz

from openupgradelib import openupgrade

from odoo import fields

_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """Migrate Payfip transaction confirmation date to UTC date instead of french timezone."""
    # Payfip timezone
    payfip_tz = pytz.timezone('Europe/Paris')
    # Retreive all payfip transaction with a confirmation date
    payfip_transactions = env['payment.transaction'].search([
        ('acquirer_id.provider', '=', 'payfip'),
        ('date_validate', '!=', False),
    ])

    _logger.info(f"Number of Payfip transaction to migrate : {len(payfip_transactions)}")
    chunk_size = 100
    # Chunk transactions for processing
    payfip_transactions_chunked = [payfip_transactions[i:i + chunk_size] for i in range(0, len(payfip_transactions), chunk_size)]

    for idx, payfip_transaction_chunk in enumerate(payfip_transactions_chunked, start=1):
        _logger.info(f"Payfip transaction processing chunk : {idx}/{len(payfip_transactions_chunked)}")
        for payfip_transaction in payfip_transaction_chunk:
            # Validate date to datetime object
            date_validate = fields.Datetime.from_string(payfip_transaction.date_validate)
            # Localize datetime and transform into an UTC one
            utc_date_validate = payfip_tz.localize(date_validate).astimezone(pytz.UTC)
            # Set UTC value into datetime
            payfip_transaction.date_validate = fields.Datetime.to_string(utc_date_validate)
    _logger.info(f"Payfip transaction all chunks have been processed.")
