FROM alpine:3.20
WORKDIR /assets
# Build from the llmosaic-rag repo root; copy local assets (specs + notebooks)
COPY ./assets/specs/ ./specs/
COPY ./assets/notebooks/ ./notebooks/
# NOTE: We intentionally do not COPY film_db_backup.sql from outside this repo.
# If a fixture is included under ./assets/film_db_backup.sql it will be copied by the seed job’s recursive copy.
