from enum import Enum
from typing import List

from .client import GmailClient
from .exceptions import LabelNotAvailableError


class LabelListVisibility(Enum):
    """Label list visibility

    Show in web ui or not. If not, the label will hide in drop down menu.

    labelShow	Show the label in the label list.
    labelShowIfUnread	Show the label if there are any unread messages with that label.
    labelHide	Do not show the label in the label list.

    """

    LABELSHOW = "labelShow"
    LABELSHOWIFUNREAD = "labelShowIfUnread"
    LABELHIDE = "labelHide"


class LabelClient(GmailClient):
    def __init__(self, client_secret: dict, refresh_token: str) -> None:
        super().__init__(client_secret, refresh_token)
        self.client = self.service.users().labels()

    @property
    def labels(self):
        """List all labels"""
        return [label["name"] for label in self.list()]

    @property
    def available_labels(self) -> List[dict]:
        """List all the labels which are available to change"""
        return [label["name"] for label in self.list() if label["type"] == "user"]

    def create(self):
        """Creates a new label."""

    def delete(self, id):
        """Delete label

        Immediately and permanently deletes the specified label and removes it
        from any messages and threads that it is applied to.
        """
        self.client.delete(userId="me", id=id).execute()

    def get(self, id: str) -> dict:
        """Gets the specified label."""
        return self.client.get(userId="me", id=id).execute()

    def list(self) -> dict:
        """Lists all labels in the user's mailbox."""
        return self.client.list(userId="me").execute()

    def patch(self, id: str, body: dict):
        """Patch the specified label.

        This method can update part of the label.
        https://stackoverflow.com/questions/65524339/what-does-gmails-method-users-labels-patch-allow-you-to-do-and-how-is-that-di
        """
        if id not in self.available_labels:
            raise LabelNotAvailableError(id)
        return self.client.patch(userId="me", id=id, body=body).execute()

    def update(self, id: str, body: dict):
        """Updates the specified label."""
        if id not in self.available_labels:
            raise LabelNotAvailableError(id)
        return self.client.update(userId="me", id=id, body=body).execute()
