FROM python:3.12-slim-trixie
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client curl ca-certificates && rm -rf /var/lib/apt/lists/* && useradd --uid 10001 --create-home app
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY backend/ ./
COPY data/ /data/
ENV SEED_FILE=/data/catalog/seed.json SCHEMA_FILE=/data/catalog/schema.json STATIC_ROOT=/app/staticfiles MEDIA_ROOT=/app/media EXPORT_ROOT=/app/exports
RUN mkdir -p staticfiles media exports && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["gunicorn","config.wsgi:application","--bind","0.0.0.0:8000","--workers","2","--threads","4","--timeout","60","--access-logfile","-"]
