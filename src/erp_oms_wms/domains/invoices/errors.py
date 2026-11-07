class InvoiceError(Exception):
    pass


class InvoiceNotFoundError(InvoiceError):
    pass


class InvalidInvoiceTransitionError(InvoiceError):
    pass
