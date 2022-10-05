import time
from typing import List, Optional

from googleapiclient.discovery import Resource

from .client import GmailClient
from .message import Message


class Thread:
    """Thread ORM"""

    def __init__(
        self,
        raw_data: dict,
        client: Resource,
        message_client: Resource,
    ) -> None:
        self.raw_data = raw_data
        self.client = client
        self.message_client = message_client

    @property
    def id(self):
        return self.raw_data["id"]

    @property
    def messages(self) -> List[Message]:
        return [
            Message(message_data, self.message_client)
            for message_data in self.raw_data["messages"]
        ]

    def delete(self):
        self.client.delete(userId="me", id=self.id).execute()

    def modify(
        self,
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
    ):
        body = {}
        if add_label_ids:
            body["addLabelIds"] = add_label_ids
        if remove_label_ids:
            body["removeLabelIds"] = remove_label_ids
        self.client.modify(userId="me", id=self.id, body=body).execute()

    def trash(self) -> None:
        """Move this thread to trash."""
        self.client.trash(userId="me", id=self.id).execute()

    def untrash(self) -> None:
        """Untrash this thread."""
        self.client.untrash(userId="me", id=self.id).execute()


class ThreadClient(GmailClient):
    """Thread Client"""

    def __init__(self, client_secret: dict, refresh_token: str) -> None:
        super().__init__(client_secret, refresh_token)
        self.client = self.service.users().threads()
        self.message_client = self.service.users().messages()

    def delete(self, id: str):
        self.client.delete(userId="me", id=id).execute()

    def get(self, id: str) -> Thread:
        thread = self.client.get(userId="me", id=id).execute()
        return Thread(
            raw_data=thread,
            client=self.client,
            message_client=self.message_client,
        )

    def list(
        self,
        search_string: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        read: Optional[bool] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        include_spam_trash: bool = False,
        page_token: Optional[str] = None,
        exhausted: bool = False,
    ):
        """Create a query string from arguments and query all the results

        Each query has the max results. The default value is 100. To make the arguments simple,
        we do not change the maxResults parameter. Instead, we add a exhausted parameter to let
        user to decide if query to the end.

        Ref:
            https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list

        Arguments:
            search_string (str): The string user wants to query.
            before (str): Time format will be year/month/day Ex. 2022/1/31.
            after (str): Time format will be year/month/day Ex. 2022/12/1.
            read (bool): read or unread.
            from_ (str): The email sender.
            to (str): The email receiver.
            page_token (str): Used to get specific page.
            exhausted (bool): Search all or not.

        Returns:
            The formatted json result from google api. The key of jsons are messages and nextPageToken.

            messages (list[dict]): A list of dict. The element dict has two keys: 'id' and 'threadId'.
                Here the id is message id. Each message belongs to a certain thread, so there is also a threadId.
            nextPageToken: A token which is used to get next page data. If exhausted is True, this item will be empty string.

        """
        # Build the query string
        criteria_list = []
        if search_string is not None:
            criteria_list.append(search_string)
        if before is not None:
            criteria_list.append(f"before:{before}")
        if after is not None:
            criteria_list.append(f"after:{after}")
        if read is not None:
            criteria_list.append(f"is:{'read' if read else 'unread'}")
        if from_ is not None:
            criteria_list.append(f"from:{from_}")
        if to is not None:
            criteria_list.append(f"to:{to}")
        query_string = " ".join(criteria_list)

        if query_string:
            result = self.client.list(
                userId="me",
                q=query_string,
                pageToken=page_token,
                includeSpamTrash=include_spam_trash,
            ).execute()
        else:
            result = self.client.list(
                userId="me",
                pageToken=page_token,
                includeSpamTrash=include_spam_trash,
            ).execute()

        if not exhausted or (exhausted and not result.get("nextPageToken")):
            result.pop("resultSizeEstimate")
            return result

        total_result = result["threads"]
        while result.get("nextPageToken"):
            # max limit is 250 units per second
            time.sleep(1)
            result = self.client.list(
                userId="me",
                q=query_string,
                pageToken=result["nextPageToken"],
            ).execute()
            total_result.extend(result["threads"])
        return {"threads": total_result, "nextPageToken": ""}

    def modify(
        self,
        id: str,
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
    ) -> None:
        body = {}
        if add_label_ids:
            body["addLabelIds"] = add_label_ids
        if remove_label_ids:
            body["removeLabelIds"] = remove_label_ids
        self.client.modify(userId="me", id=id, body=body).execute()

    def trash(self, id: str) -> None:
        """Move thread to trash."""
        self.client.trash(userId="me", id=id).execute()

    def untrash(self, id: str) -> None:
        """Untrash thread."""
        self.client.untrash(userId="me", id=id).execute()
