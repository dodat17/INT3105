FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN addgroup --system cinema && adduser --system --ingroup cinema cinema
WORKDIR /app
COPY --from=builder /install /usr/local
COPY src ./src
COPY scripts ./scripts
ENV PYTHONPATH=/app/src
USER cinema
EXPOSE 8000
CMD ["sh", "-c", "uvicorn cinema_booking.api.app:app --host 0.0.0.0 --port 8000 --workers ${WEB_WORKERS:-2}"]
