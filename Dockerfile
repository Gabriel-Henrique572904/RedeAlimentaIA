FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --upgrade \
    "jaraco.context==6.1.0" \
    "wheel==0.46.2" \
    && python -c "import importlib.metadata as m; print('jaraco.context:', m.version('jaraco.context')); print('wheel:', m.version('wheel'))"

COPY app ./app
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]