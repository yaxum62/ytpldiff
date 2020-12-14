#!/bin/bash

set -e

PROJECT=$(gcloud config get-value project)

FUNCTION_NAME=ytpldiff
SCHEDULER_NAME=ytpldiff

gcloud functions deploy ${FUNCTION_NAME} \
    --entry-point run \
    --runtime python39 \
    --set-env-vars GCP_PROJECT=${PROJECT} \
    --trigger-http \
    --no-allow-unauthenticated

if ! gcloud scheduler jobs describe ${SCHEDULER_NAME} >/dev/null; then
    gcloud scheduler jobs create http ${SCHEDULER_NAME} \
        --schedule="42 17 * * *" \
        --uri=$(gcloud functions describe ${FUNCTION_NAME} --format=value\(httpsTrigger.url\)) \
        --oidc-service-account-email=$(gcloud functions describe ${FUNCTION_NAME} --format=value\(serviceAccountEmail\))
fi

exec ./.venv/bin/python deploy_credentials.py "$@" --project=${PROJECT}
