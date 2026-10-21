"""Shared configuration and Cohere retrieval helpers."""
import json
import math
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INDEX_PATH = BASE_DIR / 'data' / 'cohere_policy_index.json'
MODEL = 'embed-v4.0'
CHUNK_SIZE = 1400
CHUNK_OVERLAP = 200


def load_environment():
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')


def embed(texts, input_type, model=MODEL):
    import cohere
    client = cohere.ClientV2(api_key=os.environ['COHERE_API_KEY'])
    vectors = []
    for offset in range(0, len(texts), 32):
        result = client.embed(texts=texts[offset:offset + 32], model=model,
                              input_type=input_type, embedding_types=['float'])
        vectors.extend(result.embeddings.float_)
    if len(vectors) != len(texts):
        raise ValueError('Embedding response count does not match input count.')
    return vectors


def split_text(text):
    text = text.strip()
    return [text[start:start + CHUNK_SIZE]
            for start in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP)]


def cosine_similarity(a, b):
    if len(a) != len(b):
        raise ValueError('Embedding dimensions differ. Rebuild the Cohere index.')
    denominator = math.sqrt(sum(x*x for x in a) * sum(y*y for y in b))
    return sum(x*y for x, y in zip(a, b)) / denominator if denominator else 0.0


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(path)
