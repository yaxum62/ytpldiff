from __future__ import annotations
import typing
import google.oauth2.credentials
from googleapiclient import discovery, http
import io
import json
from datetime import datetime


class PlaylistItem(typing.NamedTuple):
    id: str
    videoId: str
    title: str
    description: str

    @staticmethod
    def from_dict(item):
        if set(item.keys()) != {"id", "videoId", "title", "description"}:
            raise ValueError(item)
        ret = PlaylistItem(id=item['id'],
                           videoId=item['videoId'],
                           title=item['title'],
                           description=item['description'])
        ret.validate()
        return ret

    def validate(self):
        if not isinstance(self.id, str) or not isinstance(
                self.videoId, str) or not isinstance(
                    self.title, str) or not isinstance(self.description, str):
            raise TypeError(self)
        if self.id == "" or self.videoId == "" or self.title == "":
            raise ValueError(self)


class Diff:
    def __init__(self, old: list[PlaylistItem], new: list[PlaylistItem]):
        old_dict = {i.videoId: i for i in old}
        new_dict = {i.videoId: i for i in new}

        self.__diff = []

        for i in old_dict:
            if i not in new_dict:
                self.__diff.append((old_dict[i], None))

        for i in new_dict:
            if i not in old_dict:
                self.__diff.append((None, new_dict[i]))
            elif new_dict[i].title != old_dict[i].title:
                self.__diff.append((old_dict[i], new_dict[i]))

    def __iter__(
        self
    ) -> typing.Iterable[tuple[typing.Optional[PlaylistItem],
                               typing.Optional[PlaylistItem]]]:
        return iter(self.__diff)

    def __bool__(self):
        return bool(self.__diff)


class History:
    def __list_file(self, **kwargs):
        pageToken = None
        while True:
            resp = self.__drive_svc.files().list(
                spaces='appDataFolder',
                pageToken=pageToken,
                fields="nextPageToken,files(id)",
                **kwargs).execute()
            for f in resp.get("files", []):
                yield f.get("id")
            pageToken = resp.get('nextPageToken', None)
            if pageToken is None:
                break

    def __init__(self, user_cred: google.oauth2.credentials.Credentials,
                 playlist: str):
        self.__drive_svc = discovery.build("drive",
                                           "v3",
                                           credentials=user_cred)

        for folder in self.__list_file(
                q=
                f"'appDataFolder' in parents and mimeType = 'application/vnd.google-apps.folder' and name = '{playlist}'",
                pageSize=1):
            self.__folder_id = folder
            break
        else:
            resp = self.__drive_svc.files().create(body={
                "name": playlist,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": ["appDataFolder"]
            },
                                                   fields="id").execute()
            self.__folder_id = resp.get("id")

    def latest(self) -> typing.List[PlaylistItem]:
        for file in self.__list_file(
                q=
                f"'{self.__folder_id}' in parents and mimeType = 'application/json'",
                orderBy="createdTime desc",
                pageSize=1,
        ):
            req = self.__drive_svc.files().get_media(fileId=file)
            content = io.BytesIO()
            downloader = http.MediaIoBaseDownload(content, req)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            raw = json.loads(content.getvalue())
            return [PlaylistItem.from_dict(i) for i in raw]

        else:
            return []

    def append(self, new: typing.List[PlaylistItem]) -> None:
        b = json.dumps([i._asdict() for i in new],
                       ensure_ascii=False).encode("utf-8")
        file = http.MediaIoBaseUpload(io.BytesIO(b),
                                      mimetype="application/json")
        self.__drive_svc.files().create(body={
            "name":
            datetime.now().date().isoformat() + ".json",
            "parents": [self.__folder_id]
        },
                                        media_body=file).execute()
