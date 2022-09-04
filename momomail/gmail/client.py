import json
import os
from functools import lru_cache

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Can find the applicable api scope in the https://developers.google.com/identity/protocols/oauth2/scopes#gmail
# Note: Please generate new refresh token if intending to use different scope
SCOPES = ["https://mail.google.com/"]


@lru_cache
def get_client_secret() -> dict:
    """Read client secret data"""
    if os.path.isfile("client_secret.json"):
        with open("client_secret.json", "r", encoding="utf8") as file:
            return json.load(file)
    raise FileNotFoundError(
        "client_secret.json should be in current working directory."
    )


def get_refresh_token() -> None:
    """Get refresh token for GmailClient"""
    flow = InstalledAppFlow.from_client_config(
        get_client_secret(), scopes=SCOPES
    )
    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    auth_url, _ = flow.authorization_url()
    print(auth_url)
    code = input("Please enter the code:")
    flow.fetch_token(code=code)
    with open("refresh_token.json", "w") as f:
        json.dump(
            {"refresh_token": flow.credentials.refresh_token}, f
        )


class GmailClient:
    def __init__(
        self, client_secret: dict, refresh_token: str
    ) -> None:
        # Try to get refresh token
        if not os.path.isfile("refresh_token.json"):
            get_refresh_token()
        with open("refresh_token.json", "r") as f:
            refresh_token = json.load(f)["refresh_token"]

        credentials = Credentials(
            None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_secret["installed"]["client_id"],
            client_secret=client_secret["installed"]["client_secret"],
            scopes=SCOPES,
        )
        self.service = build("gmail", "v1", credentials=credentials)

    @classmethod
    def setup(cls):
        """Offers another way to initialize this client."""
        # Try to get refresh token
        if not os.path.isfile("refresh_token.json"):
            get_refresh_token()
        with open("refresh_token.json", "r") as f:
            refresh_token = json.load(f)["refresh_token"]
        return cls(
            client_secret=get_client_secret(),
            refresh_token=refresh_token,
        )
