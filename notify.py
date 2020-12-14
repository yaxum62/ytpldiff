from googleapiclient import discovery
from email.mime.text import MIMEText
import smtplib
import base64


def notify(user, cred, playlist_id, diff):
    svc = discovery.build("gmail", "v1", credentials=cred)
    msg = "<html><head><style>.add{background-color:LightGreen;}.remove{background-color:IndianRed;}.change{background-color:Gold;}</style></head><body>"
    for old, new in diff:
        if old is None:
            msg += f'<p class="add">Added {new}</p>'
        elif new is None:
            msg += f'<p class="remove">Removed {old}</p>'
        else:
            msg += f'<p class="change">Updated {old} -> {new}</p>'
    msg += "</body></html>"
    mail = MIMEText(msg, "html")
    mail['from'] = user
    mail['to'] = user
    mail['subject'] = f"Your playlist {playlist_id} has been updated."

    svc.users().messages().insert(
        userId="me",
        body={
            "labelIds": ["INBOX", "UNREAD", "IMPORTANT"],
            "raw": base64.urlsafe_b64encode(mail.as_bytes()).decode("ascii")
        }).execute()
