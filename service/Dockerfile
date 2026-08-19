# Live chain check API. Build context is the repo root, because the service
# imports the measurement code from src/ instead of carrying a copy:
#   docker build -f service/Dockerfile -t chain-check-api .
FROM python:3.13-slim

WORKDIR /app
COPY service/requirements.txt service/requirements.txt
RUN pip install --no-cache-dir -r service/requirements.txt

COPY src/ src/
COPY service/app.py service/app.py
# The scenario-order self-check reads the shipped meta.json at import time in
# selfcheck, not in app.py, so only the code ships in the image.

# ssl.get_unverified_chain needs Python 3.13+; fail the build, not the runtime.
RUN python -c "import ssl; assert hasattr(ssl.SSLSocket, 'get_unverified_chain')"

USER nobody
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--app-dir", "service", "--host", "0.0.0.0", "--port", "8000"]
