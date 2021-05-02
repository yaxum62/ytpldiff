import json
import subprocess
import typing

import credential
import google.auth.transport.requests
import google_auth_oauthlib.flow

USER_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/drive.appdata",
]


def deploy():
    with credential.Cred(credential.Cred.Kind.ClientSecret) as client_secret:
        if client_secret is None:
            print("cannot find client secret, input:")
            client_secret = json.loads(input())
            credential.Cred.set(credential.Cred.Kind.ClientSecret,
                                client_secret)

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
            client_secret, scopes=USER_SCOPES)
        flow.run_local_server(port=0)
        credential.Cred.set(credential.Cred.Kind.Credential, flow.credentials)


if __name__ == "__main__":
    deploy()
