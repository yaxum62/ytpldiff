import json
import subprocess
import typing
from contextlib import contextmanager

import google.api_core.exceptions
import google.auth.transport.requests
import google_auth_oauthlib.flow
from google.cloud import secretmanager
from google.oauth2.credentials import Credentials

DEPLOY_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
USER_SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/drive.appdata",
    "https://www.googleapis.com/auth/gmail.insert"
]


def run(*cmd: str) -> str:
    return subprocess.run(cmd, check=True, capture_output=True,
                          text=True).stdout.strip()


@contextmanager
def secret_updater(svc: secretmanager.SecretManagerServiceClient, project: str,
                   secret: str) -> typing.Iterator[dict]:

    try:
        data = svc.access_secret_version(
            request={
                "name": f"projects/{project}/secrets/{secret}/versions/latest"
            }).payload.data
    except google.api_core.exceptions.NotFound:
        try:
            svc.create_secret(
                request={
                    "parent": f"projects/{project}",
                    "secret_id": secret,
                    "secret": {
                        "replication": {
                            "automatic": {}
                        }
                    }
                })
        except google.api_core.exceptions.AlreadyExists:
            pass
        data = "{}"
    origin_dict: dict = json.loads(data)
    updated_dict: dict = json.loads(data)
    try:
        yield updated_dict
    except:
        raise
    else:
        if origin_dict != updated_dict:
            svc.add_secret_version(
                request={
                    "parent": f"projects/{project}/secrets/{secret}",
                    "payload": {
                        "data": json.dumps(updated_dict).encode("utf-8")
                    }
                })


def deployer_login(client_secret: dict) -> Credentials:
    need_update = True
    try:
        cred = Credentials.from_authorized_user_file(".credential.json")
        if cred.valid:
            need_update = False
        else:
            refresh_token = cred.refresh_token
            cred.refresh(google.auth.transport.requests.Request())
            if refresh_token != cred.refresh_token:
                need_update = True
    except (FileNotFoundError, google.auth.exceptions.RefreshError):
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
            client_secret, scopes=DEPLOY_SCOPES)
        flow.run_console()
        cred = flow.credentials
    if need_update:
        with open(".credential.json", 'w', encoding="utf-8") as f:
            f.write(cred.to_json())
    return cred


def update_user_credentials(project: str,
                            svc: secretmanager.SecretManagerServiceClient,
                            client_secret: dict,
                            user_list: typing.Optional[typing.Set[str]]):
    with secret_updater(svc, project, "user_creds") as updating_creds:

        if user_list is not None:
            extra = [u for u in updating_creds if u not in user_list]
            for u in extra:
                del updating_creds[u]
            for u in user_list:
                if u not in updating_creds:
                    updating_creds[u] = None

        for user, cred in updating_creds.items():
            failed = cred is None
            if cred is not None:
                cred = Credentials.from_authorized_user_info(cred)
                try:
                    cred.refresh(google.auth.transport.requests.Request())
                except:
                    failed = True
            if failed:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_config(
                    client_secret, scopes=USER_SCOPES)
                flow.run_console(login_hint=user)
                updating_creds[user] = json.loads(flow.credentials.to_json())


def deploy(project: str, client_secret: dict,
           user_list: typing.Optional[typing.Set[str]]):
    cred = deployer_login(client_secret)
    sm_client = secretmanager.SecretManagerServiceClient(credentials=cred)

    update_user_credentials(project, sm_client, client_secret, user_list)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=None)
    parser.add_argument("--client_secret", default="client_secret.json")
    parser.add_argument("--user_list", default=None)
    args = parser.parse_args()

    if args.project is None:
        args.project = run("gcloud", "config", "get-value", "project")

    with open(args.client_secret, encoding="utf-8") as f:
        client_secret = json.load(f)

    if args.user_list is not None:
        args.user_list = set(args.user_list.split(","))

    deploy(args.project, client_secret, args.user_list)
