FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser
COPY main.py agent.py mcp_server.py tools.py salesforce_client.py snowflake_client.py document_search.py rag_common.py index.html ./
COPY data/cohere_policy_index.json ./data/cohere_policy_index.json
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
