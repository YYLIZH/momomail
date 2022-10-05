from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, validator

from .client import GmailClient
from .exceptions import LabelNotAvailableError


class LabelListVisibility(str, Enum):
    """Label list visibility

    Show in web ui or not. If not, the label will hide in drop down menu.

    labelShow	Show the label in the label list.
    labelShowIfUnread	Show the label if there are any unread messages with that label.
    labelHide	Do not show the label in the label list.

    """

    LABELSHOW = "labelShow"
    LABELSHOWIFUNREAD = "labelShowIfUnread"
    LABELHIDE = "labelHide"


class MessageListVisibility(str, Enum):
    """Message list visibility

    Show the label in the message list.

    show	Show the label in the message list.
    hide	Do not show the label in the message list.
    """

    SHOW = "show"
    HIDE = "hide"


class Type(str, Enum):
    """Type of label"""

    SYSTEM = "system"
    USER = "user"


class Color(BaseModel):
    textColor: str
    backgroundColor: str

    @validator("*")
    def validate_color(cls, v):
        if v not in [
            "#000000",
            "#434343",
            "#666666",
            "#999999",
            "#cccccc",
            "#efefef",
            "#f3f3f3",
            "#ffffff",
            "#fb4c2f",
            "#ffad47",
            "#fad165",
            "#16a766",
            "#43d692",
            "#4a86e8",
            "#a479e2",
            "#f691b3",
            "#f6c5be",
            "#ffe6c7",
            "#fef1d1",
            "#b9e4d0",
            "#c6f3de",
            "#c9daf8",
            "#e4d7f5",
            "#fcdee8",
            "#efa093",
            "#ffd6a2",
            "#fce8b3",
            "#89d3b2",
            "#a0eac9",
            "#a4c2f4",
            "#d0bcf1",
            "#fbc8d9",
            "#e66550",
            "#ffbc6b",
            "#fcda83",
            "#44b984",
            "#68dfa9",
            "#6d9eeb",
            "#b694e8",
            "#f7a7c0",
            "#cc3a21",
            "#eaa041",
            "#f2c960",
            "#149e60",
            "#3dc789",
            "#3c78d8",
            "#8e63ce",
            "#e07798",
            "#ac2b16",
            "#cf8933",
            "#d5ae49",
            "#0b804b",
            "#2a9c68",
            "#285bac",
            "#653e9b",
            "#b65775",
            "#822111",
            "#a46a21",
            "#aa8831",
            "#076239",
            "#1a764d",
            "#1c4587",
            "#41236d",
            "#83334c",
            "#464646",
            "#e7e7e7",
            "#0d3472",
            "#b6cff5",
            "#0d3b44",
            "#98d7e4",
            "#3d188e",
            "#e3d7ff",
            "#711a36",
            "#fbd3e0",
            "#8a1c0a",
            "#f2b2a8",
            "#7a2e0b",
            "#ffc8af",
            "#7a4706",
            "#ffdeb5",
            "#594c05",
            "#fbe983",
            "#684e07",
            "#fdedc1",
            "#0b4f30",
            "#b3efd3",
            "#04502e",
            "#a2dcc1",
            "#c2c2c2",
            "#4986e7",
            "#2da2bb",
            "#b99aff",
            "#994a64",
            "#f691b2",
            "#ff7537",
            "#ffad46",
            "#662e37",
            "#ebdbde",
            "#cca6ac",
            "#094228",
            "#42d692",
            "#16a765",
        ]:
            raise ValueError(f"The color: {v} is not allowed.")
        return v


class LabelBase(BaseModel):
    name: str
    messageListVisibility: Optional[MessageListVisibility] = MessageListVisibility.SHOW
    labelListVisibility: Optional[LabelListVisibility] = LabelListVisibility.LABELSHOW
    color: Optional[Color]

    class Config:
        use_enum_values = True

    @validator("messageListVisibility", pre=True, always=True)
    def set_messageListVisibility(cls, v):
        return v or MessageListVisibility.SHOW

    @validator("labelListVisibility", pre=True, always=True)
    def set_labelListVisibility(cls, v):
        return v or LabelListVisibility.LABELSHOW

    @validator("color", pre=True, always=True)
    def set_color(cls, v: dict):
        if not isinstance(v, dict):
            v = {}
        text_color = v.get("textColor") or "#000000"
        background_color = v.get("backgroundColor") or "#fcdee8"
        return Color(**{"textColor": text_color, "backgroundColor": background_color})


class LabelInput(LabelBase):
    pass


class LabelOutput(LabelBase):
    id: str
    type: Type = Type.USER
    messagesTotal: int
    messagesUnread: int
    threadsTotal: int
    threadsUnread: int


class LabelClient(GmailClient):
    def __init__(self, client_secret: dict, refresh_token: str) -> None:
        super().__init__(client_secret, refresh_token)
        self.client = self.service.users().labels()

    @property
    def labels(self):
        """List all labels"""
        return [label["name"] for label in self.list()]

    @property
    def available_label_ids(self) -> List[dict]:
        """List all the labels which are available to change"""
        return [label["id"] for label in self.list() if label["type"] == "user"]

    def create(
        self,
        name: str,
        messageListVisibility: Optional[str] = None,
        labelListVisibility: Optional[str] = None,
        color: Optional[dict] = None,
    ):
        """Creates a new label."""
        data = LabelInput(
            name=name,
            messageListVisibility=messageListVisibility,
            labelListVisibility=labelListVisibility,
            color=color,
        )
        self.client.create(userId="me", body=data.dict()).execute()

    def delete(self, id):
        """Delete label

        Immediately and permanently deletes the specified label and removes it
        from any messages and threads that it is applied to.
        """
        self.client.delete(userId="me", id=id).execute()

    def get(self, id: str) -> dict:
        """Gets the specified label."""
        return self.client.get(userId="me", id=id).execute()

    def list(self) -> List[dict]:
        """Lists all labels in the user's mailbox."""
        return self.client.list(userId="me").execute()["labels"]

    def patch(self, id: str, body: dict):
        """Patch the specified label.

        This method can update part of the label.
        https://stackoverflow.com/questions/65524339/what-does-gmails-method-users-labels-patch-allow-you-to-do-and-how-is-that-di
        """
        if id not in self.available_label_ids:
            raise LabelNotAvailableError(id)
        return self.client.patch(userId="me", id=id, body=body).execute()

    def update(self, id: str, body: dict):
        """Updates the specified label."""
        if id not in self.available_label_ids:
            raise LabelNotAvailableError(id)
        return self.client.update(userId="me", id=id, body=body).execute()
