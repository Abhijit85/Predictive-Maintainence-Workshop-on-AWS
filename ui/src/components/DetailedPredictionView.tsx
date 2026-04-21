import React, { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prediction } from '../types/Prediction';
import { getDiagnoseData } from '../api/predictions';
import { useUserContext } from '../App';
import { parseUTCDatetime } from '../utils/datetime';
import { getSensorMetadata } from '../config/sensorMetadata';
import './DetailedPredictionView.css';

/** Convert a string to Title Case */
const toTitleCase = (s: string): string =>
  s.replace(/\b\w/g, c => c.toUpperCase());

interface DetailedPredictionViewProps {
  prediction: Prediction | null;
  panelTitle: string;
  isExpanded: boolean;
  onClose: () => void;
  onViewEvents?: () => void;
}

interface PipelineDetails {
  embedding_model?: string;
  search_method?: string;
  reranker?: string;
  completion_model?: string;
  sources?: Array<{
    file: string;
    chunk: string;
    search_score: number;
    rerank_score?: number;
  }>;
}

/** Extract sensor type key from model_used string, e.g. "Random_Forest-cooler_condition" → "cooler_condition" */
const getSensorKey = (modelUsed: string): string => {
  const parts = modelUsed.split('-');
  return parts.length > 1 ? parts.slice(1).join('-') : modelUsed;
};

const ChevronIcon: React.FC<{ open: boolean }> = ({ open }) => (
  <svg
    className={`chevron-icon${open ? ' open' : ''}`}
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <polyline points="9 18 15 12 9 6" />
  </svg>
);

const DetailedPredictionView: React.FC<DetailedPredictionViewProps> = ({
  prediction,
  panelTitle,
  isExpanded,
  onClose,
  onViewEvents
}) => {
  const [diagnoseResult, setDiagnoseResult] = useState<string | null>(null);
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [pipelineDetails, setPipelineDetails] = useState<PipelineDetails | null>(null);
  const [showPipeline, setShowPipeline] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const { selectedCompletion, selectedReRanker } = useUserContext();

  const excludedFields = ['encoded_prediction', 'model_used', 'prediction', 'description', 'color', 'icon', 'explanation', 'timestamp', 'datetime', '_id']
  const availableFields = Object.keys(prediction || {}).filter(
    key => !excludedFields.includes(key)
  );

  const healthyColors = ['#00ED64', '#28a745', '#00ed64'];
  const isHealthy = prediction ? healthyColors.includes(prediction.color?.toLowerCase()) : false;

  const handleDiagnose = useCallback(async () => {
    if (!prediction) return;

    setIsDiagnosing(true);
    setDiagnoseResult(null);
    setPipelineDetails(null);

    try {
      var issue = `Given Value: ${prediction.prediction} -- Description: ${prediction.description} -- Type: ${prediction.model_used}`;
      const result = await getDiagnoseData({
        issue: issue,
        model: selectedCompletion,
        reranker: selectedReRanker,
      });

      setDiagnoseResult(result.analysis || result.diagnosis || JSON.stringify(result));
      setPipelineDetails({
        embedding_model: result.embedding_model,
        search_method: result.search_method,
        reranker: result.reranker,
        completion_model: result.completion_model,
        sources: result.sources
      });
    } catch (error) {
      console.error('Error during diagnosis:', error);
      setDiagnoseResult('Error: Unable to perform technical analysis at this time.');
    } finally {
      setIsDiagnosing(false);
    }
  }, [prediction, selectedCompletion, selectedReRanker]);

  useEffect(() => {
    if (isExpanded && prediction && !isHealthy) {
      handleDiagnose();
    }
  }, [isExpanded, prediction]);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      onClose();
    }, 250);
  };

  if (!isExpanded || !prediction) return null;

  return (
    <div
      className={`detailed-view-overlay${isClosing ? ' closing' : ''}`}
      role="dialog"
      aria-modal="true"
      aria-labelledby="detailed-view-title"
    >
      <div className="detailed-view-container">
        <div className="detailed-view-header">
          <div className="header-content">
            <h2 id="detailed-view-title" className="detailed-title" style={{ color: prediction.color }}>{toTitleCase(prediction.description)}</h2>
          </div>
          <button className="close-button" onClick={handleClose} aria-label="Close dialog">
            <span>&times;</span>
          </button>
        </div>

        <div className="detailed-view-body">
          <div className="main-content">

            {(() => {
              const metadata = getSensorMetadata(getSensorKey(prediction.model_used));
              if (!metadata) return null;
              const about = metadata.about;
              return (
                <div className="about-section">
                  <h3>About This Signal</h3>
                  <div className="about-content">
                    <div className="about-detail">
                      <h4>Asset Context</h4>
                      <p>{metadata.title} | {metadata.assetClass}</p>
                    </div>

                    <p className="about-summary">{about.summary}</p>

                    <div className="about-detail">
                      <h4>What It Measures</h4>
                      <p>{about.measures}</p>
                    </div>

                    <div className="about-detail">
                      <h4>Key Readings</h4>
                      <ul>
                        {about.readings.map((r, i) => <li key={i}>{r}</li>)}
                      </ul>
                    </div>

                    <div className="about-detail">
                      <h4>Health States</h4>
                      <ul className="state-list">
                        {about.states.map((s, i) => <li key={i}>{s}</li>)}
                      </ul>
                    </div>
                  </div>
                </div>
              );
            })()}

            <div className="explanation-section">
              <h3>Technical Analysis</h3>
              <div className="explanation-content">
                {isHealthy ? (
                  <div className="healthy-status">
                    <p style={{ color: prediction.color, fontWeight: 'bold', fontSize: '1.1em' }}>
                      Equipment is operating normally.
                    </p>
                    <p style={{ color: 'var(--color-text-muted)' }}>
                      Diagnosis skipped — prediction indicates healthy state
                      ({prediction.description}). AI-powered analysis is only triggered
                      for degraded or critical conditions.
                    </p>
                  </div>
                ) : isDiagnosing ? (
                  <div className="loading-analysis">
                    <div className="loading-spinner"></div>
                    <p>Performing AI analysis...</p>
                  </div>
                ) : diagnoseResult ? (
                  <div className="ai-analysis">
                    <ReactMarkdown>{diagnoseResult}</ReactMarkdown>
                  </div>
                ) : (
                  'No technical analysis available for this prediction.'
                )}
              </div>
            </div>

            {pipelineDetails && (
              <div className="pipeline-section">
                <h3
                  className="pipeline-toggle"
                  onClick={() => setShowPipeline(!showPipeline)}
                  style={{ cursor: 'pointer' }}
                >
                  <ChevronIcon open={showPipeline} />
                  Pipeline Details
                </h3>
                {showPipeline && (
                  <div className="pipeline-content">
                    <div className="pipeline-info">
                      {pipelineDetails.embedding_model && (
                        <div className="info-item">
                          <span className="label">Embedding Model:</span>
                          <span className="value">{pipelineDetails.embedding_model}</span>
                        </div>
                      )}
                      {pipelineDetails.search_method && (
                        <div className="info-item">
                          <span className="label">Search Method:</span>
                          <span className="value">{pipelineDetails.search_method}</span>
                        </div>
                      )}
                      {pipelineDetails.reranker && (
                        <div className="info-item">
                          <span className="label">Reranker:</span>
                          <span className="value">{pipelineDetails.reranker}</span>
                        </div>
                      )}
                      {pipelineDetails.completion_model && (
                        <div className="info-item">
                          <span className="label">Completion Model:</span>
                          <span className="value">{pipelineDetails.completion_model}</span>
                        </div>
                      )}
                    </div>
                    {pipelineDetails.sources && pipelineDetails.sources.length > 0 && (
                      <div className="sources-section">
                        <h4>Source Documents</h4>
                        {pipelineDetails.sources.map((source, idx) => (
                          <div key={idx} className="source-item">
                            <div className="source-file">{source.file}</div>
                            <div className="source-chunk">{source.chunk}</div>
                            <div className="source-scores">
                              <span>Search: {source.search_score?.toFixed(4)}</span>
                              {source.rerank_score !== null && source.rerank_score !== undefined && (
                                <span> | Rerank: {source.rerank_score.toFixed(4)}</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="recent-events-section">
              <h3>Recent Events</h3>
              <div className="events-summary">
                <p>View the last 10 system events and their status changes.</p>
                <button
                  className="view-events-button"
                  onClick={() => {
                    if (onViewEvents) {
                      onViewEvents();
                    }
                  }}
                >
                  View Recent Events
                </button>
              </div>
            </div>
          </div>

          <div className="sidebar">
            <div className="sensor-data-card">
              <h3>Sensor Readings</h3>
              <div className="sensor-grid">
                {
                  availableFields.map((field) => (
                    <div className="sensor-item" key={field}>
                      <span>{field}:</span>
                      <span className="value">{prediction[field]}</span>
                    </div>
                  ))
                }
              </div>
            </div>

            <div className="model-info-card">
              <h3>Model Information</h3>
              <div className="info-item">
                <span className="label">Model:</span>
                <span className="value">{prediction.model_used}</span>
              </div>
              <div className="info-item">
                <span className="label">Prediction:</span>
                <span className="value">
                  {prediction.prediction !== undefined ? prediction.prediction : prediction.encoded_prediction !== undefined ? prediction.encoded_prediction : 'N/A'}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Timestamp:</span>
                <span className="value">
                  {prediction.datetime ? parseUTCDatetime(prediction.datetime).toLocaleString() : 'N/A'}
                </span>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

export default DetailedPredictionView;
