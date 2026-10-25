# Cached-artifact demo image. No build-time network beyond the package installs,
# and no keys baked in: live agent runs stay off unless ANTHROPIC_API_KEY is
# supplied at run time.
FROM node:20-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    REPURPOSE_OFFLINE=1 \
    REPURPOSE_DAILY_LIVE_CAP=40

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
      "fastapi>=0.115,<1" "uvicorn>=0.30,<1" \
      "pandas==2.3.3" "networkx==3.6.1" "requests>=2.32,<3" \
      "pyarrow>=19,<24" "numpy>=2,<3" "scipy>=1.14,<2" "anthropic>=0.40"

COPY src/ src/
COPY artifacts/ artifacts/
COPY data/synonyms.json data/synonyms.json
COPY data/cache/ data/cache/
COPY config/ config/
COPY --from=web /web/dist web/dist

# Measured peak resident for the hot artifacts is ~134 MB; with uvicorn this lands
# around 200 MB, so a 512 MB instance is comfortable and 256 MB is not.
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=4)"
CMD ["python", "-m", "uvicorn", "repurpose.api:app", "--app-dir", "src", \
     "--host", "0.0.0.0", "--port", "8000"]
