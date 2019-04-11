# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID

import logging

_logger = logging.getLogger(__name__)
__name__ = 'Update operation identifier'


def migrate(cr, version):
    """Update operation identifier."""
    if not version:
        return

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        PaymentAcquirerModel = env['payment.acquirer']
        PaymentTransactionModel = env['payment.transaction']

        tipiregie_acquirers = PaymentAcquirerModel.search([('provider', '=', 'tipiregie')])
        txs = PaymentTransactionModel.search([('acquirer_id', 'in', tipiregie_acquirers.ids)])

        limit = 100
        if len(txs) > 100000:
            limit = 10000
        elif len(txs) > 10000:
            limit = 1000

        offset = 0

        _logger.info("Migration catched {} records to compute and will iterate by group of {}.".format(len(txs), limit))

        while offset < len(txs):
            txs_block = txs[offset:offset + limit]

            for tx in txs_block:
                if tx.acquirer_reference and len(tx.acquirer_reference) != 15:
                    tx.write({
                        'tipiregie_operation_identifier': tx.acquirer_reference,
                        'acquirer_reference': ''
                    })

                if tx.acquirer_id.tipiregie_customer_number != 'dummy' \
                        and tx.tipiregie_operation_identifier \
                        and not tx.acquirer_reference:
                    try:
                        data = tx.acquirer_id.tipiregie_get_result_from_web_service(tx.tipiregie_operation_identifier)
                    except:
                        data = {}

                    if 'refdet' in data:
                        tx.write({'acquirer_reference': data.get('refdet', '')})

            offset += limit
            _logger.info("{}/{} records computed".format(len(txs) if offset > len(txs) else offset, len(txs)))

