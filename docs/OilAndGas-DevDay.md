# Oil & Gas Developer Day

This guide turns the predictive-maintenance application in this repository into a hands-on workshop focused on MongoDB Atlas Vector Search, hybrid retrieval, and RAG diagnostics for Oil & Gas operations.

## Audience

- Developers building AI-powered operations tools
- Solutions architects running technical workshops
- Field engineers and platform teams evaluating predictive maintenance workflows

## Workshop Outcomes

By the end of the day, attendees should be able to:

- run the predictive-maintenance stack locally
- explain how MongoDB Atlas serves as both the operational store and the vector store
- inspect and modify the document indexing flow used by the app
- execute semantic and hybrid search over maintenance manuals and SOPs
- build a telemetry-aware RAG diagnostic workflow in a notebook
- connect the notebook flow back to the running FastAPI and React application

## Agenda

### Session 1: Architecture and Scenario Setup

Duration: 30-45 minutes

- Introduce the Oil & Gas scenario: compressor trains, pumps, hydraulic systems, and safety procedures
- Walk through [Architecture](./ARCHITECTURE.md)
- Explain the three core layers:
  - sensor-driven predictive maintenance
  - Atlas Vector Search plus full-text search
  - LLM-based diagnostic generation

### Lab 1: Run the Application Locally

Duration: 60-75 minutes

1. Set required environment variables:

```bash
export MONGODB_URI="mongodb+srv://user:password@cluster.mongodb.net"
export VOYAGE_API_KEY="your-voyage-api-key"
```

2. Start the backend services:

```bash
cd backend
pip install -r requirements.txt
python indexing.py
python generate_models.py
python fastapi_mcp.py
python stream.py
python simulation.py
```

3. Start the frontend:

```bash
cd ui
npm install
export REACT_APP_FASTAPI_HOST=127.0.0.1
export REACT_APP_FASTAPI_PORT=5001
npm start
```

Expected outcome:

- live dashboard
- simulated sensor data
- output predictions written by the stream processor
- diagnostic endpoint available at `/api/diagnose`

### Lab 2: Vector Search on Oil & Gas Maintenance Content

Duration: 75-90 minutes

Use [notebooks/01_vector_search_oil_gas.ipynb](../notebooks/01_vector_search_oil_gas.ipynb).

Focus areas:

- inspect the raw maintenance corpus
- chunk documents the same way as `backend/indexing.py`
- generate Voyage embeddings
- create Atlas Vector Search and full-text search indexes
- run semantic and hybrid retrieval queries over maintenance documentation

Suggested prompts:

- "What is the recommended response when compressor discharge pressure rises rapidly?"
- "Which procedure applies when accumulator pressure drops below the normal operating band?"
- "What maintenance action is recommended for severe internal pump leakage?"

### Lab 3: RAG Diagnostics for Oil & Gas Incidents

Duration: 75-90 minutes

Use [notebooks/02_rag_diagnostics_oil_gas.ipynb](../notebooks/02_rag_diagnostics_oil_gas.ipynb).

Focus areas:

- load recent telemetry from MongoDB
- construct a realistic incident narrative
- retrieve relevant manuals and SOPs with hybrid search
- rerank candidates with Voyage rerank
- build a safety-first prompt for the LLM
- compare the notebook pipeline with the production `/api/diagnose` endpoint

Suggested incident:

`Accumulator pressure dropped from 130 bar to 95 bar while valve lag increased and motor efficiency trended down over the last 10 minutes.`

### Wrap-Up

Duration: 30 minutes

- connect notebook experiments back to the production API flow
- highlight where attendees can customize the corpus, prompts, and alerting
- outline next steps for production hardening and domain adaptation

## Mapping the Existing Sensors to Oil & Gas Concepts

The workshop can keep the current model targets while presenting them with Oil & Gas terminology:

| Existing Sensor | Oil & Gas Framing |
| --- | --- |
| `cooler_condition` | Compressor or skid cooling efficiency |
| `valve_condition` | Hydraulic valve actuation lag |
| `internal_pump_leakage` | Pump or ESP leakage severity |
| `hydraulic_accumulator` | Accumulator charge pressure health |
| `stable_flag` | Asset stability or control-loop stability |
| `motor_power` | Drive motor efficiency |

## Recommended Corpus Updates

To make the workshop feel domain-specific, replace or augment the current documents under `backend/data_processing/data` with:

- compressor maintenance manuals
- pump maintenance and troubleshooting guides
- hydraulic safety operating procedures
- incident summaries or root-cause analyses

The indexing flow does not need to change as long as the files remain in a supported format such as `.pdf`, `.docx`, `.txt`, or `.html`.

## Notebook Design Principles

The notebooks in `notebooks/` intentionally mirror the production code:

- `backend/indexing.py` for chunking, embeddings, and Atlas search index creation
- `backend/core/services.py` for vector search, hybrid search, and reranking
- `backend/utils/llm_utils.py` for embeddings, reranking, and text generation

This keeps the workshop material aligned with the actual application rather than introducing parallel demo logic.

## Presenter Notes

- Keep the first run local to reduce workshop setup friction
- Treat the notebooks as the teaching surface and the app as the validation surface
- Emphasize that Atlas is handling operational telemetry, search, and vector retrieval in one platform
- Use a safety-first diagnostic prompt for Oil & Gas scenarios and remind attendees that outputs are advisory, not operational authority

