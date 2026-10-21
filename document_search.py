"""MCP-compatible search_documents replacement; no PDF parsing at query time."""
import json

from rag_common import INDEX_PATH, cosine_similarity, embed, load_environment

load_environment()


def search_documents(query: str):
    """Search fictional support policies; return source filenames and PDF pages."""
    if not query.strip():
        return {'error': 'A search question is required.'}
    if not INDEX_PATH.exists():
        return {'error': 'Cohere policy index missing. Run python ingest.py first.'}
    index = json.loads(INDEX_PATH.read_text(encoding='utf-8'))
    if index.get('provider') != 'cohere':
        return {'error': 'Unexpected embedding provider. Rebuild with python ingest.py.'}
    if not index['records']:
        return {'error': 'The policy index is empty.'}
    vector = embed([query], 'search_query', model=index['model'])[0]
    ranked = sorted(((cosine_similarity(vector, record['embedding']), record)
                     for record in index['records']), reverse=True, key=lambda pair: pair[0])
    return {'passages': [
        {**{key: record[key] for key in ('source', 'source_system', 'source_mode',
                                        'source_path', 'page', 'chunk_id', 'text')},
         'score': round(score, 4)}
        for score, record in ranked[:3]
    ]}
