FROM python:3.12-slim

# تثبيت الأدوات اللازمة لبناء المكتبات (مثل OpenCV أو التشفير)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت المكتبات (هذه الطبقة يتم تخزينها مؤقتاً لتسريع البناء)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات المشروع
COPY . .

# إنشاء المجلدات المطلوبة للتشغيل
RUN mkdir -p uploads/rooms cached


CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]