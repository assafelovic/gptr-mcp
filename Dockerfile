# ── Stage 1: build wheels ────────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /app

ARG BUILD_FROM_SOURCE=false
ARG GPT_RESEARCHER_OWNER=assafelovic
ARG GPT_RESEARCHER_REF=master

ENV EXTRA_PIP_PACKAGES=""
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        $([ "$BUILD_FROM_SOURCE" = "true" ] && echo git) \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN if [ "$BUILD_FROM_SOURCE" = "true" ]; then \
      sed -E "s|^gpt-researcher.*$|gpt-researcher @ git+https://github.com/${GPT_RESEARCHER_OWNER}/gpt-researcher.git@${GPT_RESEARCHER_REF}|" \
        requirements.txt > requirements.build.txt; \
    else \
      cp requirements.txt requirements.build.txt; \
    fi

RUN pip install --upgrade pip \
 && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.build.txt


# ── Stage 2: runtime ────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

COPY --from=builder /wheels /wheels

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir /wheels/*.whl \
 && rm -rf /wheels \
 && find /usr/local/lib/python3.11/site-packages \
      \( -type d -name "__pycache__" \
         -o -type d -name "tests" \
         -o -type d -name "test" \
         -o -type d -name "testing" \
         -o -name "*.pyc" \
         -o -name "*.pyo" \
         -o -name "*.c" \
         -o -name "*.h" \
         -o -name "*.a" \
         -o -name "*.lib" \
         -o -name "*.pdb" \) \
      -exec rm -rf {} + 2>/dev/null; true

COPY . .

ENV DOCKER_CONTAINER=true \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=7s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the server
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "server.py"]
