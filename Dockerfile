FROM python:3.12-slim
WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_HOST=0.0.0.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
  && rm -rf /var/lib/apt/lists/*

COPY config.py ./
COPY api/ ./api/
COPY www/ ./www/
RUN pip install --no-cache-dir -r api/requirements.txt

EXPOSE 5000
CMD ["python3", "api/app1.py"]
