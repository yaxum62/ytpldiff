from googleapiclient import discovery
import google.auth.exceptions
from playlist_history import History, PlaylistItem, Diff
import typing
import credential
import os
import json
from notify import notify
from deploy_credentials import deploy
import time

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


def diff(cred, playlist_id):
    hist = History(cred, playlist_id)
    saved_items = hist.latest()
    current_items = get_playlist_items(cred, playlist_id)

    diffs = Diff(saved_items, current_items)

    if diffs:
        hist.append(current_items)
        notify(f"Your playlist {playlist_id} has been updated.", diffs)

    return diffs


def run():
    with credential.Cred(credential.Cred.Kind.Credential) as cred:
        if cred is None:
            notify("cannot find credential")
            return
        for i in range(2):
            try:
                diff(cred, "LL")
            except google.auth.exceptions.GoogleAuthError as e:
                notify(f"Auth failed: {e}")
                deploy()
                time.sleep(1)
            else:
                return
        notify(f"too many fails, give up")




if __name__ == "__main__":
    run()