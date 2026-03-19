import React, { useEffect, useState } from 'react';
import { Prediction } from '../types/Prediction';
import { getMonitoringData } from '../api/predictions';
import { parseUTCDatetime } from '../utils/datetime';
import './EventsModal.css';

interface EventsModalProps {
  isOpen: boolean;
  onClose: () => void;
  panelTitle: string;
  sensorType: string;
  excludeId?: string;
}

const EventsModal: React.FC<EventsModalProps> = ({
  isOpen,
  onClose,
  panelTitle,
  sensorType,
  excludeId
}) => {
  const [events, setEvents] = useState<Prediction[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoadingEvents(true);
      getMonitoringData({
        sensor: sensorType,
        limit: 10,
        excludeId
      })
        .then((data) => {
          if (Array.isArray(data)) {
            setEvents(data);
          } else if (data) {
            setEvents([data]);
          } else {
            setEvents([]);
          }
        })
        .catch(console.error)
        .finally(() => setLoadingEvents(false));
    }
  }, [isOpen, sensorType, excludeId]);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      onClose();
    }, 250);
  };

  if (!isOpen) return null;

  return (
    <div
      className={`events-modal-overlay${isClosing ? ' closing' : ''}`}
      onClick={handleClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="events-modal-title"
    >
      <div className="events-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="events-modal-header">
          <h2 id="events-modal-title" className="events-modal-title">{panelTitle} - Recent Events</h2>
          <button className="events-modal-close" onClick={handleClose} aria-label="Close dialog">
            <span>&times;</span>
          </button>
        </div>

        <div className="events-modal-body">
          {loadingEvents ? (
            <div className="loading-events">
              <div className="loading-spinner"></div>
              <p>Loading recent events...</p>
            </div>
          ) : (
            <div className="events-container">
              <div className="events-header">
                <h3>Last 10 System Events</h3>
                <p className="events-subtitle">Recent monitoring events and status changes</p>
              </div>

              <div className="events-list">
                {events.length > 0 ? (
                  events.map((event, index) => (
                    <div key={event._id || index} className="event-card">
                      <div className="event-card-header">
                        <div className="event-number">#{index + 1}</div>
                        <div className="event-timestamp">
                          {event.datetime ? parseUTCDatetime(event.datetime).toLocaleString() : 'N/A'}
                        </div>
                      </div>

                      <div className="event-card-body">
                        <h4 className="event-title" style={{ color: event.color }}>{event.description}</h4>
                        <p className="event-explanation">{event.explanation || 'No explanation available for this event.'}</p>

                        <div className="event-metrics">
                          <div className="metric-item">
                            <span className="metric-label">Prediction:</span>
                            <span className="metric-value">
                              {event.prediction !== undefined ? event.prediction : event.encoded_prediction !== undefined ? event.encoded_prediction : 'N/A'}
                            </span>
                          </div>
                          <div className="metric-item">
                            <span className="metric-label">Model:</span>
                            <span className="metric-value">{event.model_used}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-events-message">
                    <div className="no-events-icon">📊</div>
                    <h3>No Recent Events</h3>
                    <p>There are no recent monitoring events available for this sensor at the moment.</p>
                    <p className="no-events-subtitle">The system will display events here as they are captured.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EventsModal;
