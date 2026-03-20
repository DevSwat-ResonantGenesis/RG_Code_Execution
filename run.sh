#!/bin/bash
# Start Code Execution Microservice

cd "$(dirname "$0")"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
