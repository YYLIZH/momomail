import copy
import re
import time
from base64 import urlsafe_b64decode
from pathlib import Path
from typing import Dict, List, Optional

from googleapiclient.discovery import Resource
from .client import GmailClient


class Message:
    """Message ORM

    We see the whole gmail api as a database. This class plays as an
    ORM. Properties are the data in this model, methods allow ORM to
    control the gmail api.

    """

    def __init__(self, raw_data: dict, client: Resource) -> None:
        self.raw_data = raw_data
        self.client = client

    def __str__(self) -> str:
        return self.subject

    @property
    def id(self) -> str:
        return self.raw_data["id"]

    @property
    def thread_id(self) -> str:
        return self.raw_data["threadId"]

    @property
    def label_ids(self) -> List[str]:
        return self.raw_data["labelIds"]

    @property
    def subject(self) -> str:
        for header in self.raw_data["payload"]["headers"]:
            if header["name"] == "Subject":
                return str(header["value"])
        return ""

    @property
    def date(self) -> str:
        for header in self.raw_data["payload"]["headers"]:
            if header["name"] == "Date":
                return str(header["value"])
        return ""

    def _format_date(self, date_string: str) -> str:
        """Format date string"""
        month = {
            "Jan": "1",
            "Feb": "2",
            "Mar": "3",
            "Apr": "4",
            "May": "5",
            "Jun": "6",
            "Jul": "7",
            "Aug": "8",
            "Sep": "9",
            "Oct": "10",
            "Nov": "11",
            "Dec": "12",
        }
        mrx = re.search(r"(\d+)\s+(\w+)\s+(\d+)", date_string)
        if mrx:
            return "-".join([mrx.group(3), month[mrx.group(2)], mrx.group(1)])
        return "NA"

    @property
    def from_(self) -> Optional[str]:
        for header in self.raw_data["payload"]["headers"]:
            if header["name"] == "From":
                return str(header["value"])
        return ""

    @property
    def to(self) -> str:
        for header in self.raw_data["payload"]["headers"]:
            if header["name"] == "To":
                return str(header["value"])
        return ""

    @property
    def body(self) -> str:
        body_data = self.raw_data["payload"]["body"].get("data")
        if body_data:
            return urlsafe_b64decode(body_data).decode()
        return ""

    @property
    def parts(self) -> List[Dict[str, str]]:
        # parts could be nested, use DFS to recursively parse out data
        # DFS can keep the order
        result = []

        def dfs(parts: list, result):
            for part in parts:
                if part.get("parts"):
                    dfs(part.get("parts"), result)
                else:
                    result.append(self._parse_part(part))

        dfs(copy.deepcopy(self.raw_data["payload"]["parts"]), result)

        return result

    def delete(self) -> None:
        """Delete message from mail box.

        Dangerous, suggest to use trash instead.
        """
        self.client.delete(userId="me", id=self.id).execute()

    def modify(
        self,
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
    ) -> None:
        body = {}
        if add_label_ids:
            body["addLabelIds"] = add_label_ids
        if remove_label_ids:
            body["removeLabelIds"] = remove_label_ids
        self.client.modify(userId="me", id=self.id, body=body).execute()

    def trash(self) -> None:
        """Move this message to trash."""
        self.client.trash(userId="me", id=self.id).execute()

    def untrash(self) -> None:
        """Untrash this message."""
        self.client.untrash(userId="me", id=self.id).execute()

    def dump(self) -> None:
        """Dump the mail content"""
        mail_dir = Path(f"{self.subject}-{self._format_date(self.date)}")
        mail_dir.mkdir()
        if self.body:
            with open(mail_dir / "body.txt", "w") as f:
                f.write(self.body)
        for part in self.parts:
            # attachment need to use byte format to write
            buffer_format = "wb" if part["type"] == "attachment" else "w"
            with open(mail_dir / part["filename"], buffer_format) as f:
                f.write(part["data"])

    def get_attachment(self, attachment_id: str) -> bytes:
        """Get attachment"""
        data = (
            self.client.attachments()
            .get(id=attachment_id, userId="me", messageId=self.id)
            .execute()
            .get("data")
        )
        return urlsafe_b64decode(data)

    def _parse_part(self, part: dict) -> Optional[dict]:
        if part.get("mimeType") == "text/plain":
            filename = part.get("filename", "") or "sample.txt"
            data = part.get("body", {}).get("data", "")
            if data:
                data = urlsafe_b64decode(data).decode()
                return {
                    "filename": filename,
                    "type": "text/plain",
                    "data": data,
                }

        elif part.get("mimeType") == "text/html":
            filename = part.get("filename", "") or "sample.html"
            data = part.get("body", {}).get("data", "")
            if data:
                data = urlsafe_b64decode(data).decode()
                return {
                    "filename": filename,
                    "type": "text/html",
                    "data": data,
                }
        else:
            if part.get("body", {}).get("attachmentId"):
                data = self.get_attachment(part["body"]["attachmentId"])
                filename = part.get("filename", "") or "sample"
                return {
                    "filename": filename,
                    "type": "attachment",
                    "data": data,
                }


class MessageClient(GmailClient):
    def __init__(self, client_secret: dict, refresh_token: str) -> None:
        super().__init__(client_secret, refresh_token)
        self.client = self.service.users().messages()

    def delete(self, id: str) -> None:
        """Delete message from mail box.

        Dangerous, suggest to use trash instead.
        """
        self.client.delete(userId="me", id=id).execute()

    def get(self, id: str) -> Message:
        """Get message message by its id"""
        message: dict = self.client.get(userId="me", id=id).execute()
        return Message(raw_data=message, client=self.client)

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
                userId="me", pageToken=page_token, includeSpamTrash=include_spam_trash
            ).execute()

        if not exhausted or (exhausted and not result.get("nextPageToken")):
            result.pop("resultSizeEstimate")
            return result

        total_result = result["messages"]
        while result.get("nextPageToken"):
            # max limit is 250 units per second
            time.sleep(1)
            result = self.client.list(
                userId="me",
                q=query_string,
                pageToken=result["nextPageToken"],
            ).execute()
            total_result.extend(result["messages"])
        return {"messages": total_result, "nextPageToken": ""}

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

    def send(self):
        pass

    def trash(self, id: str) -> None:
        """Move message to trash."""
        self.client.trash(userId="me", id=id).execute()

    def untrash(self, id: str) -> None:
        """Untrash message."""
        self.client.untrash(userId="me", id=id).execute()

    def batch_modify(
        self,
        ids: List[str],
        add_label_ids: Optional[List[str]] = None,
        remove_label_ids: Optional[List[str]] = None,
    ) -> None:
        body = {"ids": ids}
        if add_label_ids:
            body["addLabelIds"] = add_label_ids
        if remove_label_ids:
            body["removeLabelIds"] = remove_label_ids
        self.client.batchModify(userId="me", body=body).execute()

    def batch_trash(self, ids: List[str]) -> None:
        """Batch move messages into trash can"""
        self.batch_modify(ids=ids, add_label_ids=["TRASH"])

    def batch_untrash(self, ids: List[str]) -> None:
        """Batch move messages out of trash can"""
        self.batch_modify(ids=ids, remove_label_ids=["TRASH"])

    def batch_delete(self, ids: List[str]) -> None:
        """Batch delete messages

        Should be very careful since this method will completely delete the messages.
        You can use batch_trash instead to put messages into trash can.

        """
        self.client.batchDelete(userId="me", body={"ids": ids}).execute()
