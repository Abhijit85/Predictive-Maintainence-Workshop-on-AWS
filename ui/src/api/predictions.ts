import { Prediction } from '../types/Prediction';
import { EndpointsAction, endpointsMap } from './endpoints';

interface MonitoringSearchProps {
  sensor: string;
  limit?: number;
  excludeId?: string;
}

interface DiagnoseSearchProps {
  issue: string;
  model: string;
  reranker?: string;
  embeddings_model?: string;
}

export async function getSensors(): Promise<String[]> {
  const sensorsEndpoint = endpointsMap[EndpointsAction.SENSORS];

  try {
    const response = await fetch(sensorsEndpoint.path, sensorsEndpoint.config);

    if (!response.ok) {
      const error = await response.text();
      const errorMessage = `Error fetching sensors [Status=${response.status}]:${error}`;
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data["collections"];
  } catch (error) {
    console.error('Error fetching sensors:', error);
    throw error;
  }
}

export async function getMonitoringData(props: MonitoringSearchProps): Promise<Prediction | Prediction[]> {
  const monitoring = endpointsMap[EndpointsAction.MONITORING];
  let parameters = `?sensor=${props.sensor}&limit=${props.limit || 1}`;

  if (props.excludeId) {
    parameters += `&excludeId=${props.excludeId}`;
  }

  try {
    const response = await fetch(monitoring.path + parameters, monitoring.config);

    if (!response.ok) {
      const error = await response.text();
      const errorMessage = `Error fetching monitoring data [Status=${response.status}]:${error}`;
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching monitoring data:', error);
    throw error;
  }
}

export async function getDiagnoseData(props: DiagnoseSearchProps): Promise<any> {
  const diagnose = endpointsMap[EndpointsAction.DIAGNOSE];
  let parameters = `?issue=${encodeURIComponent(props.issue)}&model=${encodeURIComponent(props.model)}`;

  if (props.reranker) {
    parameters += `&reranker=${encodeURIComponent(props.reranker)}`;
  }
  if (props.embeddings_model) {
    parameters += `&embeddings_model=${encodeURIComponent(props.embeddings_model)}`;
  }

  try {
    const response = await fetch(diagnose.path + parameters, diagnose.config);

    if (!response.ok) {
      const error = await response.text();
      const errorMessage = `Error fetching diagnose data [Status=${response.status}]:${error}`;
      throw new Error(errorMessage);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching diagnose data:', error);
    throw error;
  }
}
