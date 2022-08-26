from __future__ import print_function

import json
from functools import lru_cache
from optparse import Option
from pathlib import Path
from typing import List, Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from pygmail.mail import Mail

# Can find the applicable api scope in the https://developers.google.com/identity/protocols/oauth2/scopes#gmail
SCOPES = ["https://mail.google.com/"]
REFRESH_TOKEN = "1//0e6i8vlTqvnAeCgYIARAAGA4SNwF-L9IrZswvCXMKTvqHkoyM6AW_sruCFr24cN4_lxCykX4_xl4_20KyuwbLIy3k4yR90ybCgzo"


@lru_cache
def get_client_config() -> dict:
    # from google-console -> apis -> credentials
    with open(Path(__file__).parent / "client_config.json") as file:
        return json.load(file)


def get_auth_url(client_config: dict = get_client_config()) -> str:
    """
    :param scopes: The types of scopes can be found from https://developers.google.com/drive/api/v2/about-auth.
    Return: auth url
    By Clicking the auth url, one can get a code which can be used for generating refresh token.
    """
    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    auth_url, _ = flow.authorization_url()
    return auth_url


def get_refresh_token(
    code: str, scopes: List[str], client_config: dict = get_client_config()
) -> str:
    """
    :param code: Code from get_auth_url
    :param scopes: Scopes should be as same as that used in get_auth_url
    # NOTE: Remember to get new refresh token while intending to use different scopes
    """
    flow = InstalledAppFlow.from_client_config(client_config, scopes)
    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    flow.fetch_token(code=code)
    return flow.credentials.refresh_token


class GmailClient:
    def __init__(self) -> None:
        credentials = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=get_client_config()["installed"]["client_id"],
            client_secret=get_client_config()["installed"]["client_secret"],
            scopes=SCOPES,
        )
        self.service = build("gmail", "v1", credentials=credentials)

    def search_message(
        self,
        search_string: str,
        before: Optional[str] = None,
        after: Optional[str] = None,
        read: Optional[bool] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
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

        Return:
            The formatted json result from google api. The key of jsons are messages and nextPageToken.

            messages (list[dict]): A list of dict. The element dict has two keys: 'id' and 'threadId'.
                Here the id is message id. Each message belongs to a certain thread, so there is also a threadId.
            nextPageToken: A token which is used to get next page data. If exhausted is True, this item will be empty string.

        """

        criteria_list = [search_string]
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
        result = (
            self.service.users()
            .messages()
            .list(userId="me", q=query_string, page_token=page_token)
        )
        if not exhausted:
            result.pop("resultSizeEstimate")
            return result
        total_result = result["messages"]
        while result["nextPageToken"]:
            result = (
                self.service.users()
                .messages()
                .list(userId="me", q=query_string, page_token=result["nextPageToken"])
            )
            total_result.extend(result["messages"])
        return {"messages": total_result, "nextPageToken": ""}

    def get_message(self, id: str) -> Mail:
        message: dict = (
            self.service.users().messages().get(userId="me", id=id).execute()
        )
        message["message_client"] = self.service.users().messages()
        return Mail(**message)

    def batch_delete_messages(self, ids: List[str]) -> None:
        self.service.users().message().get(userId="me", ids=ids).execute()
