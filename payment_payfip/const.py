SUPPORTED_CURRENCIES = [
    "EURO",
]


# Mapping of transaction states to payment status.
PAYMENT_STATUS_MAPPING = {
    "done": ["P", "V"],
    "cancel": ["A"],
    "reject": ["R", "Z"],
}
