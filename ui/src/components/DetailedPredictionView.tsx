import React, { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prediction } from '../types/Prediction';
import { getDiagnoseData } from '../api/predictions';
import { useUserContext } from '../App';
import { parseUTCDatetime } from '../utils/datetime';
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

/** Sensor-specific about/context information */
const sensorAbout: Record<string, { summary: string; measures: string; readings: string[]; states: string[] }> = {
  cooler_condition: {
    summary: 'Monitors the cooling system that regulates hydraulic fluid temperature. Overheating degrades oil viscosity, accelerates wear on seals and pumps, and can cause sudden shutdowns.',
    measures: 'Thermal efficiency of the cooling circuit, derived from temperature differentials (TS1–TS4), coolant flow rates (FS1, FS2), and cooling power (CP).',
    readings: [
      'TS1–TS4 — Temperature sensors across the cooling loop (°C)',
      'FS1, FS2 — Flow sensors measuring coolant throughput (l/min)',
      'CP — Cooling power output (kW)',
    ],
    states: [
      'Full efficiency (100) — Cooler operating at rated capacity',
      'Reduced efficiency (20) — Degraded cooling; schedule maintenance',
      'Close to total failure (3) — Imminent thermal runaway risk',
    ],
  },
  valve_condition: {
    summary: 'Tracks the hydraulic directional control valve responsible for routing pressurized fluid. Valve degradation causes sluggish actuator response and pressure losses.',
    measures: 'Switching lag and response time of the valve spool, inferred from pressure transients (PS1–PS6) and flow behaviour (FS1, FS2).',
    readings: [
      'PS1–PS6 — Pressure sensors at various circuit points (bar)',
      'FS1, FS2 — Flow sensors before and after the valve (l/min)',
      'VS1 — Vibration sensor on the valve body (mm/s)',
    ],
    states: [
      'Optimal switching behaviour (100) — Crisp, fast valve response',
      'Small lag (90) — Minor delay; monitor trend',
      'Severe lag (80) — Significant delay; plan repair',
      'Close to total failure (73) — Valve nearly non-functional',
    ],
  },
  internal_pump_leakage: {
    summary: 'Detects internal leakage within the hydraulic pump. Leakage reduces volumetric efficiency, drops system pressure, and increases energy consumption.',
    measures: 'Pump volumetric efficiency estimated from pressure differential (PS1–PS3), motor power draw (EPS1), and efficiency metrics (CE, SE).',
    readings: [
      'PS1, PS2, PS3 — Suction and discharge pressures (bar)',
      'EPS1 — Motor electrical power consumption (W)',
      'CE — Cooling efficiency (%)',
      'SE — System efficiency (%)',
    ],
    states: [
      'No leakage (0) — Pump seals intact, full efficiency',
      'Weak leakage (1) — Minor seal wear; schedule inspection',
      'Severe leakage (2) — Major internal bypass; immediate action needed',
    ],
  },
  hydraulic_accumulator: {
    summary: 'Monitors the gas-charged hydraulic accumulator that stores energy and dampens pressure spikes. Loss of pre-charge pressure leads to pulsation, cavitation, and pump damage.',
    measures: 'Accumulator pre-charge pressure level, estimated from system pressure dynamics (PS1–PS6) and vibration (VS1).',
    readings: [
      'PS1–PS6 — System pressure measurements (bar)',
      'VS1 — Vibration amplitude near the accumulator (mm/s)',
      'EPS1 — Motor power draw reflecting load changes (W)',
    ],
    states: [
      'Optimal pressure (130 bar) — Fully charged, operating normally',
      'Slightly reduced (115 bar) — Minor gas loss; plan recharge',
      'Severely reduced (100 bar) — Significant loss; recharge soon',
      'Close to total failure (90 bar) — Critical; immediate recharge required',
    ],
  },
  stable_flag: {
    summary: 'An aggregate stability indicator that evaluates whether the overall hydraulic system is operating within stable boundaries. It combines signals from all sensors to detect oscillations, drift, or erratic behaviour.',
    measures: 'Global system stability derived from a composite analysis of all 17 sensor channels — pressure, temperature, flow, vibration, and efficiency.',
    readings: [
      'All PS, TS, FS, VS, CE, CP, SE channels contribute',
      'The model looks for oscillations, sudden shifts, and out-of-range correlations',
    ],
    states: [
      'Stable (1) — System operating within normal bounds',
      'Unstable (0) — Anomalous dynamics detected; investigate root cause',
    ],
  },
  motor_power: {
    summary: 'Assesses the electric drive motor powering the hydraulic pump. Degraded motor output leads to insufficient pressure, slower cycle times, and increased thermal stress.',
    measures: 'Motor power efficiency estimated from electrical draw (EPS1), system pressures (PS1–PS6), and overall efficiency metrics (CE, SE).',
    readings: [
      'EPS1 — Motor electrical power consumption (W)',
      'PS1–PS6 — Resulting system pressures (bar)',
      'CE — Cooling efficiency (%), SE — System efficiency (%)',
    ],
    states: [
      'Full power efficiency (2) — Motor delivering rated output',
      'Slightly degraded (1) — Minor power loss; monitor trend',
      'Severely degraded (0) — Significant power deficit; service required',
    ],
  },
};

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
              const about = sensorAbout[getSensorKey(prediction.model_used)];
              if (!about) return null;
              return (
                <div className="about-section">
                  <h3>About This Sensor</h3>
                  <div className="about-content">
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
