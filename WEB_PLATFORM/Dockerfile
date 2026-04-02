FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY diagnostic/ .
RUN python manage.py collectstatic --noinput 2>/dev/null || true
EXPOSE 8001
CMD ["sh", "-c", "python manage.py migrate --run-syncdb && python manage.py runserver 0.0.0.0:8001"]
