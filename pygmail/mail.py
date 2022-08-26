import base64
from typing import List, Optional, Any
from googleapiclient.discovery import Resource
from pydantic import BaseModel, root_validator, validator

# reference site: https://www.thepythoncode.com/article/use-gmail-api-in-python


class Body(BaseModel):
    size: int
    data: Optional[str]

    @validator("data")
    def decode_body(cls, value):
        missing_padding = len(value) % 4
        if missing_padding != 0:
            value = value + "=" * (4 - missing_padding)
        return base64.urlsafe_b64decode(value).decode()


class Part(BaseModel):
    filename: str
    body: Body


class Mail(BaseModel):
    id: str
    threadId: str
    labelIds: List[str]
    Date: str
    From: str
    To: str
    Subject: str
    filename: str
    body: Body
    parts: List[Part]
    payload: dict
    """Mail ORM"""

    @root_validator(pre=True)
    def parse_payload(cls, values):
        payload = values["payload"]
        extract_items = ["Date", "From", "To", "Subject"]
        values["filename"] = payload["filename"]
        values["body"] = Body(**payload["body"])
        for header in payload["headers"]:
            for item in extract_items:
                if header["name"] == item:
                    values[item] = header["value"]
        values["parts"] = payload["parts"]
        return values

    def __init__(self, **data: Any) -> None:
        self.message_client: Resource = data.pop("message_client")
        super().__init__(**data)

    def get(self) -> dict:
        """Get raw data"""
        return self.message_client.get(userId="me", id=self.id).execute()

    def delete(self) -> None:
        """Delete message from mail box.

        Dangerous, suggest to use trash instead.
        """
        self.message_client.delete(userId="me", id=self.id).execute()

    def trash(self) -> None:
        """Move this message to trash."""
        self.message_client.trash(userId="me", id=self.id).execute()

    def untrash(self) -> None:
        """Untrash this message."""
        self.message_client.untrash(userId="me", id=self.id).execute()
