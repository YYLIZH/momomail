# Momomail
Momomail is a gmail api wrapper. This package aims to provide a more straight forward way to control gmail. 

## Install
```bash
pip install git+https://github.com/YYLIZH/momomail.git
```

## Generate a client_secret.json file
This project uses Oauth to authenticate google api. You can go to google api page to apply an Oauth ID then download it. The content would be like below
```json
{
    "installed": {
        "client_id": "xxxxxx.apps.googleusercontent.com",
        "project_id": "xxxxxx",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "xxxxxx",
        "redirect_uris": [
            "http://localhost"
        ]
    }
}
```

## GmailClient
We use a GmailClient to control the gmail api. There are two ways to initialize the gmail client.

### If you don't know the refresh token of gmail api
Download the Oauth ID json file, rename it to `client_secret.json` and **put it in the current directory**
```python
from momomail.gmail.client import GmailClient

client=GmailClient.setup()
```
The prgram will first check if there is a `refresh_token.json` file in the **current working directory**. If not, the program will enter the authenticate process. There will be a url for user to click to authenticate this api. Copy and paste the code to terminal to authenticate and generate a `refresh_token.json` in the current working directory.
### If you have data of client secret and refresh token
```python
from momomail.gmail.client import GmailClient

client=GmailClient(client_secret,refresh_token)
```

## MessageClient
Message Client deal with batch action on messages, the available methods are listed below:

- **search messages**: <br>
search_message support arguments inputs like gmail web ui: search string, before, after, read or unread, from, to
    ```python
    messages=client.message_client.search_messages("twitter")
    ```
- **get message**: <br>
get_message is used to get detail of a message. The return object is a **Message** object.
    ```python
    message:Message=client.message_client.get_message(id="message_id")
    ```

- **batch modify**: <br>
batch_modify modify messages' labels
    ```python
    client.message_client.batch_modify(ids=["aaa","bbb"],add_label_ids["TEST"],remove_label_ids["SPAM"])
    ```

Gmail moves messages into trash can by adding a "TRASH" label. Thus, message client uses this property to make batch trash and batch untrash method.  

- **batch trash**: <br>
Move messages to trash can 
    ```python
    client.message_client.batch_trash(ids=["aaa","bbb"])
    ```

- **batch untrash**: <br>
Move messages out of trash can 
    ```python
    client.message_client.batch_untrash(ids=["aaa","bbb"])
    ```


### Message
Message is an ORM model. It offer several properties and methods same as gmail api doc.

properties: id, thread_id, label_ids, subject, date, from_, to, body, parts

methods: delete, trash, untrash

## Frequently asked quentions
1. Why my refresh token expired after 7 days?

    In google's refresh token policy, if the app in google is a test app, the refresh token expired after 7 days. You need to publish your app to get a long-lived refresh token.

## Contributing 
This is an immature project. PRs are welcome. Feel free to ask any questions or offer suggestions