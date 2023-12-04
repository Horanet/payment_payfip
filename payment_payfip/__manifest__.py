{
    'name': "Intermédiaire de paiement PayFIP",
    'version': '11.0.22.02.25',
    'summary': """Intermédiaire de paiement : Implémentation de PayFIP""",
    'author': "Horanet",
    'website': "http://www.horanet.com/",
    'license': "AGPL-3",
    'category': 'Accounting',
    'external_dependencies': {
        'python': [
            'openupgradelib',
        ]
    },
    'depends': [
        'payment'
    ],
    'qweb': [],
    'init_xml': [],
    'update_xml': [],
    'data': [
        # Views must be before data to avoid loading issues
        'views/payment_payfip_templates.xml',
        'views/payment_views.xml',

        'data/payment_acquirer.xml',
        'data/draft_payments_recovered_mail.xml',
        'data/cron_check_drafts.xml',
    ],
    'demo': [
    ],
    'application': False,
    'auto_install': False,
    'installable': True,
}
