"""Run on your Mac; writes the CLI token to .env without printing it."""
from pathlib import Path
from dotenv import set_key
from salesforce_client import run_sf

if __name__ == "__main__":
    env = Path(__file__).resolve().parent / ".env"
    if not env.exists():
        raise SystemExit("Copy .env.example to .env first")
    metadata = run_sf(["org", "display", "--target-org", "servicing-demo"])
    credentials = run_sf(["org", "auth", "show-access-token", "--target-org", "servicing-demo"])
    token = credentials["accessToken"]
    if not token or "[REDACTED]" in token:
        raise SystemExit("Salesforce did not return a usable token; refresh your CLI login")
    for key, value in {"SALESFORCE_AUTH_MODE": "token", "SALESFORCE_INSTANCE_URL": metadata["instanceUrl"], "SALESFORCE_ACCESS_TOKEN": token}.items():
        set_key(str(env), key, value, quote_mode="never")
    env.chmod(0o600)
    print("Salesforce credentials saved to .env. Token is temporary; no token was printed.")
