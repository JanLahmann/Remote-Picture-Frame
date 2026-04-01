"""IBM Cloud Function: refresh_subscription

Triggered daily by an IBM Cloud cron trigger. Renews the Microsoft Graph API
webhook subscription so we continue receiving change notifications for the
OneDrive /FamilyFrame/photos/ folder.

If no subscription exists (first run or expired), creates a new one.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared import config
from shared.onedrive import create_subscription, renew_subscription
from shared.metadata import _get_client as get_cloudant_client

# Cloudant doc ID for storing the subscription state
SUBSCRIPTION_DOC_ID = "_local/graph_subscription"


def main(params: dict) -> dict:
    """Entry point for the IBM Cloud Function."""
    config.init(params)

    db_name = config.get("CLOUDANT_DB_NAME", "familyframe")
    client = get_cloudant_client()

    # Load existing subscription ID from Cloudant
    subscription_id = None
    try:
        doc = client.get_document(db=db_name, doc_id=SUBSCRIPTION_DOC_ID).get_result()
        subscription_id = doc.get("subscription_id")
    except Exception:
        pass

    user_id = config.get("ONEDRIVE_USER_ID")
    resource = f"/users/{user_id}/drive/root"
    webhook_url = config.get("WEBHOOK_URL")

    if subscription_id:
        # Try to renew existing subscription
        try:
            result = renew_subscription(subscription_id)
            return {
                "statusCode": 200,
                "body": {
                    "action": "renewed",
                    "subscription_id": subscription_id,
                    "expiration": result.get("expirationDateTime"),
                },
            }
        except Exception:
            # Subscription expired or invalid — create a new one
            pass

    # Create new subscription
    result = create_subscription(resource=resource, notification_url=webhook_url)
    new_sub_id = result["id"]

    # Store the subscription ID in Cloudant
    doc = {
        "_id": SUBSCRIPTION_DOC_ID,
        "subscription_id": new_sub_id,
        "resource": resource,
        "expiration": result.get("expirationDateTime"),
    }
    try:
        existing = client.get_document(db=db_name, doc_id=SUBSCRIPTION_DOC_ID).get_result()
        doc["_rev"] = existing["_rev"]
    except Exception:
        pass

    client.put_document(db=db_name, doc_id=SUBSCRIPTION_DOC_ID, document=doc).get_result()

    return {
        "statusCode": 200,
        "body": {
            "action": "created",
            "subscription_id": new_sub_id,
            "expiration": result.get("expirationDateTime"),
        },
    }
