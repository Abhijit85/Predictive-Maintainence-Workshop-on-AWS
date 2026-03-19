import { getSensors, getMonitoringData, getDiagnoseData } from './predictions';

// Mock global fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
});

describe('getSensors', () => {
  test('returns collections array on success', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ collections: ['sensor_a', 'sensor_b'] }),
    });

    const result = await getSensors();
    expect(result).toEqual(['sensor_a', 'sensor_b']);
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  test('throws on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => 'Internal Server Error',
    });

    await expect(getSensors()).rejects.toThrow('Error fetching sensors');
  });
});

describe('getMonitoringData', () => {
  test('sends correct query params', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ temp: 80, prediction: 1 }),
    });

    await getMonitoringData({ sensor: 'temp_sensor', limit: 1 });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain('sensor=temp_sensor');
    expect(calledUrl).toContain('limit=1');
  });

  test('includes excludeId when provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ([]),
    });

    await getMonitoringData({ sensor: 's1', limit: 10, excludeId: 'abc123' });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain('excludeId=abc123');
  });

  test('throws on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      text: async () => 'Not Found',
    });

    await expect(getMonitoringData({ sensor: 's1' })).rejects.toThrow('Error fetching monitoring data');
  });
});

describe('getDiagnoseData', () => {
  test('sends issue and model params', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        diagnosis: 'Replace bearing',
        search_method: 'hybrid',
      }),
    });

    const result = await getDiagnoseData({
      issue: 'valve failure',
      model: 'bedrock/nova-lite',
    });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain('issue=valve%20failure');
    expect(calledUrl).toContain('model=bedrock%2Fnova-lite');
    expect(result.diagnosis).toBe('Replace bearing');
  });

  test('sends reranker and embeddings_model when provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ diagnosis: 'ok' }),
    });

    await getDiagnoseData({
      issue: 'test',
      model: 'model',
      reranker: 'voyage/rerank-2',
      embeddings_model: 'voyage/voyage-3',
    });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain('reranker=voyage%2Frerank-2');
    expect(calledUrl).toContain('embeddings_model=voyage%2Fvoyage-3');
  });

  test('omits reranker and embeddings_model when not provided', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ diagnosis: 'ok' }),
    });

    await getDiagnoseData({ issue: 'test', model: 'model' });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).not.toContain('reranker=');
    expect(calledUrl).not.toContain('embeddings_model=');
  });

  test('throws on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => 'Error',
    });

    await expect(getDiagnoseData({ issue: 'x', model: 'm' })).rejects.toThrow('Error fetching diagnose data');
  });
});
