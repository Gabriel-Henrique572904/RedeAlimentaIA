FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade \
    pip \
    setuptools \
    && pip install --no-cache-dir -r requirements.txt \
    && python -c "import importlib.metadata as m; print('setuptools:', m.version('setuptools')); print('wheel:', m.version('wheel')); print('jaraco.context:', m.version('jaraco.context'))"

COPY app ./app
COPY data ./data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]