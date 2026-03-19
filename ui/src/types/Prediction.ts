export interface Prediction {
  // Prediction results
  encoded_prediction: number;
  model_used: string;
  prediction?: number;

  // Additional info
  description: string;
  color: string;
  icon: string;
  explanation?: string;

  // Metadata
  timestamp?: string;
  datetime?: string;
  _id?: string;

  // Pipeline metadata (from diagnosis)
  search_method?: string;
  reranker?: string;
  embedding_model?: string;
  completion_model?: string;
  sources?: Array<{
    file: string;
    chunk: string;
    search_score: number;
    rerank_score?: number;
  }>;

  // Sensors
  [key: string]: any;
}

export interface PredictionPanel {
  id: string;
  title: string;
  field: keyof Prediction;
  color: string;
  icon: string;
}
