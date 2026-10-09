FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ARG INSTALL_TEST_DEPS=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN if [ "$INSTALL_TEST_DEPS" = "true" ]; then \
      pip install --no-cache-dir ".[test]"; \
    else \
      pip install --no-cache-dir .; \
    fi

EXPOSE 8000

CMD ["uvicorn", "src.listener.app:app", "--host", "0.0.0.0", "--port", "8000"]
