from datetime import datetime, timedelta
import logging
import uuid

from odoo import _, api, exceptions, fields, models
from odoo.addons.payment_payfip.const import PAYMENT_STATUS_MAPPING
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class PayFIPTransaction(models.Model):
    # region Private attributes
    _inherit = 'payment.transaction'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    payfip_acquirer_reference = fields.Char(
        string="Acquirer identifier",
    )

    payfip_operation_identifier = fields.Char(
        string="Operation identifier",
        help="Reference of the request of TX as stored in the acquirer database",
    )

    payfip_return_url = fields.Char(
        string="Return URL",
    )

    payfip_sent_to_webservice = fields.Boolean(
        string="Sent to PayFIP webservice",
        default=False,
    )

    payfip_state = fields.Selection(
        string="PayFIP state",
        selection=[
            ('P', "Effective payment (P)"),
            ('V', "Effective payment (V)"),
            ('A', "Abandoned payment (A)"),
            ('R', "Other cases (R)"),
            ('Z', "Other cases (Z)"),
            ('U', "Unknown"),
        ],
    )

    payfip_amount = fields.Float(
        string="PayFIP amount",
    )

    # endregion

    # region Fields method
    # endregion

    # region Constrains and Onchange
    # endregion

    # region CRUD (overrides)
    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return payflip-specific rendering values.

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of provider-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'payfip':
            return res

        prec = self.env['decimal.precision'].precision_get('Product Price')
        email = self.partner_email
        amount = int(float_round(self.amount * 100.0, prec))
        reference = self.reference.replace('/', ' ')
        acquirer_reference = "%.15d" % int(uuid.uuid4().int % 899999999999999)
        self.payfip_acquirer_reference = acquirer_reference

        idop = self.provider_id.payfip_get_id_op_from_web_service(email, amount, reference, acquirer_reference)

        self.payfip_operation_identifier = idop

        res['api_url'] = 'https://www.payfip.gouv.fr/tpa/paiementws.web'
        if idop:
            res['idop'] = idop
        return res
    # endregion

    # region Actions
    def action_payfip_check_transaction(self):
        self.ensure_one()
        if self.payfip_operation_identifier:
            data = {'idop': self.payfip_operation_identifier}
            self.env['payment.transaction']._process_notification_data(data)

    # endregion

    # region Model methods
    @api.model
    def payfip_cron_check_draft_payment_transactions(self, options={}):
        """Execute cron task to get all draft payments and check actual state

        Execute cron task to get all draft payments before number of days passed as argument and ask for PayFIP
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

        transactions = transaction_model.search(
            [
                ('provider_code', '=', 'payfip'),
                ('state', 'in', ['draft', 'pending']),
                ('payfip_operation_identifier', '!=', False),
                ('payfip_operation_identifier', '!=', ''),
                ('create_date', '>=', fields.Datetime.to_string(date_from)),
            ]
        )

        for tx in transactions:
            data = {'idop': tx.payfip_operation_identifier}
            tx.env['payment.transaction']._process_notification_data(data)

        if send_summary:
            mail_template = self.env.ref('payment_payfip.mail_template_draft_payments_recovered')
            mail_template.with_context(transactions=transactions).send_mail(self.env.user.id)

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'payfip' or len(tx) == 1:
            return tx

        reference = notification_data.get('idop')
        if not reference:
            _msg = _("received data with missing idop!")
            _logger.error("PayFIP: " + _msg)
            raise exceptions.ValidationError("PayFIP: " + _msg)

        tx = self.search([('payfip_operation_identifier', '=', reference), ('provider_code', '=', 'payfip')])

        if not tx:
            raise exceptions.ValidationError("PayFIP: " + _("No transaction found matching idop %s.", reference))

        return tx

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(notification_data)

        if self.provider_code != 'payfip':
            return

        idop = notification_data['idop']
        data = self.provider_id.payfip_get_result_from_web_service(idop)
        payment_status = data.get('resultrans', False)

        if not payment_status:
            return False

        elif payment_status in PAYMENT_STATUS_MAPPING['done']:
            self._set_done()
        elif payment_status in PAYMENT_STATUS_MAPPING['cancel']:
            self._set_canceled()
        elif payment_status in PAYMENT_STATUS_MAPPING['reject']:
            self._set_error(self.provider_id.reject_msg)
        else:
            _logger.error("Received data with invalid payment status (%s) for transaction with reference %s.",
                          payment_status, self.reference)
            self._set_error("PayFIP: " + _("Unknown payment status: %s", payment_status))

    # endregion
