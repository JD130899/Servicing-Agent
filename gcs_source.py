from pathlib import Path
from google.cloud import storage

BASE_DIR = Path(__file__).resolve().parent
BUCKET = "servicing-agent-docs-jai-20261018"

OBJECTS = [
    "support_policy.pdf",
    "duplicate_charge_guide.pdf",
]


def sync_gcs_pdfs():
    client = storage.Client(project="valuebuddy-demo")
    bucket = client.bucket(BUCKET)
    sources = {}

    for name in OBJECTS:
        blob = bucket.get_blob(name)

        if blob is None:
            raise FileNotFoundError(f"Missing gs://{BUCKET}/{name}")

        destination = BASE_DIR / "sources" / "cloud_storage" / name
        destination.parent.mkdir(parents=True, exist_ok=True)

        temporary = destination.with_suffix(".pdf.tmp")

        try:
            blob.download_to_filename(
                str(temporary),
                if_generation_match=int(blob.generation),
            )
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)

        uri = f"gs://{BUCKET}/{name}"
        sources[destination] = uri
        print(f"Downloaded from GCS: {uri}")

    return sources