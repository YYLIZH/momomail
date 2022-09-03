class LabelNotFoundError(Exception):
    def __init__(self, msg: str, *args, **kwargs) -> None:
        msg = f"The label: {msg} not found. Please refer to user_client.available_label for more information"
        super().__init__(msg, *args, **kwargs)
