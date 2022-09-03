class LabelNotFoundError(Exception):
    def __init__(self, msg: str, *args, **kwargs) -> None:
        msg = f"The label: {msg} not found. Please refer to labelclient.labels for more information"
        super().__init__(msg, *args, **kwargs)


class LabelNotAvailableError(Exception):
    def __init__(self, msg: str, *args, **kwargs) -> None:
        msg = f"The label: {msg} is not able change. Please refer to labelclient.available_labels for more information"
        super().__init__(msg, *args, **kwargs)
