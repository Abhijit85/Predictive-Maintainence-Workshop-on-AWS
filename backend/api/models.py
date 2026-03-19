"""Pydantic models for the Predictive Maintenance API"""

from pydantic import BaseModel, Field
from typing import List, Any, Optional


class PredictionRequest(BaseModel):
    """Request model for making predictions"""
    independent_variables: List[Any] = Field(..., description="Input features for prediction")
    dependent_variables: Optional[List[Any]] = Field(None, description="Known outcomes for validation (optional)")
    model_identifier: str = Field(..., description="Model name to use for prediction")


class PredictionResponse(BaseModel):
    """Response model for predictions"""
    encoded_prediction: int = Field(..., description="Encoded prediction value")
    model_used: str = Field(..., description="Model that was used for prediction")
    prediction: Optional[int] = Field(None, description="Decoded prediction value")
    dependent_variables: Optional[List[Any]] = Field(None, description="Dependent variables if provided")


class ModelListResponse(BaseModel):
    """Response model for listing available models"""
    models: List[str] = Field(..., description="List of available model names")
    count: int = Field(..., description="Number of available models")


class SensorListResponse(BaseModel):
    """Response model for listing sensor collections"""
    collections: List[str] = Field(..., description="List of sensor collection names")


class SourceInfo(BaseModel):
    """Information about a source document used in diagnosis"""
    file: str = Field("", description="Source file path")
    chunk: str = Field("", description="Relevant text chunk")
    search_score: float = Field(0, description="Search relevance score")
    rerank_score: Optional[float] = Field(None, description="Reranking relevance score")


class DiagnosisResponse(BaseModel):
    """Response model for technical diagnosis"""
    diagnosis: str = Field(..., description="AI-generated diagnosis and recommendations")
    sources: Optional[List[SourceInfo]] = Field(None, description="Source documents used for diagnosis")
    search_method: Optional[str] = Field(None, description="Search method used (vector, hybrid)")
    reranker: Optional[str] = Field(None, description="Reranker model used")
    embedding_model: Optional[str] = Field(None, description="Embedding model used")
    completion_model: Optional[str] = Field(None, description="Completion model used")


class TextGenerationResponse(BaseModel):
    """Response model for text generation"""
    answer: str = Field(..., description="AI-generated text response")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
