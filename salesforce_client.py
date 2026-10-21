import os
from dotenv import load_dotenv
import json
import subprocess

from simple_salesforce import Salesforce


def run_sf(arguments):
    result = subprocess.run(
        ["sf", *arguments, "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Salesforce CLI command failed. Try logging in again with: "
            "sf org login web --alias servicing-demo"
        )

    payload = json.loads(result.stdout)

    if payload.get("status") != 0:
        raise RuntimeError("Salesforce CLI could not complete the request.")

    return payload["result"]


def get_salesforce():
    load_dotenv()
    mode = os.environ.get("SALESFORCE_AUTH_MODE", "cli")
    if mode == "token":
        return Salesforce(instance_url=os.environ["SALESFORCE_INSTANCE_URL"],
                          session_id=os.environ["SALESFORCE_ACCESS_TOKEN"])
    if mode == "jwt":
        return Salesforce(username=os.environ["SALESFORCE_USERNAME"],
                          consumer_key=os.environ["SALESFORCE_CONSUMER_KEY"],
                          privatekey_file=os.environ["SALESFORCE_PRIVATE_KEY_FILE"],
                          domain=os.environ.get("SALESFORCE_DOMAIN", "login"))
    if mode != "cli":
        raise ValueError("Unsupported SALESFORCE_AUTH_MODE")

    metadata = run_sf([
        "org", "display",
        "--target-org", "servicing-demo",
    ])

    credentials = run_sf([
        "org", "auth", "show-access-token",
        "--target-org", "servicing-demo",
    ])

    token = credentials["accessToken"]

    if not token or "[REDACTED]" in token:
        raise RuntimeError("Salesforce did not return a usable access token.")

    return Salesforce(
        instance_url=metadata["instanceUrl"],
        session_id=token,
    )