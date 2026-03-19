#!/bin/bash
set -e

# ─── Startup Order ───────────────────────────────────────────────────
# 1. S3 Sync      (ENV=ecs)            — pull pre-trained models/encoders
# 2. Indexing      (INDEXING=true)      — MUST run first so the info
#    collection (description/color/icon lookups) and search indexes
#    exist before predictions are made. Without it, predictions show
#    "Description not found".
# 3. Model training (GENERATE_MODELS=true) — trains ML models from CSVs.
#    Only needed if models aren't already in the image or S3.
# 4. CMD (api or stream) — the main process.
#
# Sensor datasets (6 total):
#   cooler_condition, valve_condition, internal_pump_leakage,
#   hydraulic_accumulator, stable_flag, motor_power
#
# On a fresh/empty database:
#   - simulation.py creates collections for ALL datasets (including new
#     ones) — it no longer requires the DB to be completely empty.
#   - stream.py retries for up to 10 min waiting for collections.
#   - indexing.py upserts info records (safe to re-run).
# ─────────────────────────────────────────────────────────────────────

cd /app/backend

# Sync models from S3 if running on ECS
if [ "$ENV" = "ecs" ]; then
    echo "[INFO] Running on ECS — syncing models from S3..."
    mkdir -p models encoders
    aws s3 sync "s3://$BUCKET/models/" models/ || true
    aws s3 sync "s3://$BUCKET/encoders/" encoders/ || true
fi

# Run indexing if flagged (idempotent — safe to re-run)
if [ "$INDEXING" = "true" ]; then
    echo "[INFO] Running indexing..."
    python indexing.py
fi

# Generate models if flagged
if [ "$GENERATE_MODELS" = "true" ]; then
    echo "[INFO] Generating models..."
    python generate_models.py
    if [ "$ENV" = "ecs" ]; then
        aws s3 sync models/ "s3://$BUCKET/models/"
        aws s3 sync encoders/ "s3://$BUCKET/encoders/"
    fi
fi

# Verify expected models exist before starting
EXPECTED_MODELS=$(ls datasets/*.csv 2>/dev/null | wc -l)
ACTUAL_MODELS=$(ls models/*.pkl 2>/dev/null | wc -l)
if [ "$ACTUAL_MODELS" -eq 0 ] && [ "$EXPECTED_MODELS" -gt 0 ]; then
    echo "[WARN] No trained models found in models/ but $EXPECTED_MODELS datasets exist."
    echo "[WARN] Run with GENERATE_MODELS=true or ensure models are in S3."
fi

# Execute the CMD passed to the container
exec "$@"
