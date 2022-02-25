import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """Reduce interval of already existing cron (which are in no update mode)."""
    if not version:
        return

    cron = env.ref('payment_payfip.cron_check_draft_payment_transactions', raise_if_not_found=False)
    if cron and cron.interval_number == 1 and cron.interval_type == 'days':
        cron.write({
            'interval_number': 5,
            'interval_type': 'minutes',
        })
        _logger.info("Reduce the cron_check_draft_payment_transactions interval from every day to every 5 minutes")
