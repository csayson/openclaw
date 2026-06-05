FROM python:3.11-slim

WORKDIR /app

# System deps for TA-Lib and psycopg
RUN apt-get update && apt-get install -y \
    build-essential wget libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Build TA-Lib from source
RUN wget https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib && ./configure --prefix=/usr && make && make install \
    && cd .. && rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:socket_app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop"]
