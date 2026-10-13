FROM python:3.11-slim

WORKDIR /app

COPY frontend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --timeout=120 --retries=10 -r requirements.txt

COPY frontend/ ./frontend/

ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]