# Architecture

## Overview

The system follows a split-service architecture with independently deployable components communicating through MongoDB and an HTTP API. The frontend is served via AWS Amplify, API requests are proxied through CloudFront for HTTPS termination, and the backend runs on ECS Fargate behind an Application Load Balancer.

## Deployment Diagram

```
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │  Browser                                                                                │
 └────────────────────────────────────┬────────────────────────────────────────────────────┘
                                      │ HTTPS
                                      ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │  AWS Amplify  (*.amplifyapp.com)                                                        │
 │  ┌───────────────────────────────────────────────────────────────────────────────────┐   │
 │  │  Static Assets (HTML/JS/CSS)  ←── React 19 SPA build                             │   │
 │  ├───────────────────────────────────────────────────────────────────────────────────┤   │
 │  │  Proxy Rewrite Rules (server-side, status 200):                                   │   │
 │  │    /api/<*>  → https://CloudFront/api/<*>    (reverse proxy)                      │   │
 │  │    /health   → https://CloudFront/health     (reverse proxy)                      │   │
 │  │    /*        → /index.html                   (SPA fallback)                       │   │
 │  └──────────────────────────────────┬────────────────────────────────────────────────┘   │
 └─────────────────────────────────────┼───────────────────────────────────────────────────┘
                                       │ HTTPS (server-side proxy rewrite)
                                       ▼
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │  CloudFront Distribution  (*.cloudfront.net)                                            │
 │  Origin: ALB (HTTP, origin_protocol_policy = "http-only")                               │
 │  Caching: disabled (default_ttl = 0)                                                    │
 │  Purpose: HTTPS termination for Amplify proxy (Amplify requires HTTPS targets)          │
 └─────────────────────────────────────┬───────────────────────────────────────────────────┘
                                       │ HTTP (origin fetch)
                                       ▼
 ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
   VPC  10.0.0.0/16
 │                                                                                         │
   ┌─────────────────────────────────────────────────────────────────────────────────────┐
 │ │  Application Load Balancer  (internet-facing, port 80 + optional 443)               │ │
   │  ┌────────────────────────────┐  ┌────────────────────────────────────────────────┐ │
 │ │  │  SG: *-alb-sg              │  │  SG: *-alb-amp-sg                              │ │ │
   │  │  HTTP/HTTPS from           │  │  HTTP from Amplify proxy                       │ │
 │ │  │  allowed IPs prefix list   │  │  (CloudFront origin-facing IPs)                │ │ │
   │  │  (~32 CIDRs)              │  │  (~45 CIDRs)                                   │ │
 │ │  └────────────────────────────┘  └────────────────────────────────────────────────┘ │ │
   │  Health check: GET /health (HTTP, 30s interval)                                     │
 │ │  Target group: IP-based → ECS API tasks on port 5001                                │ │
   └──────────────────────────┬──────────────────────────────────────────────────────────┘
 │                            │                                                            │
      ┌───────────────────────┴───────────────────────┐
 │    │    Public Subnets  (10.0.4-6.0/24, 3 AZs)     │                                   │
      │    assign_public_ip = true (no NAT gateway)    │
 │    │                                                │                                   │
      │  ┌──────────────────────────────────────────┐  │
 │    │  │  ECS Fargate: API Service                │  │                                   │
      │  │  Container: predictive-maintenance-api   │  │
 │    │  │  Command:   python fastapi_mcp.py        │  │                                   │
      │  │  Port:      5001                         │  │
 │    │  │  Tasks:     1 (fixed, no autoscaling)    │  │                                   │
      │  │  Startup:   S3 sync → indexing → serve   │  │
 │    │  │                                          │  │         ┌──────────────────────┐   │
      │  │  Endpoints:                              │  │         │  Voyage AI (HTTPS)   │
 │    │  │    GET  /health                          │  │    ┌───▶│  Embeddings + Rerank │   │
      │  │    GET  /api/sensors                     │  │    │    └──────────────────────┘
 │    │  │    GET  /api/models                      │  │    │                               │
      │  │    GET  /api/monitoring                  ├──┼────┤
 │    │  │    POST /api/predict                     │  │    │    ┌──────────────────────┐   │
      │  │    GET  /api/diagnose ──────────────────▶├──┼────┤───▶│  AWS Bedrock (HTTPS) │
 │    │  │    GET  /api/text_gen                    │  │    │    │  LLM Completion      │   │
      │  │    GET  /docs (Swagger)                  │  │    │    │  + Guardrails         │
 │    │  │         /mcp/ (MCP)                      │  │    │    └──────────────────────┘   │
      │  └───────────────────┬──────────────────────┘  │    │
 │    │                      │                         │    │                               │
      │  ┌───────────────────┴──────────────────────┐  │    │
 │    │  │  ECS Fargate: Stream Service             │  │    │                               │
      │  │  Container: predictive-maintenance-stream│  │    │
 │    │  │  Command:   python stream.py             │  │    │                               │
      │  │  Tasks:     1 (fixed, no autoscaling)    │  │    │
 │    │  │  Startup:   S3 sync → indexing → watch   │  │    │                               │
      │  │                                          │  │    │
 │    │  │  Calls API at ALB:80 for predictions     ├──┼────┘                               │
      │  │  Publishes SNS alerts for critical state │  │
 │    │  │  Discovers collections once at startup   │  │                                    │
      │  └──────────────────────────────────────────┘  │
 │    │                                                │                                    │
      │  ┌──────────────────────────────────────────┐  │
 │    │  │  ECS Fargate: Simulation Task            │  │                                    │
      │  │  (one-shot, triggered by EventBridge)    │  │
 │    │  │  Command:   python simulation.py         │  │                                    │
      │  │  Reuses API task definition with         │  │
 │    │  │  command override                        │  │                                    │
      │  └──────────────────────────────────────────┘  │
 │    └────────────────────────────────────────────────┘                                    │
                                       │
 │    ┌────────────────────────────────┼────────────────────────────────────────────────┐   │
      │    Private Subnets  (10.0.1-3.0/24, 3 AZs)                                    │
 │    │    (used only when atlas_create=true)       │                                   │   │
      │                                             │                                   │
 │    │  ┌──────────────────────────────────────────┐│                                  │   │
      │  │  VPC Endpoint (PrivateLink)              ││                                  │
 │    │  │  SG: port 27017 from VPC CIDR            │├──────────────────────────┐       │   │
      │  │  Interface type, 3 subnet ENIs           ││                          │       │
 │    │  └──────────────────────────────────────────┘│                          │       │   │
      └─────────────────────────────────────────────┘                          │       │
 │                                                                              │          │
 └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ┘
                                       │                                        │
               ┌───────────────────────┘                                        │
               ▼                                                                ▼
 ┌──────────────────────────────┐                          ┌───────────────────────────────┐
 │  MongoDB Atlas               │                          │  MongoDB Atlas                │
 │  (public internet when       │◀── OR ──────────────────▶│  (PrivateLink when            │
 │   atlas_create=false)        │                          │   atlas_create=true)           │
 │                              │                          │                               │
 │  M10 Cluster (ReplicaSet)    │                          │  M10 Cluster (ReplicaSet)     │
 │  Region: US_EAST_1           │                          │  Region: US_EAST_1            │
 │  3 electable nodes           │                          │  3 electable nodes            │
 │                              │                          │                               │
 │  Databases:                  │                          │  VPC Endpoint Service          │
 │  ├── predictions             │                          │  connected to AWS VPC          │
 │  │   ├── *_input (6 sensor   │                          │  Endpoint above                │
 │  │   │    collections)       │                          └───────────────────────────────┘
 │  │   ├── *_output (6 sensor  │
 │  │   │    collections)       │
 │  │   ├── chunks (embeddings) │
 │  │   └── description (info)  │
 │  │                           │
 │  │  Indexes:                 │
 │  │   ├── Vector search index │
 │  │   └── Full-text search    │
 │  │        index              │
 │  │                           │
 │  │  Change Streams:          │
 │  │   └── Watched by stream   │
 │  │        processor on all   │
 │  │        6 *_input colls    │
 │  └───────────────────────────│
 └──────────────────────────────┘

 ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
   Supporting AWS Services
 │                                                                                         │
   ┌─────────────────────┐  ┌─────────────────────┐  ┌──────────────────────────────────┐
 │ │  EventBridge         │  │  S3 Bucket           │  │  Secrets Manager                 │ │
   │  Rule: rate(1 min)  │  │  Versioned, locked   │  │  Secret: *-secrets               │
 │ │  Target: ECS RunTask │  │  Contents:           │  │  Keys:                           │ │
   │  (simulation.py via │  │  ├── input/models/   │  │  ├── MONGODB_URI                 │
 │ │   command override)  │  │  ├── input/encoders/ │  │  └── VOYAGE_API_KEY              │ │
   │  IAM role for ECS   │  │  ├── input/datasets/ │  │  Injected into ECS containers    │
 │ │  RunTask + PassRole  │  │  ├── input/config/   │  │  as secrets (not env vars)       │ │
   └─────────────────────┘  │  ├── input/data/     │  └──────────────────────────────────┘
 │                           │  └── input/info/     │                                      │
   ┌─────────────────────┐  └─────────────────────┘  ┌──────────────────────────────────┐
 │ │  CloudWatch Logs     │                           │  SNS Topic                       │ │
   │  Log group:         │  ┌─────────────────────┐  │  Name: *-alerts                  │
 │ │  /ecs/<app-name>    │  │  IAM                 │  │  Protocol: email                 │ │
   │  Retention: 30 days │  │  Service policy:     │  │  Published by stream.py when     │
 │ │  Stream prefix: ecs │  │  ├── S3 (read/write) │  │  prediction is critical (red)    │ │
   │  Used by both API   │  │  ├── Bedrock (invoke)│  └──────────────────────────────────┘
 │ │  and Stream services │  │  ├── Secrets Mgr     │                                      │
   └─────────────────────┘  │  │   (get secret)    │  ┌──────────────────────────────────┐
 │                           │  ├── SNS (publish)   │  │  ECR (optional)                  │ │
                             │  ├── CloudWatch Logs │  │  Private repository when
 │                           │  └── ECS (describe)  │  │  app_use_public_ecr=false        │ │
                             └─────────────────────┘  │  Otherwise uses public ECR image  │
 │                                                     └──────────────────────────────────┘ │
 └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

## Services

### API Service (`fastapi_mcp.py`)

- FastAPI server exposing REST API and MCP endpoint
- Runs as a single ECS Fargate task in public subnets with `assign_public_ip = true`
- Behind Application Load Balancer with health checks on `/health`
- Reachable from the internet via: Amplify → CloudFront → ALB → ECS
- Handles: predictions, diagnosis (hybrid search + reranking), monitoring queries, text generation
- Secrets (`MONGODB_URI`, `VOYAGE_API_KEY`) injected from Secrets Manager, not environment variables

### Stream Processor (`stream.py`)

- Watches MongoDB change streams on all 6 sensor input collections
- When new sensor data arrives, calls the API service via ALB (HTTP port 80) for prediction
- Enriches results with description metadata and writes to output collections
- Publishes SNS alerts for critical predictions (color `#dc3545`)
- Runs as a single ECS Fargate task in public subnets (no ALB, outbound only)
- Discovers collections once at startup — must be restarted to pick up new sensor types

### Simulation (`simulation.py`)

- Inserts random historical sensor readings into MongoDB input collections
- Triggered by EventBridge rule every 1 minute as a one-shot ECS task
- Reuses the API service task definition with a command override (`python simulation.py`)
- Automatically creates missing MongoDB collections from dataset filenames

### Frontend (`ui/`)

- React 19 + TypeScript + React Router v7 + Bootstrap 5
- Deployed via AWS Amplify with proxy rewrite rules for API routing
- Built with **no `REACT_APP_FASTAPI_HOST`** — all API calls use relative paths (`/api/*`)
- Amplify proxy rules forward `/api/*` and `/health` through CloudFront to the ALB
- Configurable reranker and completion model selection (embedding model fixed at indexing time)
- Displays predictions, diagnostics, sparkline/gauge visualizations, and pipeline details
- Healthy predictions (green) skip AI diagnosis automatically

## Request Flow

### User → Dashboard (static assets)

```
Browser → Amplify (HTTPS) → React SPA served directly
```

### User → API (predictions, diagnosis, monitoring)

```
Browser → Amplify (HTTPS) → /api/* proxy rewrite → CloudFront (HTTPS) → ALB (HTTP :80) → ECS API (:5001)
```

Amplify requires HTTPS targets in proxy rewrite rules. Since the ALB only serves HTTP (unless an ACM certificate is provided), a CloudFront distribution sits between Amplify and the ALB to provide the HTTPS termination. CloudFront connects to the ALB over HTTP (`origin_protocol_policy = "http-only"`). All caching is disabled (`default_ttl = 0`) so every API request reaches the backend.

### Sensor data → Prediction → Alert

```
EventBridge (1/min) → ECS: simulation.py → MongoDB *_input collection
                                                  │
                                          change stream trigger
                                                  │
                                                  ▼
                                    ECS: stream.py detects insert
                                                  │
                                    HTTP POST → ALB → ECS API /api/predict
                                                  │
                                                  ▼
                                    Prediction written to *_output collection
                                                  │
                                          (if critical prediction)
                                                  │
                                                  ▼
                                    SNS → email notification
```

### RAG Diagnosis Pipeline

```
User question → /api/diagnose
     │
     ├── 1. Voyage AI: generate query embedding
     │
     ├── 2. MongoDB Atlas: hybrid search
     │      ├── Vector search (cosine similarity, top 20)
     │      └── Full-text search ($unionWith, top 20)
     │      └── Deduplicated + merged results
     │
     ├── 3. Voyage AI: rerank candidates (top 5 of 20)
     │
     ├── 4. AWS Bedrock: LLM completion with context
     │      └── Optional guardrails (BEDROCK_GUARDRAIL_ID)
     │
     └── 5. Response with answer + source documents
```

## Sensors

The system monitors 6 equipment health sensors from a hydraulic test rig:

| Sensor | Model Type | Health States |
|--------|-----------|---------------|
| `cooler_condition` | Logistic Regression | Full efficiency (100) → Reduced (20) → Total failure (3) |
| `valve_condition` | Random Forest | Optimal (100) → Small lag (90) → Severe lag (80) → Total failure (73) |
| `internal_pump_leakage` | Logistic Regression | No leakage (0) → Weak (1) → Severe (2) |
| `hydraulic_accumulator` | Random Forest | Optimal (130) → Slightly reduced (115) → Severely reduced (100) → Total failure (90) |
| `stable_flag` | Random Forest | Stable (1) → Unstable (0) |
| `motor_power` | Random Forest | Full power (2) → Slightly degraded (1) → Severely degraded (0) |

All sensors share the same 17 input features (PS1–PS6, EPS1, FS1–FS2, TS1–TS4, VS1, CE, CP, SE).

## Data Flow

1. **Training**: 6 CSV datasets → `generate_models.py` → pickle files (models/ + encoders/) → S3 sync
2. **Indexing**: Documents → `DocumentChunker` → Voyage AI embeddings → MongoDB (vector search index + full-text search index). Also upserts `info.csv` metadata (description/color/icon for each prediction state).
3. **Simulation**: EventBridge (1/min) → ECS one-shot task → `simulation.py` → random sensor doc inserted to MongoDB input collection (creates missing collections automatically)
4. **Prediction**: New sensor doc → `stream.py` change stream → API `/api/predict` (via ALB) → enriched prediction written to output collection
5. **Alerting**: Critical prediction (red) → `stream.py` → SNS topic → email notification
6. **Diagnosis**: User query → hybrid search (vector + full-text) → Voyage AI reranking (top 5 of 20) → Bedrock LLM completion → response with sources

## ECS Startup Sequence

The `entrypoint.sh` script handles startup order for both API and Stream containers:

```
1. S3 Sync (ENV=ecs)          — aws s3 sync models/ and encoders/ from S3 bucket
2. Indexing (INDEXING=true)    — python indexing.py (upserts info, creates search indexes)
3. Model Training (optional)  — python generate_models.py → sync back to S3
4. CMD                        — python fastapi_mcp.py (API) or python stream.py (Stream)
```

## AWS Infrastructure

| Resource | Terraform File | Purpose |
|----------|---------------|---------|
| VPC | `vpc.tf` | 10.0.0.0/16 with 3 public + 3 private subnets across 3 AZs |
| ECS Cluster | `ecs_api.tf` | Fargate cluster with FARGATE + FARGATE_SPOT capacity providers |
| API Service | `ecs_api.tf` | ECS service (1 task) behind ALB, port 5001 |
| Stream Service | `ecs_stream.tf` | ECS service (1 task), outbound only, no ALB |
| ALB | `alb.tf` | Internet-facing, HTTP listener (+ optional HTTPS with ACM cert) |
| ALB Security Groups | `alb.tf` | Two SGs: allowed IPs prefix list + CloudFront origin-facing IPs |
| CloudFront | `cloudfront.tf` | HTTPS proxy from Amplify to ALB (Amplify requires HTTPS targets) |
| Amplify | `amplify.tf` | Frontend hosting with `/api/*` and `/health` proxy rules through CloudFront |
| EventBridge | `eventbridge.tf` | Scheduled simulation every 1 minute (ECS RunTask) |
| S3 | `s3.tf` | Versioned bucket for models, encoders, datasets, config |
| Secrets Manager | `secrets_manager.tf` | MONGODB_URI + VOYAGE_API_KEY |
| CloudWatch | `cloudwatch.tf` | Log group `/ecs/<app-name>` with 30-day retention |
| SNS | `sns.tf` | Alert topic with optional email subscription |
| Atlas Cluster | `mongo_atlas.tf` | M10 ReplicaSet, 3 nodes, US_EAST_1 (when `atlas_create=true`) |
| PrivateLink | `privatelink.tf` | VPC endpoint to Atlas (when `atlas_create=true`) |
| IAM | `iam.tf` | Service policy: S3, Bedrock, Secrets Manager, SNS, CloudWatch, ECS |
| ECR | `ecr.tf` | Private Docker repository (when `app_use_public_ecr=false`) |

## Network Design

### Public Subnets (10.0.4-6.0/24)

All ECS services run in public subnets with `assign_public_ip = true`. This eliminates the need for a NAT gateway while still allowing outbound internet access for:
- Pulling Docker images from ECR
- Connecting to MongoDB Atlas (when not using PrivateLink)
- Calling Voyage AI and AWS Bedrock APIs

### Private Subnets (10.0.1-3.0/24)

Used exclusively for PrivateLink VPC endpoints when `atlas_create=true`. The VPC endpoint creates an elastic network interface (ENI) in each private subnet, providing a private path to MongoDB Atlas without traversing the public internet.

### Security Groups

The ALB uses **two security groups** to stay within the default 60-rules-per-SG limit:

| Security Group | Purpose | Rule Count |
|---------------|---------|------------|
| `*-alb-sg` | HTTP/HTTPS from allowed IPs (managed prefix list) | ~32 CIDRs |
| `*-alb-amp-sg` | HTTP from Amplify proxy (CloudFront origin-facing IPs, AWS-managed prefix list) | ~45 CIDRs |

AWS counts each prefix list entry as a separate rule. The combined ~77 entries would exceed a single SG's 60-rule limit.

### DNS & HTTPS

- **Amplify**: Serves on `https://main.<app-id>.amplifyapp.com` with AWS-managed TLS
- **CloudFront**: Serves on `https://<distribution-id>.cloudfront.net` with AWS-managed TLS. Proxies to ALB over HTTP.
- **ALB**: HTTP only by default. Set `acm_certificate_arn` to enable HTTPS (port 443)

## Security

- **PrivateLink**: MongoDB Atlas accessed via AWS PrivateLink when `atlas_create=true` (otherwise public internet)
- **Secrets Manager**: MONGODB_URI and VOYAGE_API_KEY stored as secrets, injected into ECS containers via `valueFrom` (not plaintext environment variables)
- **Bedrock Guardrails**: Optional content filtering on LLM responses (`BEDROCK_GUARDRAIL_ID`)
- **IAM**: Scoped service policy granting only S3, Bedrock, Secrets Manager, SNS, CloudWatch, and ECS describe permissions
- **ALB Access Control**: Configurable IP allowlist via managed prefix list (default: MongoDB office CIDRs)
- **CloudFront Proxy Access**: ALB accepts traffic from CloudFront origin-facing IP ranges via AWS-managed prefix list

## Backend Structure

```
backend/
  entrypoint.sh               # Startup sequence: S3 sync → indexing → models → CMD
  fastapi_mcp.py              # API server (REST + MCP)
  stream.py                   # MongoDB change stream processor
  generate_models.py          # ML model training
  indexing.py                 # Document chunking + embedding + search index creation
  simulation.py               # One-shot sensor data simulation
  config/
    config.yaml               # Central configuration (env var substitution)
    config_loader.py          # YAML + env var config classes
  core/
    services.py               # PredictionService (prediction, hybrid search, reranking, diagnosis)
  api/
    models.py                 # Pydantic request/response models
  utils/
    llm_utils.py              # LiteLLM wrappers (completion, embeddings, reranking)
    utils.py                  # Model/encoder/scaler loading
  data_processing/
    DocumentChunker.py        # PDF/DOCX/TXT/HTML document chunking
  models/                     # Trained model pickle files (1 per sensor)
  encoders/                   # Label encoder and scaler pickle files (2 per sensor)
  datasets/                   # Training CSV files (6 sensors)
```
