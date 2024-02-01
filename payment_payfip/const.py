SUPPORTED_CURRENCIES = [
    "EURO",
]


# Mapping of transaction states to payment status.
PAYMENT_STATUS_MAPPING = {
    # "authorized": ["authorize"],
    # "pending": ["pending"],
    "done": ["P", "V"],
    "cancel": ["A"],
    "reject": ["R", "Z"],
}
