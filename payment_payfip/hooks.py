from odoo.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(cr, registry):
    setup_provider(cr, registry, 'payfip')


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, 'payfip')
