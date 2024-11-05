{
    "name": "Intermédiaire de paiement PayFIP",
    "version": "16.0.0.1.1",
    "summary": """Intermédiaire de paiement : Implémentation de PayFIP""",
    "author": "Horanet & Yotech",
    "website": "https://www.yotech.pro/",
    "license": "AGPL-3",
    "category": "Accounting/Payment Providers",
    "depends": ["payment"],
    "data": [
        "templates/payment_payfip_template.xml",
        "views/payment_provider_views.xml",

        "data/ir_cron_data.xml",
        "data/mail_template_data.xml",
        "data/payment_provider_data.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "application": False,
    "auto_install": False,
    "installable": True,
}
