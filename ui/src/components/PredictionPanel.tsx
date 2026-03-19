import React, { useRef, useEffect, useState } from 'react';
import { Prediction } from '../types/Prediction';
import { parseUTCDatetime } from '../utils/datetime';
import './PredictionPanel.css';

interface PredictionPanelProps {
  title: string;
  prediction: Prediction;
  color: string;
  icon: string;
  history?: number[];
  onClick: () => void;
}

const Sparkline: React.FC<{ data: number[]; color: string }> = ({ data, color }) => {
  if (!data || data.length < 2) return null;
  const width = 120;
  const height = 32;
  const padding = 4;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min;
  const strokeColor = color || 'var(--color-accent-green)';

  // If all values are identical, draw a centered dashed line
  if (range === 0) {
    const midY = height / 2;
    return (
      <svg className="sparkline" width={width} height={height} aria-hidden="true">
        <line
          x1={padding} y1={midY} x2={width - padding} y2={midY}
          stroke={strokeColor} strokeWidth="1.5" strokeDasharray="4 3" opacity="0.4"
        />
      </svg>
    );
  }

  const points = data.map((v, i) => {
    const x = padding + (i / (data.length - 1)) * (width - padding * 2);
    const y = height - padding - ((v - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg className="sparkline" width={width} height={height} aria-hidden="true">
      <polyline
        fill="none"
        stroke={strokeColor}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

/** Map status color to a universal 0-100 health score */
const colorToHealthPct = (color: string): number => {
  const c = color?.toLowerCase();
  if (c === '#00ed64' || c === '#28a745') return 100;  // green — healthy
  if (c === '#ffc107' || c === '#ffc010') return 60;   // yellow — warning
  if (c === '#fd7e14') return 35;                       // orange — degraded
  if (c === '#dc3545' || c === '#db3030') return 10;   // red — critical
  return 0;                                              // unknown
};

const RadialGauge: React.FC<{ healthPct: number; color: string }> = ({ healthPct, color }) => {
  const size = 48;
  const strokeWidth = 5;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(Math.max(healthPct / 100, 0), 1);
  const offset = circumference * (1 - pct);

  return (
    <svg className="radial-gauge" width={size} height={size} aria-hidden="true">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color || 'var(--color-accent-green)'}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: 'stroke-dashoffset 0.6s ease' }}
      />
      <text
        x={size / 2}
        y={size / 2}
        textAnchor="middle"
        dominantBaseline="central"
        fill="var(--color-text-primary)"
        fontSize="10"
        fontFamily="var(--font-mono)"
        fontWeight="600"
      >
        {healthPct}%
      </text>
    </svg>
  );
};

const getStatusIcon = (color: string): string => {
  const c = color?.toLowerCase();
  if (c === '#00ed64' || c === '#28a745') return '✓';
  if (c === '#ffc010' || c === '#ffc107') return '⚠';
  return '✕';
};

const PredictionPanel: React.FC<PredictionPanelProps> = ({
  title,
  prediction,
  color,
  icon,
  history,
  onClick
}) => {
  const prevEncodedRef = useRef<number | undefined>(undefined);
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    if (
      prevEncodedRef.current !== undefined &&
      prevEncodedRef.current !== prediction.encoded_prediction
    ) {
      setFlash(true);
      const t = setTimeout(() => setFlash(false), 1000);
      return () => clearTimeout(t);
    }
    prevEncodedRef.current = prediction.encoded_prediction;
  }, [prediction.encoded_prediction]);

  const isTimestampStale = (): boolean => {
    if (!prediction.datetime) return true;
    const timestamp = parseUTCDatetime(prediction.datetime);
    const now = new Date();
    const diffInMinutes = (now.getTime() - timestamp.getTime()) / (1000 * 60);
    return diffInMinutes > 5;
  };

  const statusText = prediction.description || 'Unknown';
  const statusColor = prediction.color;
  const isStale = isTimestampStale();
  const healthPct = colorToHealthPct(statusColor);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className="prediction-panel"
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      aria-label={`${title}: ${statusText}`}
    >
      <div className="panel-header" style={{ backgroundColor: color }}>
        <div className="panel-icon">
          <span className="icon-text">{icon}</span>
        </div>
        <h3 className="panel-title">{title}</h3>
      </div>

      <div className="panel-content" aria-live="polite">
        <div className="status-indicator">
          <span className="status-icon" aria-hidden="true">{getStatusIcon(statusColor)}</span>
          <div
            className="status-dot"
            style={{
              backgroundColor: statusColor,
              boxShadow: `0 0 10px ${statusColor}`
            }}
          ></div>
          <span className="status-text" style={{ color: statusColor }}>{statusText}</span>
        </div>

        <div className="panel-viz-row">
          <RadialGauge healthPct={healthPct} color={statusColor} />
          <Sparkline data={history || []} color={statusColor} />
        </div>

        <div className="prediction-details">
          <div className="detail-item">
            <span className="detail-label">Model</span>
            <span className="detail-value">{prediction.model_used}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Timestamp</span>
            <div className="timestamp-container">
              <span className={`detail-value${flash ? ' flash' : ''}`}>
                {prediction.datetime ? parseUTCDatetime(prediction.datetime).toLocaleString() : 'N/A'}
              </span>
              {isStale && (
                <span
                  className="stale-warning-icon"
                  title="Sensor data is stale — no updates received for more than 5 minutes."
                >
                  ⚠️
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PredictionPanel;
