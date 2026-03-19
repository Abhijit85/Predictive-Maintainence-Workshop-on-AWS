import { useEffect, useState, useCallback, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMonitoringData, getSensors } from '../../api/predictions'
import { Prediction } from '../../types/Prediction'

import mongodbLogo from '../../icons/mongodb-logo-white.png'
import Menu from '../menu/Menu'
import PredictionPanel from '../../components/PredictionPanel'
import DetailedPredictionView from '../../components/DetailedPredictionView'
import EventsModal from '../../components/EventsModal'
import './Home.css'

import { useUserContext } from '../../App'

const Home = () => {
  const [predictions, setPredictions] = useState<{ [key: string]: Prediction }>({})
  const [predictionHistory, setPredictionHistory] = useState<{ [key: string]: number[] }>({})
  const [error, setError] = useState<string | null>(null)
  const [isExpanded, setIsExpanded] = useState(false)
  const [selectedPrediction, setSelectedPrediction] = useState<Prediction | null>(null)
  const [selectedPanelTitle, setSelectedPanelTitle] = useState('')
  const [currentTime, setCurrentTime] = useState(new Date())
  const [isEventsModalOpen, setIsEventsModalOpen] = useState(false)
  const [isBackendConnected, setIsBackendConnected] = useState(true)
  const [sensors, setSensors] = useState<string[]>([])
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false)
  const isFetchingRef = useRef(false)
  const navigate = useNavigate()
  const { selectedCompletion } = useUserContext()
  const refreshRate = 30

  const getModelDisplayName = (model: string) => {
    if (model === 'us.amazon.nova-lite-v1:0') return ['Bedrock', model]
    const parts = model.split('/')
    return [parts[0] || model, model]
  }

  const panels = useMemo(() => {
    return sensors.map(sensor => ({
      id: sensor.replace(/_/g, '-'),
      title: sensor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      field: sensor as keyof Prediction,
      sensor
    }))
  }, [sensors])

  useEffect(() => {
    const fetchSensors = async () => {
      try {
        const sensorList = await getSensors()
        setSensors(sensorList as string[])
      } catch (err) {
        setError('Failed to fetch sensors')
        setIsBackendConnected(false)
      }
    }
    fetchSensors()
  }, [])

  const fetchPredictions = useCallback(async () => {
    if (isFetchingRef.current) return

    isFetchingRef.current = true
    try {
      const newPredictions: { [key: string]: Prediction } = {}

      for (const panel of panels) {
        try {
          const data = await getMonitoringData({
            sensor: panel.sensor,
            limit: 1
          })

          if (Array.isArray(data)) {
            if (data.length > 0) {
              newPredictions[panel.sensor] = data[0]
            }
          } else if (data) {
            newPredictions[panel.sensor] = data
          }
        } catch (err) {
          console.error(`Error fetching ${panel.sensor}:`, err)
        }
      }

      setPredictions(newPredictions)
      setHasLoadedOnce(true)

      // Accumulate sparkline history using the first numeric sensor reading
      // (e.g. PS1, EPS1, TS1) which changes each cycle — not encoded_prediction
      // which is a discrete class label that stays flat
      const excludedKeys = new Set([
        'encoded_prediction', 'model_used', 'prediction', 'description',
        'color', 'icon', 'explanation', 'timestamp', 'datetime', '_id'
      ])
      setPredictionHistory(prev => {
        const next = { ...prev }
        for (const [sensor, pred] of Object.entries(newPredictions)) {
          // Find the first numeric sensor field
          const sensorKey = Object.keys(pred).find(
            k => !excludedKeys.has(k) && typeof pred[k] === 'number'
          )
          const val = sensorKey ? pred[sensorKey] : undefined
          if (val !== undefined) {
            const arr = [...(prev[sensor] || []), val]
            next[sensor] = arr.slice(-20)
          }
        }
        return next
      })

      setError(null)
      setIsBackendConnected(true)
    } catch (err) {
      console.error('Error in fetchPredictions:', err)
      setIsBackendConnected(false)
      if (Object.keys(predictions).length === 0) {
        setError(err instanceof Error ? err.message : 'Failed to fetch predictions')
      }
    } finally {
      isFetchingRef.current = false
    }
  }, [panels])

  useEffect(() => {
    if (panels.length > 0) {
      fetchPredictions()
    }
  }, [panels])

  useEffect(() => {
    const interval = setInterval(fetchPredictions, refreshRate * 1000)
    return () => clearInterval(interval)
  }, [fetchPredictions])

  useEffect(() => {
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timeInterval)
  }, [])

  const handlePanelClick = (prediction: Prediction, panelTitle: string) => {
    setSelectedPrediction(prediction)
    setSelectedPanelTitle(panelTitle)
    setIsExpanded(true)
  }

  const closeDetailedView = () => {
    setIsExpanded(false)
    setSelectedPrediction(null)
    setSelectedPanelTitle('')
  }

  const handleViewEvents = () => {
    setIsEventsModalOpen(true)
  }

  const closeEventsModal = () => {
    setIsEventsModalOpen(false)
  }

  const getSensorTypeFromPanelTitle = (panelTitle: string): string => {
    const panel = panels.find(p => p.title === panelTitle)
    return panel ? panel.sensor : 'N/A'
  }

  if (error) return (
    <div className="home-container">
      <div className="predictions-container">
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={fetchPredictions} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    </div>
  )

  return (
    <div className="home-container">
      <div className="predictions-container">
        <div className="dashboard-header">
          <div className="dashboard-header-left">
            <img
              src={mongodbLogo}
              alt="MongoDB"
              className="dashboard-logo"
              onClick={() => navigate('/')}
            />
            <div>
              <h1 className="dashboard-title">System Monitoring Dashboard</h1>
              <p className="dashboard-subtitle">Real-time Equipment Health Analysis</p>
            </div>
          </div>
          <div className="system-status">
            <div className="status-indicator">
              <div className={`status-dot ${isBackendConnected ? 'online' : 'offline'}`}></div>
              <span className="status-text">
                {isBackendConnected ? 'System Online' : 'Backend Offline'}
              </span>
            </div>
          </div>
        </div>

        <div className="monitoring-hero">
          <div className="hero-count">{Object.keys(predictions).length}</div>
          <div className="hero-label">Active Sensors</div>
        </div>

        <div className="status-bar">
          <div className="status-bar-item">
            <span className="status-bar-label">AI Model</span>
            <span className="status-bar-value" title={getModelDisplayName(selectedCompletion)[1]}>
              {getModelDisplayName(selectedCompletion)[0]}
            </span>
          </div>
          <div className="status-bar-item">
            <span className="status-bar-label">Refresh</span>
            <span className="status-bar-value">{refreshRate}s</span>
          </div>
          <div className="status-bar-item">
            <span className="status-bar-label">Time</span>
            <span className="status-bar-value">{currentTime.toLocaleTimeString()}</span>
          </div>
        </div>

        <Menu />

        <div className="predictions-grid">
          {panels.map((panel) => {
            const prediction = predictions[panel.sensor]

            // Show skeleton while first load is in progress
            if (!hasLoadedOnce) {
              return (
                <div key={panel.id} className="skeleton-card">
                  <div className="skeleton-header" />
                  <div className="skeleton-body">
                    <div className="skeleton-line medium" />
                    <div className="skeleton-line short" />
                    <div className="skeleton-line" />
                    <div className="skeleton-line short" />
                  </div>
                </div>
              )
            }

            // Show empty state if sensor has no data yet
            if (!prediction) {
              return (
                <div key={panel.id} className="empty-panel">
                  Awaiting data for {panel.title}...
                </div>
              )
            }

            return (
              <PredictionPanel
                key={panel.id}
                title={panel.title}
                prediction={prediction}
                color={prediction.color}
                icon={prediction.icon ? prediction.icon : '⚙️'}
                history={predictionHistory[panel.sensor]}
                onClick={() => handlePanelClick(prediction, panel.title)}
              />
            )
          })}
        </div>

        <div className="dashboard-footer">
          <span className="footer-label">Powered by</span>
          <span className="badge-footer badge-footer-aws">AWS</span>
          <span className="badge-footer badge-footer-mongodb">MongoDB Atlas</span>
          <span className="badge-footer badge-footer-voyage">Voyage AI</span>
        </div>
      </div>

      <DetailedPredictionView
        isExpanded={isExpanded}
        onClose={closeDetailedView}
        prediction={selectedPrediction}
        panelTitle={selectedPanelTitle}
        onViewEvents={handleViewEvents}
      />

      <EventsModal
        isOpen={isEventsModalOpen}
        onClose={closeEventsModal}
        panelTitle={selectedPanelTitle}
        sensorType={getSensorTypeFromPanelTitle(selectedPanelTitle)}
        excludeId={selectedPrediction?._id}
      />
    </div>
  )
}

export default Home
