# Predictive Maintenance — AWS + MongoDB Atlas + Voyage AI

Industrial predictive maintenance system powered by three core technologies:

- **MongoDB Atlas** — Operational database, vector search, full-text search, and change streams for real-time processing
- **AWS** — ECS Fargate compute, Bedrock LLM inference, S3 model storage, CloudWatch observability, EventBridge scheduling, SNS alerting, Secrets Manager, CloudFront HTTPS proxy, Amplify hosting, and ALB load balancing
- **Voyage AI** — High-quality embeddings (voyage-3) and neural reranking (rerank-2) for the RAG diagnostic pipeline

The system predicts equipment failures from sensor data using scikit-learn models, provides RAG-based diagnostics over technical documentation with hybrid search and reranking, and streams real-time predictions via MongoDB change streams.

## Key Features

* **Real-Time Equipment Monitoring** — 6 sensor types with continuous data processing and instant failure prediction alerts via SNS
* **Hybrid Search RAG Pipeline** — Atlas Vector Search + Full-Text Search, Voyage AI reranking, Bedrock LLM completion
* **Split Architecture** — Separate API and stream processor services on ECS Fargate with independent scaling
* **ML Model Training** — Automated model training with best-model selection per target
* **PrivateLink Connectivity** — Secure MongoDB Atlas access without public IP exposure (when `atlas_create=true`)
* **Bedrock Guardrails** — Optional content filtering on LLM responses
* **Frontend Dashboard** — Dark-themed React UI with sparkline/gauge visualizations, configurable reranker and completion model, AI-powered diagnostics with markdown rendering

## Sensors

The system monitors 6 equipment health sensors:

| Sensor | Description | Health States |
|--------|-------------|---------------|
| `cooler_condition` | Cooling system thermal efficiency | Full efficiency → Reduced → Total failure |
| `valve_condition` | Hydraulic valve switching response | Optimal → Small lag → Severe lag → Total failure |
| `internal_pump_leakage` | Pump volumetric efficiency | No leakage → Weak → Severe |
| `hydraulic_accumulator` | Gas-charged accumulator pressure | Optimal (130 bar) → Slightly reduced → Severely reduced → Total failure |
| `stable_flag` | Overall system stability indicator | Stable → Unstable |
| `motor_power` | Electric drive motor efficiency | Full power → Slightly degraded → Severely degraded |

## Architecture

The system is split into independently deployable services:

| Service | Description | Scaling |
|---------|-------------|---------|
| **API** (`fastapi_mcp.py`) | FastAPI server with REST + MCP endpoints, behind ALB | Fixed 1 task |
| **Stream** (`stream.py`) | MongoDB change stream processor, writes predictions | Fixed 1 task |
| **Simulation** (`simulation.py`) | Injects sample sensor data via EventBridge (1/min) | Scheduled task |
| **Frontend** (`ui/`) | React SPA deployed via AWS Amplify | Managed |

For detailed architecture, see [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Quick Start

### One-Click AWS Deployment

```bash
cd deployment
# Set AWS credentials in Makefile or environment
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."   # if using temporary credentials
export AWS_REGION="us-east-1"

make deploy-with-public-ecr
```

This deploys: VPC, ECS Fargate cluster, ALB, CloudFront, Amplify frontend, S3, EventBridge, CloudWatch, SNS, Secrets Manager, and IAM roles. Optionally provisions a MongoDB Atlas cluster with PrivateLink when `atlas_create=true`.

**AWS Permissions Required:** The deploying IAM user/role needs access to ECS, EC2/VPC, ELB, S3, Secrets Manager, CloudWatch Logs, EventBridge, SNS, IAM, Amplify, and CloudFront. See [Deployment Guide](./docs/DEPLOYING.md#aws-iam-permissions) for the full list of managed policies or individual permissions.

### Local Development

```bash
# Set required environment variables
export MONGODB_URI="mongodb+srv://user:password@cluster.mongodb.net"
export VOYAGE_API_KEY="your-voyage-api-key"

# Backend
cd backend
pip install -r requirements.txt
python indexing.py            # Index documents + create search indexes (run first)
python generate_models.py    # Train ML models (6 datasets)
python fastapi_mcp.py        # Start API server (port 5001)
python stream.py             # Start change stream processor (separate terminal)
python simulation.py         # Inject sample sensor data (separate terminal)

# Frontend (set REACT_APP_* vars before starting)
cd ui
npm install
export REACT_APP_FASTAPI_HOST=127.0.0.1
export REACT_APP_FASTAPI_PORT=5001
npm start                    # Dev server on port 3001
```

### Docker

```bash
docker build -t predictive-maintenance .
docker run -e MONGODB_URI=... -e VOYAGE_API_KEY=... predictive-maintenance
```

## Configuration

All backend configuration is in `backend/config/config.yaml` with environment variable overrides.

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `VOYAGE_API_KEY` | Voyage AI API key | — |
| `EMBEDDING_MODEL` | Embedding model | `voyage/voyage-3` |
| `RERANKER_MODEL` | Reranker model | `voyage/rerank-2` |
| `BEDROCK_GUARDRAIL_ID` | Bedrock guardrail ID | — |
| `SNS_ALERT_TOPIC_ARN` | SNS topic for critical alerts | — |

For full configuration details, see [docs/CONFIGURATION.md](./docs/CONFIGURATION.md).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/models` | List available ML models |
| `GET` | `/api/sensors` | List sensor collections |
| `GET` | `/api/monitoring` | Get monitoring/prediction data |
| `POST` | `/api/predict` | Run prediction |
| `GET` | `/api/diagnose` | RAG-based diagnosis with hybrid search + reranking |
| `GET` | `/api/text_gen` | Text generation |
| `GET` | `/docs` | Interactive API docs (Swagger) |
| — | `/mcp/` | MCP (Model Context Protocol) endpoint |

## Documentation

- [Architecture](./docs/ARCHITECTURE.md)
- [Configuration](./docs/CONFIGURATION.md)
- [Local Quickstart](./docs/LOCAL_QUICKSTART.md)
- [Deployment](./docs/DEPLOYING.md)
- [Features & Usage](./docs/FEATURES_AND_USAGE.md)
- [Oil & Gas Developer Day](./docs/OilAndGas-DevDay.md)

## Workshop Assets

- [Oil & Gas Vector Search Lab](./notebooks/01_vector_search_oil_gas.ipynb)
- [Oil & Gas RAG Diagnostics Lab](./notebooks/02_rag_diagnostics_oil_gas.ipynb)
