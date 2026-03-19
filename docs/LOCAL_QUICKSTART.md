# Local Quickstart

## Prerequisites

- Python 3.13+
- Node.js 18+
- MongoDB Atlas cluster (or local MongoDB with replica set for change streams)
- Voyage AI API key (for embeddings and reranking)

## 1. Environment Setup

Set required environment variables:

```bash
export MONGODB_URI="mongodb+srv://user:password@cluster.mongodb.net"
export VOYAGE_API_KEY="your-voyage-api-key"
```

Optional overrides:

```bash
export MONGODB_NAME="predictions"
export EMBEDDING_MODEL="voyage/voyage-3"
export RERANKER_MODEL="voyage/rerank-2"
```

## 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

## 3. Data Indexing (Run First)

> **Important:** Indexing must run before simulation or stream processing. It creates the `info` collection (description/color/icon lookups for all 6 sensor types) and the search indexes (for the RAG pipeline). If the stream processor runs before indexing, predictions will show "Description not found" with no color/icon metadata.

Index technical documents and create search indexes:

```bash
cd backend
python indexing.py
```

This will:
- Chunk documents from `data_processing/data/`
- Generate embeddings via Voyage AI
- Store chunks with embeddings in MongoDB
- Create a vector search index (`embeddings`)
- Create a full-text search index (`text_search`)
- Upsert `info.csv` metadata (safe to re-run — existing records are updated, not duplicated)

> **Note:** `indexing.py` is idempotent. Re-running it will clear and re-index chunks, and upsert info records without duplicate key errors.

## 4. Model Training

Train ML models from the 6 CSV datasets:

```bash
cd backend
python generate_models.py
```

This will:
- Load and scale all 6 datasets from `datasets/`:
  - `Cooler_condition.csv`, `Valve_condition.csv`, `Internal_pump_leakage.csv`
  - `Hydraulic_accumulator.csv`, `Stable_flag.csv`, `Motor_power.csv`
- Train Logistic Regression and Random Forest models for each
- Keep only the best-performing model per target
- Save models to `models/` and encoders to `encoders/`

> **Note:** Pre-trained models are included in the repository. You only need to re-train if you modify the datasets or want fresh models.

## 5. Start the API Server

```bash
cd backend
python fastapi_mcp.py
```

The API server starts on `http://127.0.0.1:5001`. Verify with:

```bash
curl http://127.0.0.1:5001/health
```

To make the API accessible from other machines on the network:

```bash
export HOST=0.0.0.0
python fastapi_mcp.py
```

## 6. Start the Stream Processor

In a separate terminal:

```bash
cd backend
python stream.py
```

This watches MongoDB change streams on all 6 sensor input collections and processes predictions in real-time.

> **Note:** The stream processor discovers collections at startup. If you add new sensor datasets and collections after the stream processor is already running, you must restart it for the new sensors to be picked up.

> **Note:** On a fresh database with no collections, the stream processor retries every 30 seconds for up to 10 minutes, waiting for simulation or indexing to create collections.

## 7. Run Simulation

To insert sample sensor data for all 6 sensors:

```bash
cd backend
python simulation.py
```

This inserts one round of random sensor readings for each sensor type. Run it multiple times or set up a cron job for continuous simulation.

> **Note:** Simulation automatically creates MongoDB collections for any dataset that doesn't have a corresponding collection yet. This works whether the database is empty or already has existing collections — new sensor types (e.g., `stable_flag`, `motor_power`) will be bootstrapped alongside existing ones.

## 8. Start the Frontend

The frontend requires backend connection environment variables to be set **before** starting the dev server (React inlines `REACT_APP_*` variables at build/start time):

```bash
cd ui
npm install

# Point frontend at the backend API (defaults to 127.0.0.1:5001)
export REACT_APP_FASTAPI_HOST=127.0.0.1
export REACT_APP_FASTAPI_PORT=5001

npm start
```

The UI starts on `http://localhost:3001`.

To make the frontend accessible from other machines:

```bash
HOST=0.0.0.0 npm start
```

> **Important:** If the backend is running on a different host (e.g., a remote server), set `REACT_APP_FASTAPI_HOST` to that host's IP or hostname before running `npm start`. Changing these values after the server starts has no effect — you must restart.

## 9. Docker (Alternative)

```bash
docker build -t predictive-maintenance .
docker run -p 5001:5001 \
  -e MONGODB_URI="mongodb+srv://..." \
  -e VOYAGE_API_KEY="..." \
  predictive-maintenance
```

The Docker image runs the backend only. For the frontend, use `npm start` locally or deploy via Amplify.

## Startup Order Summary

```
1. python indexing.py          ← Creates info collection + search indexes
2. python generate_models.py   ← Trains models (skip if using pre-trained)
3. python fastapi_mcp.py       ← API server (must be running before stream.py)
4. python stream.py            ← Change stream processor (discovers collections at start)
5. python simulation.py        ← Pushes sensor data (creates missing collections)
6. cd ui && npm start           ← Frontend dashboard
```
