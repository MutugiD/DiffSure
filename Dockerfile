FROM python:3.12-slim

LABEL org.opencontainers.image.title="DiffSure" \
      org.opencontainers.image.description="Independently verified repository patch service" \
      org.opencontainers.image.source="https://github.com/MutugiD/DiffSure" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends docker-cli git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

USER 65534:65534
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]
ENTRYPOINT ["diffsure"]
CMD ["serve"]
