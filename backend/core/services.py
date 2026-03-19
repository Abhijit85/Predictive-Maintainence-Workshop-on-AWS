"""Business logic services for Predictive Maintenance API"""

import logging
import numpy as np
from fastapi import HTTPException
from typing import List, Any, Optional, Dict
from pymongo.collection import Collection
from pymongo.database import Database
from bson import ObjectId

from utils.utils import load_model, validate_input_data, load_encoder, load_scaler, model_folder, extensions, model_prefixes
from utils.llm_utils import text_completion, generate_embeddings, reranking


class PredictionService:
    """Service class for prediction operations"""

    def __init__(self, client, input_db: Database, output_db: Database, chunks_col: Collection,
                 info_col: Collection, embedding_model: str, reranker_model: str = "",
                 guardrail_id: str = "", guardrail_version: str = ""):
        self.client = client
        self.input_db = input_db
        self.output_db = output_db
        self.chunks_col = chunks_col
        self.info_col = info_col
        self.embedding_model = embedding_model
        self.reranker_model = reranker_model
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version

    def make_prediction(self, independent_variables: List[Any], model_identifier: str,
                       dependent_variables: Optional[List[Any]] = None) -> Dict[str, Any]:
        """Make predictions using trained machine learning models"""
        try:
            data = {
                "independent_variables": independent_variables,
                "model_identifier": model_identifier
            }
            if dependent_variables:
                data["dependent_variables"] = dependent_variables

            is_valid, error_message = validate_input_data(data)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_message)

            model, error = load_model(model_identifier)
            if model is None:
                raise HTTPException(status_code=404, detail=error)

            if isinstance(independent_variables[0], (int, float)):
                X = np.array(independent_variables).reshape(1, -1)
            else:
                X = np.array(independent_variables)

            scaler, error = load_scaler(model_identifier.replace(model_prefixes[0], '').replace(model_prefixes[1], ''))
            if scaler is not None:
                X = scaler.transform(X)
            else:
                logging.warning(f"Using raw input data, error: {error}")

            prediction = int(model.predict(X)[0])

            response = {
                'encoded_prediction': prediction,
                'model_used': model_identifier
            }

            encoder, error = load_encoder(model_identifier.replace(model_prefixes[0], '').replace(model_prefixes[1], ''))
            if encoder is not None:
                response['prediction'] = int(encoder.inverse_transform([prediction])[0])

            if dependent_variables is not None:
                response['dependent_variables'] = dependent_variables

            logging.info("Successfully obtained prediction")
            return response

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    def list_models(self) -> Dict[str, Any]:
        """List all available trained models"""
        try:
            from pathlib import Path
            folder = Path(model_folder)
            if not folder.exists():
                return {
                    'models': [],
                    'message': f'Models directory "{model_folder}" does not exist'
                }

            model_files = []
            for file_path in folder.iterdir():
                if file_path.suffix.lower() in extensions:
                    model_files.append(file_path.stem)

            return {
                'models': sorted(model_files),
                'count': len(model_files)
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")

    def vector_search(self, collection: Collection, model: str, query: str, limit: int = 5) -> List[Dict]:
        """Vector search function matching original API"""
        embeddings = generate_embeddings(model, query)

        pipeline = [
            {
                "$vectorSearch": {
                    "index": "embeddings",
                    "path": "embeddings",
                    "queryVector": embeddings,
                    "numCandidates": 100,
                    "limit": limit
                }
            },
            {
                "$addFields": {
                    "search_score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        return list(collection.aggregate(pipeline))

    def hybrid_search(self, collection: Collection, model: str, query: str, limit: int = 20) -> List[Dict]:
        """Hybrid search combining Atlas Vector Search and Full-Text Search via $unionWith."""
        embeddings = generate_embeddings(model, query)

        pipeline = [
            # Vector search stage
            {
                "$vectorSearch": {
                    "index": "embeddings",
                    "path": "embeddings",
                    "queryVector": embeddings,
                    "numCandidates": 100,
                    "limit": limit
                }
            },
            {
                "$addFields": {
                    "search_score": {"$meta": "vectorSearchScore"},
                    "search_type": "vector"
                }
            },
            {
                "$project": {
                    "embeddings": 0
                }
            },
            # Merge with full-text search results
            {
                "$unionWith": {
                    "coll": collection.name,
                    "pipeline": [
                        {
                            "$search": {
                                "index": "text_search",
                                "text": {
                                    "query": query,
                                    "path": "chunk"
                                }
                            }
                        },
                        {
                            "$addFields": {
                                "search_score": {"$meta": "searchScore"},
                                "search_type": "text"
                            }
                        },
                        {
                            "$project": {
                                "embeddings": 0
                            }
                        },
                        {"$limit": limit}
                    ]
                }
            },
            # Deduplicate by _id, keeping highest score
            {
                "$group": {
                    "_id": "$_id",
                    "chunk": {"$first": "$chunk"},
                    "file": {"$first": "$file"},
                    "search_score": {"$max": "$search_score"},
                    "search_type": {"$first": "$search_type"}
                }
            },
            {"$sort": {"search_score": -1}},
            {"$limit": limit}
        ]

        return list(collection.aggregate(pipeline))

    def diagnose_issue(self, issue: str, completion_model: str = "",
                      embeddings_model: Optional[str] = None,
                      reranker: Optional[str] = None) -> Dict[str, Any]:
        """Diagnose technical issues using AI with hybrid search and reranking"""
        try:
            if not issue:
                raise HTTPException(status_code=400, detail="Issue description is required")

            if embeddings_model is None:
                embeddings_model = self.embedding_model

            if reranker is None:
                reranker = self.reranker_model

            completion_model = completion_model.replace("\"", "").replace("'", "")
            embeddings_model = embeddings_model.replace("\"", "").replace("'", "")

            # Use hybrid search to retrieve candidates (20 docs)
            search_method = "hybrid"
            try:
                results = self.hybrid_search(self.chunks_col, embeddings_model, issue, limit=20)
            except Exception as e:
                logging.warning(f"Hybrid search failed, falling back to vector search: {e}")
                results = self.vector_search(self.chunks_col, embeddings_model, issue, limit=20)
                search_method = "vector"

            # Rerank results if a reranker is configured
            sources = []
            if reranker and reranker.lower() not in ("", "no rerank", "none"):
                try:
                    documents = [r.get("chunk", "") for r in results]
                    rerank_response = reranking(reranker, issue, documents, top_n=5)

                    # Build reranked context from top 5
                    reranked_results = []
                    for item in rerank_response.results:
                        idx = item.index
                        if idx < len(results):
                            result = results[idx]
                            result["rerank_score"] = item.relevance_score
                            reranked_results.append(result)

                    results = reranked_results
                except Exception as e:
                    logging.warning(f"Reranking failed, using raw search results: {e}")
                    results = results[:5]
            else:
                reranker = None
                results = results[:5]

            # Build context and sources
            context = ""
            for chunk in results:
                chunk_text = chunk.get("chunk", "")
                context += f"- {chunk_text}\n"
                sources.append({
                    "file": chunk.get("file", "unknown"),
                    "chunk": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                    "search_score": chunk.get("search_score", 0),
                    "rerank_score": chunk.get("rerank_score")
                })

            prompt = f"You are a technical assistant. Based on the contexts below from provided manuals, answer how to solve the following Issue **{issue}**\n\nCONTEXT:\n{context}\n\nAnswer:"

            answer = text_completion(
                completion_model, prompt,
                guardrail_id=self.guardrail_id if self.guardrail_id else None,
                guardrail_version=self.guardrail_version if self.guardrail_version else None
            )

            return {
                "diagnosis": answer,
                "sources": sources,
                "search_method": search_method,
                "reranker": reranker,
                "embedding_model": embeddings_model,
                "completion_model": completion_model
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")

    def get_monitoring_data(self, sensor: str, limit: int = 10,
                           exclude_id: Optional[str] = None) -> Any:
        """Get monitoring data for a specific sensor"""
        try:
            if not sensor:
                raise HTTPException(status_code=400, detail="Missing 'sensor' parameter")

            if self.client is None:
                raise HTTPException(status_code=500, detail="Database connection not available")

            try:
                self.client.admin.command('ping')
                collection = self.output_db[sensor]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to access collection '{sensor}': {str(e)}")

            query = {}
            if exclude_id:
                try:
                    query["_id"] = {"$ne": ObjectId(exclude_id)}
                except Exception:
                    pass

            cursor = collection.find(query).sort("datetime", -1).limit(limit)
            response = list(cursor)

            for doc in response:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            if limit == 1 and response:
                return response[0]
            return response

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get monitoring data: {str(e)}")

    def generate_text(self, text: str, model: str = "") -> Dict[str, str]:
        """Generate text using AI models"""
        try:
            model = model.replace("\"", "").replace("'", "")
            text = text.replace("\"", "").replace("'", "")

            answer = text_completion(model, text)
            return {"answer": answer}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")

    def list_sensor_collections(self) -> Dict[str, List[str]]:
        """List all sensor collections in the predictions database"""
        try:
            if self.client is None:
                raise HTTPException(status_code=500, detail="Database connection not available")
            self.client.admin.command('ping')
            collections = self.output_db.list_collection_names()
            return {"collections": collections}
        except Exception as e:
            logging.error(f"Error listing sensor collections: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error listing sensor collections: {str(e)}")
