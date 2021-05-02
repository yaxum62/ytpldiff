import typing
import keyring
import json
import enum
from google.oauth2.credentials import Credentials


class Cred:
    class Kind(enum.Enum):
        Credential = 1
        ClientSecret = 2

        def serialize(self, obj: typing.Any) -> str:
            if self == Cred.Kind.Credential:
                if not isinstance(obj, Credentials):
                    raise TypeError
                return obj.to_json()
            if self == Cred.Kind.ClientSecret:
                if not isinstance(obj, dict):
                    raise TypeError
                return json.dumps(obj)
            raise ValueError

        def deserialize(self, val: str) -> typing.Any:
            if self == Cred.Kind.Credential:
                return Credentials.from_authorized_user_info(json.loads(val))
            if self == Cred.Kind.ClientSecret:
                return json.loads(val)
            raise ValueError

    @staticmethod
    def set(kind: Kind, val):
        keyring.set_password("ytpldiff", kind.name, kind.serialize(val))

    def __init__(self, kind: Kind):
        self.__kind = kind
        self.__cred = None
        self.__cred_val = None

    def __enter__(self):
        self.__cred_val = keyring.get_password("ytpldiff", self.__kind.name)
        if self.__cred_val is None:
            return None
        self.__cred = self.__kind.deserialize(self.__cred_val)
        return self.__cred

    def __exit__(self, typ, val, tb):
        if self.__cred is None:
            return

        new_val = self.__kind.serialize(self.__cred)
        if new_val != self.__cred_val:
            keyring.set_password("ytpldiff", self.__kind.name, new_val)
