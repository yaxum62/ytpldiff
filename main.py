from google.oauth2.credentials import Credentials
from googleapiclient import discovery
from playlist_history import History, PlaylistItem
import typing
from google.cloud import secretmanager
import os
import json
from notify import notify

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

MAX_PAGE_SIZE = 50


def get_playlist_items(cred, pl_id):
    svc = discovery.build("youtube", "v3", credentials=cred)

    ret: typing.List[PlaylistItem] = []
    req = svc.playlistItems().list(part="snippet",
                                   playlistId=pl_id,
                                   maxResults=MAX_PAGE_SIZE)
    while True:
        resp = req.execute()
        for i in resp['items']:
            ni = PlaylistItem(id=i['id'],
                              videoId=i['snippet']['resourceId']['videoId'],
                              title=i['snippet']['title'],
                              description=i['snippet']['description'])

            ni.validate()
            if ni.title == 'Deleted video':
                continue
            ret.append(ni)

        req = svc.playlistItems().list_next(req, resp)
        if req is None:
            break

    return ret


def diff_list(
    saved: typing.List[PlaylistItem], current: typing.List[PlaylistItem]
) -> typing.Iterator[typing.Tuple[typing.Optional[PlaylistItem],
                                  typing.Optional[PlaylistItem]]]:
    saved_dict = {i.videoId: i for i in saved}
    current_dict = {i.videoId: i for i in current}

    for i in saved_dict:
        if i not in current_dict:
            yield saved_dict[i], None

    for i in current_dict:
        if i not in saved_dict:
            yield None, current_dict[i]
        elif current_dict[i].title != saved_dict[i].title:
            yield saved_dict[i], current_dict[i]


def diff(user, cred, playlist_id):
    hist = History(cred, playlist_id)
    saved_items = hist.latest()
    current_items = get_playlist_items(cred, playlist_id)

    diffs = list(diff_list(saved_items, current_items))

    if diffs:
        hist.append(current_items)
        notify(user, cred, playlist_id, diffs)

    return diffs


def run(request):
    this_project = os.environ['GCP_PROJECT']
    secret_mgr = secretmanager.SecretManagerServiceClient()
    creds_info: dict = json.loads(
        secret_mgr.access_secret_version(request={
            "name":
            f"projects/{this_project}/secrets/user_creds/versions/latest"
        }).payload.data)

    updated = False

    for user, info in creds_info.items():
        print(f"diff for user {user}:LL")
        cred = Credentials.from_authorized_user_info(info)
        diff(user, cred, "LL")
        if cred.refresh_token != info['refresh_token']:
            print(f"updating credentials for user {user}")
            creds_info[user] = json.loads(cred.to_json())
            updated = True

    if updated:
        secret_mgr.add_secret_version(
            request={
                "parent": f"projects/{this_project}/secrets/user_creds",
                "payload": {
                    "data": json.dumps(creds_info).encode("ascii")
                }
            })

    return "Done"
