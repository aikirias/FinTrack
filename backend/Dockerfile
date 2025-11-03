FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

CMD ["./start.sh"]
