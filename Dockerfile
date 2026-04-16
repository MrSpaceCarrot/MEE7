# Build
FROM python:3.14-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv pip install --system .

# Runtime
FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /usr/local /usr/local

COPY . .

RUN addgroup --system mee7group && \
    adduser --system --ingroup mee7group mee7user && \
    mkdir -p /app/logs && \
    chown -R mee7user:mee7group /app

USER mee7user

CMD ["python", "main.py"]