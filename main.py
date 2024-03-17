from momomail.gmail import message
from momomail.gmail.client import GmailClient
from momomail.gmail.message import MessageClient

# ref: https://www.skipser.com/p/2/p/auto-delete-email-in-any-gmail-label-.html
# https://developers.google.com/gmail/api/reference/rest/v1/users.messages/modify?
# https://developers.google.com/gmail/api/guides/labels#manage_labels_on_messages_threads



#client=GmailClient.setup()
message_client=MessageClient.setup()

#lables = message_client.list_labels()
#print("Labels:", lables)

def search_messages(search_string=None, read=False, after=None, before=None, from_=None, to=None, subject=None, labels=None, max_results=1000):
    result = message_client.list_messages(search_string=search_string, read=read, after=after, before=before, from_=from_, to=to, subject=subject, labels=labels, max_results=max_results)
    messages = result.get('messages', [])
    while True and not messages.__len__() >= max_results:
        print("Messages added count:", messages.__len__())
        if 'nextPageToken' in result:
            result = message_client.list_messages(search_string=search_string, read=read, after=after, before=before, from_=from_, to=to, subject=subject, max_results=max_results, labels=labels, page_token=result['nextPageToken'])
            messages += result.get('messages', [])
        else:
            break
    print("Message count:", len(messages))
    return messages


def delete_messages(search_string=None, read=False, after=None, before=None, from_=None, to=None, subject=None, labels=None):
    total__messages_deleted_count = 0
    while True:
        messages = search_messages(search_string=search_string, read=read, after=after, before=before, from_=from_, to=to, subject=subject, labels=labels)
        if messages.__len__() > 0:
            message_ids = [message['id'] for message in messages]
            print("Message ids count:", len(message_ids))
            print("Message ids:", message_ids)
            message_client.batch_trash(message_ids)
            total__messages_deleted_count += len(message_ids)
        else:
            break
        
    print("Messages deleted count:", total__messages_deleted_count)
    print("Task completed")
        


if "__main__" == __name__:
    #  messages = search_messages(search_string=None, read=False,  after="2020-01-01", before=None, from_="nyhetsbrev@tovek.se", to=None, subject=None, label=None)
    #  messages += message_client.list(search_string=None, read=False,  after="2020-01-01", from_="nyhetsbrev@tovek.se", page_token=messages['nextPageToken'])
    #delete_messages(search_string=None, read=False,  after="2020-01-01", before=None, from_="nyhetsbrev@tovek.se")
    delete_messages(labels= ['CATEGORY_PROMOTIONS'])
    

