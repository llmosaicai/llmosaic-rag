FROM alpine:3.20
WORKDIR /assets
# Build from the llmosaic-rag repo root; copy local assets
COPY ./assets/specs/ ./specs/
COPY ./assets/notebooks/ ./notebooks/
# Include film DB SQL fixture if available in this repo; tolerate missing path
ARG FIXTURE=services/frontend/public/fixtures/film_db_backup.sql
COPY ${FIXTURE} ./film_db_backup.sql
