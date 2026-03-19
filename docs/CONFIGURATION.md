# Configuration

## Configuration File

All backend configuration flows through `backend/config/config.yaml`. Environment variables override YAML values using `${VAR_NAME:-default}` syntax.

## Environment Variables

### Core

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB Atlas connection string | `mongodb://localhost:27017` |
| `MONGODB_NAME` | Output database name | `predictions` |
| `MONGODB_COLLECTION_INPUT` | Input collection name | `predictions_input` |
| `MONGODB_COLLECTION_OUTPUT` | Output collection name | `predictions_output` |
| `MONGODB_COLLECTION_CHUNKS` | Chunks collection name | `chunks` |
| `MONGODB_COLLECTION_INFO` | Info/description collection name | `description` |

### Embeddings & Reranking (Voyage AI)

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDING_MODEL` | Embedding model identifier | `voyage/voyage-3` |
| `RERANKER_MODEL` | Reranker model identifier | `voyage/rerank-2` |
| `VOYAGE_API_KEY` | Voyage AI API key | — |

### AWS Services

| Variable | Description | Default |
|----------|-------------|---------|
| `BEDROCK_GUARDRAIL_ID` | Bedrock guardrail identifier | — |
| `BEDROCK_GUARDRAIL_VERSION` | Bedrock guardrail version | — |
| `SNS_ALERT_TOPIC_ARN` | SNS topic ARN for critical alerts | — |
| `BUCKET` | S3 bucket for model storage | — |
| `ENV` | Deployment environment (`ecs` or `local`) | `local` |

### Server

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_FASTAPI_HOST` | FastAPI server host | `127.0.0.1` |
| `REACT_APP_FASTAPI_PORT` | FastAPI server port | `5001` |
| `FASTAPI_RELOAD` | Enable hot reload | `false` |

### Startup Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `INDEXING` | Run document indexing on startup | `false` |
| `GENERATE_MODELS` | Train ML models on startup | `false` |
| `SIMULATE` | (Deprecated — simulation now via EventBridge) | — |

## Configuration Priority

1. Environment variables (highest priority)
2. `config.yaml` values
3. Default values in code

## Terraform Variables

Additional variables for deployment via Terraform:

| Variable | Description |
|----------|-------------|
| `voyage_api_key` | Voyage AI API key (stored in Secrets Manager) |
| `acm_certificate_arn` | ACM certificate for HTTPS on ALB |
| `alert_email` | Email for SNS alert subscriptions |
| `atlas_org_id` | MongoDB Atlas organization ID |
| `atlas_public_key` | Atlas API public key |
| `atlas_private_key` | Atlas API private key |
| `atlas_password` | Atlas admin user password |
