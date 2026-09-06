# Dev-oriented backend image: the source tree is bind-mounted over this in
# docker-compose.yml, so `--reload` picks up code changes without a rebuild.
# The image still works standalone (`docker build . && docker run`) since the
# COPY below gives it a full, runnable copy of the repo too.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
