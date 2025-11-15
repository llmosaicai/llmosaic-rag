FROM alpine:3.20
WORKDIR /assets
ARG REPO_ROOT=.
# Copy specs, notebooks, and fixture SQL from repo root (build with context at repo root)
COPY ./repos-local/llmosaic-rag/assets/specs/ ./specs/
COPY ./repos-local/llmosaic-rag/assets/notebooks/ ./notebooks/
COPY ./services/frontend/public/fixtures/film_db_backup.sql ./film_db_backup.sql
