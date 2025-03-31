FROM python:3.11-slim

WORKDIR /app

# Dastlab tizim paketlarini o'rnatamiz (agar kerak bo'lsa)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Virtual muhit yaratamiz
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Avval requirements.txt ni ko'chiramiz
COPY requirements.txt .

# Kutubxonalarni o'rnatamiz
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Barcha fayllarni ko'chiramiz
COPY . .

# Ishga tushirish buyrug'i
CMD ["python", "main.py"]
