# -*- coding: utf-8 -*-

import logging
import uuid
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.tools import float_round

from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class TipiRegieTransaction(models.Model):
    # region Private attributes
    _inherit = 'payment.transaction'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    tipiregie_operation_identifier = fields.Char(
        string='Operation identifier',
        help='Reference of the request of TX as stored in the acquirer database'
    )

    tipiregie_return_url = fields.Char(
        string='Return URL',
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    # endregion

    # region Actions
    # endregion

    # region Model methods
    @api.model
    def _tipiregie_form_get_tx_from_data(self, idop):
        if not idop:
            error_msg = _('Tipi Regie: received data with missing idop!')
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        txs = self.env['payment.transaction'].sudo().search([('tipiregie_operation_identifier', '=', idop)])
        if not txs or len(txs) > 1:
            error_msg = 'Tipi Regie: received data for idop %s' % idop
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    @api.multi
    def _tipiregie_form_validate(self, idop):
        self.ensure_one()

        # If transaction is already done, we don't try to validate again.
        if self.state in ['done']:
            return True

        if not idop:
            error_msg = _('Tipi Regie: received data with missing idop!')
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        data = self.acquirer_id.tipiregie_get_result_from_web_service(idop)

        self._tipiregie_evaluate_data(data)

    @api.multi
    def _tipiregie_evaluate_data(self, data=False):
        if not data:
            return False

        self.ensure_one()

        result = data.get('resultrans', False)
        if not result:
            return False

        if result in ['P', 'V']:
            message = 'Validated Tipi Regie payment for tx %s: set as done' % self.reference
            _logger.info(message)
            self.write({
                'state': 'done',
                'date_validate': fields.Datetime.now()
            })
            return True
        elif result in ['A']:
            message = 'Received notification for Tipi Regie payment %s: set as canceled' % self.reference
            _logger.info(message)
            self.write({
                'state': 'cancel',
            })
            return True
        elif result in ['R', 'Z']:
            message = 'Received notification for Tipi Regie payment %s: set as error' % self.reference
            _logger.info(message)
            self.write({
                'state': 'error',
                'state_message': message,
            })
            return True
        else:
            message = 'Received unrecognized status for Tipi Regie payment %s: %s, set as error' % (
                self.reference,
                result
            )
            _logger.error(message)
            self.write({
                'state': 'error',
                'state_message': message,
            })
            return False

    @api.multi
    def tipiregie_generate_operation(self):
        prec = self.env['decimal.precision'].precision_get('Product Price')
        for tx in self:
            email = tx.partner_id.email
            price = int(float_round(tx.amount * 100.0, prec))
            object = tx.reference.replace('/', '  slash  ')
            acquirer_reference = tx.acquirer_reference or '%.15d' % int(uuid.uuid4().int % 899999999999999)
            idop = tx.acquirer_id.tipiregie_get_id_op_from_web_service(email, price, object, acquirer_reference)

            tx.write({
                'acquirer_reference': acquirer_reference,
                'tipiregie_operation_identifier': idop,
            })

        return

    @api.model
    def tipiregie_cron_check_draft_payment_transactions(self, options={}):
        """Execute cron task to get all draft payments and check actual state

        Execute cron task to get all draft payments before number of days passed as argument and ask for Tipi Régie
        web service to know actual state

        :param number_of_days: number of days (before today) to get draft transactions
        :type number_of_days: int
        """
        number_of_days = int(options.get('number_of_days', 1))
        send_summary = bool(options.get('send_summary', False))

        if number_of_days < 1:
            number_of_days = 1

        date_from = datetime.today() - timedelta(days=number_of_days)
        date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)
        transaction_model = self.env['payment.transaction']
        acquirer_model = self.env['payment.acquirer']

        tipiregie_acquirers = acquirer_model.search([
            ('provider', '=', 'tipiregie'),
        ])
        transactions = transaction_model.search([
            ('acquirer_id', 'in', tipiregie_acquirers.ids),
            ('state', 'in', ['draft', 'pending']),
            ('tipiregie_operation_identifier', '!=', False),
            ('tipiregie_operation_identifier', '!=', ''),
            ('create_date', '>=', fields.Datetime.to_string(date_from)),
        ])

        for tx in transactions:
            self.env['payment.transaction'].form_feedback(tx.tipiregie_operation_identifier, 'tipiregie')

        if send_summary:
            mail_template = self.env.ref('payment_tipiregie.mail_template_draft_payments_recovered')
            mail_template.with_context(transactions=transactions).send_mail(self.env.user.id)
    # endregion

    pass
