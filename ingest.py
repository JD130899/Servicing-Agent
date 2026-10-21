"""Download PDFs from GCS, parse them, and save Cohere embeddings."""

import hashlib
import json

from gcs_source import sync_gcs_pdfs
from rag_common import (
    BASE_DIR,
    INDEX_PATH,
    MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    embed,
    load_environment,
    split_text,
    write_json,
)

PARSER_CONFIG = {
    "tier": "agentic",
    "version": "latest",
    "format": "markdown",
}


def parse_pdf(path):
    from llama_cloud import LlamaCloud

    client = LlamaCloud()

    uploaded = client.files.create(
        file=str(path),
        purpose="parse",
    )

    result = client.parsing.parse(
        file_id=uploaded.id,
        tier=PARSER_CONFIG["tier"],
        version=PARSER_CONFIG["version"],
        expand=["markdown"],
    )

    if not result.markdown or not result.markdown.pages:
        raise ValueError(f"No parsed pages returned for {path.name}")

    pages = [
        page.markdown or ""
        for page in result.markdown.pages
    ]

    if not any(text.strip() for text in pages):
        raise ValueError(f"No text returned for {path.name}")

    return pages


def ingest():
    # Download both PDFs from Google Cloud Storage.
    gcs_sources = sync_gcs_pdfs()
    files = sorted(gcs_sources)
    records = []

    if not files:
        raise ValueError("No PDFs downloaded from GCS.")

    for path in files:
        # Identify the PDF by its content.
        digest = hashlib.sha256(path.read_bytes()).hexdigest()

        parse_key = hashlib.sha256(
            (
                digest
                + json.dumps(PARSER_CONFIG, sort_keys=True)
            ).encode()
        ).hexdigest()

        parsed_path = (
            BASE_DIR / "data" / "parsed" / f"{parse_key}.json"
        )

        # Reuse parsed pages if this PDF has not changed.
        if parsed_path.exists():
            pages = json.loads(
                parsed_path.read_text(encoding="utf-8")
            )["pages"]

            print(f"Using saved parse: {path.name}")

        else:
            print(f"Parsing PDF with LlamaParse: {path.name}")
            pages = parse_pdf(path)

            write_json(
                parsed_path,
                {
                    "pages": pages,
                    "sha256": digest,
                    "parser": PARSER_CONFIG,
                },
            )

        # Invalidate embeddings if the model or chunk settings change.
        settings = (
            f"{parse_key}:{MODEL}:{CHUNK_SIZE}:"
            f"{CHUNK_OVERLAP}:search_document"
        )

        embed_key = hashlib.sha256(
            settings.encode()
        ).hexdigest()

        vector_path = (
            BASE_DIR / "data" / "embeddings" / f"{embed_key}.json"
        )

        if vector_path.exists():
            chunks = json.loads(
                vector_path.read_text(encoding="utf-8")
            )["chunks"]

            print(f"Using saved embeddings: {path.name}")

        else:
            chunks = [
                {
                    "page": page_number,
                    "text": chunk,
                }
                for page_number, text in enumerate(pages, start=1)
                for chunk in split_text(text)
            ]

            vectors = embed(
                [chunk["text"] for chunk in chunks],
                "search_document",
            )

            for chunk, vector in zip(chunks, vectors):
                chunk["embedding"] = vector

            write_json(
                vector_path,
                {
                    "model": MODEL,
                    "chunks": chunks,
                },
            )

        # Preserve the original GCS location for every passage.
        source_path = path.relative_to(BASE_DIR).as_posix()

        for index, chunk in enumerate(chunks):
            records.append(
                {
                    "source": path.name,
                    "source_system": "gcs",
                    "source_mode": "gcs",
                    "source_uri": gcs_sources[path],
                    "source_path": source_path,
                    "chunk_id": index,
                    "sha256": digest,
                    **chunk,
                }
            )

    if not records:
        raise ValueError(
            "No passages found; existing index was not changed."
        )

    write_json(
        INDEX_PATH,
        {
            "schema_version": 1,
            "provider": "cohere",
            "model": MODEL,
            "records": records,
        },
    )

    print(
        f"Saved {len(records)} passages "
        f"from {len(files)} GCS PDFs to {INDEX_PATH}"
    )


if __name__ == "__main__":
    load_environment()
    ingest()