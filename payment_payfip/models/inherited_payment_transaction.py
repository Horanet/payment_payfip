from datetime import datetime, timedelta
import logging
import pytz
import uuid

from odoo import api, fields, models, _
from odoo.tools import float_round

from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class PayFIPTransaction(models.Model):
    # region Private attributes
    _inherit = 'payment.transaction'
    # endregion

    # region Default methods
    # endregion

    # region Fields declaration
    payfip_operation_identifier = fields.Char(
        string='Operation identifier',
        help='Reference of the request of TX as stored in the acquirer database',
    )

    payfip_return_url = fields.Char(
        string='Return URL',
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
        ]
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
    @api.model
    def create(self, vals):
        res = super(PayFIPTransaction, self).create(vals)
        if res.acquirer_id.provider == 'payfip':
            prec = self.env['decimal.precision'].precision_get('Product Price')
            email = res.partner_email
            amount = int(float_round(res.amount * 100.0, prec))
            reference = res.reference.replace('/', '  slash  ')
            acquirer_reference = '%.15d' % int(uuid.uuid4().int % 899999999999999)
            res.acquirer_reference = acquirer_reference
            idop = res.acquirer_id.payfip_get_id_op_from_web_service(email, amount, reference, acquirer_reference)
            res.payfip_operation_identifier = idop

        return res

    # endregion

    # region Actions
    def action_payfip_check_transaction(self):
        self.ensure_one()
        self._payfip_check_transactions()
    # endregion

    # region Model methods
    def _payfip_check_transactions(self):
        for rec in self.filtered('payfip_operation_identifier'):
            data = rec.acquirer_id.payfip_get_result_from_web_service(rec.payfip_operation_identifier)
            rec._payfip_evaluate_data(data)

    @api.model
    def _payfip_form_get_tx_from_data(self, idop):
        if not idop:
            error_msg = _('PayFIP: received data with missing idop!')
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # find tx -> @TDENOTE use txn_id ?
        txs = self.env['payment.transaction'].sudo().search([('payfip_operation_identifier', '=', idop)])
        if not txs or len(txs) > 1:
            error_msg = 'PayFIP: received data for idop %s' % idop
            if not txs:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return txs[0]

    @api.multi
    def _payfip_form_validate(self, idop):
        self.ensure_one()

        # If transaction is already done, we don't try to validate again.
        if self.state in ['done']:
            return True

        if not idop:
            error_msg = _('PayFIP: received data with missing idop!')
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        data = self.acquirer_id.payfip_get_result_from_web_service(idop)

        self._payfip_evaluate_data(data)

    @api.multi
    def _payfip_evaluate_data(self, data=False):
        if not data:
            return False

        self.ensure_one()

        result = data.get('resultrans', False)
        if not result:
            return False

        payfip_amount = int(data.get('montant', 0)) / 100

        if result in ['P', 'V']:
            message = 'Validated PayFIP payment for tx %s: set as done' % self.reference
            _logger.info(message)

            date_validate = fields.Datetime.now()
            payfip_date = str(data.get('dattrans', ''))
            payfip_datetime = str(data.get('heurtrans', ''))
            if payfip_date and payfip_datetime and len(payfip_date) == 8 and len(payfip_datetime) == 4:
                # Add a minute to validation datetime cause we don't get seconds from webservice and don't want to be
                # in trouble with creation datetime
                day = int(payfip_date[0:2])
                month = int(payfip_date[2:4])
                year = int(payfip_date[4:8])
                hour = int(payfip_datetime[0:2])
                minute = int(payfip_datetime[2:4])
                payfip_tz = pytz.timezone('Europe/Paris')
                td_minute = timedelta(minutes=1)
                date_validate = fields.Datetime.to_string(
                    datetime(year, month, day, hour=hour, minute=minute, tzinfo=payfip_tz) + td_minute
                )

            self.write({
                'state': 'done',
                'payfip_state': result,
                'date_validate': date_validate,
                'payfip_amount': payfip_amount,
            })
            return True
        elif result in ['A']:
            message = 'Received notification for PayFIP payment %s: set as canceled' % self.reference
            _logger.info(message)
            self.write({
                'state': 'cancel',
                'payfip_state': result,
                'payfip_amount': payfip_amount,
            })
            return True
        elif result in ['R', 'Z']:
            message = 'Received notification for PayFIP payment %s: set as error' % self.reference
            _logger.info(message)
            self.write({
                'state': 'error',
                'payfip_state': result,
                'state_message': message,
                'payfip_amount': payfip_amount,
            })
            return True
        else:
            message = 'Received unrecognized status for PayFIP payment %s: %s, set as error' % (
                self.reference,
                result
            )
            _logger.error(message)
            self.write({
                'state': 'error',
                'payfip_state': 'U',
                'state_message': message,
            })
            return False

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
        acquirer_model = self.env['payment.acquirer']

        payfip_acquirers = acquirer_model.search([
            ('provider', '=', 'payfip'),
        ])
        transactions = transaction_model.search([
            ('acquirer_id', 'in', payfip_acquirers.ids),
            ('state', 'in', ['draft', 'pending']),
            ('payfip_operation_identifier', '!=', False),
            ('payfip_operation_identifier', '!=', ''),
            ('create_date', '>=', fields.Datetime.to_string(date_from)),
        ])

        for tx in transactions:
            self.env['payment.transaction'].form_feedback(tx.payfip_operation_identifier, 'payfip')

        if send_summary:
            mail_template = self.env.ref('payment_payfip.mail_template_draft_payments_recovered')
            mail_template.with_context(transactions=transactions).send_mail(self.env.user.id)
    # endregion
