FROM python:3.12-slim
WORKDIR /srv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt
COPY storefront_agents ./storefront_agents
COPY skills ./skills
COPY data ./data
COPY runs/baseline-v1/outputs.jsonl ./runs/baseline-v1/outputs.jsonl
COPY runs/pipeline-v1/outputs.jsonl ./runs/pipeline-v1/outputs.jsonl
COPY evals/rubric.md ./evals/rubric.md
COPY app ./app
# One worker: the per-visitor limits live in memory (Cloud Run max instances = 1).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1"]
