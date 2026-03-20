FROM docker:cli AS docker-cli

FROM python:3.11-slim

WORKDIR /app

# Copy docker CLI binary from official image
COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
