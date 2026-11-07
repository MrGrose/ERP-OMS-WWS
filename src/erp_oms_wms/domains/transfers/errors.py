class TransferError(Exception):
    pass


class TransferNotFoundError(TransferError):
    def __init__(self, transfer_id: str) -> None:
        super().__init__(f"warehouse transfer not found: {transfer_id}")


class InvalidTransferTransitionError(TransferError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
