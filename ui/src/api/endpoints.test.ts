export {};

describe('endpoints', () => {
  const OLD_ENV = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...OLD_ENV };
  });

  afterAll(() => {
    process.env = OLD_ENV;
  });

  test('uses relative paths when env vars not set', () => {
    delete process.env.REACT_APP_FASTAPI_HOST;
    delete process.env.REACT_APP_FASTAPI_PORT;

    const { endpointsMap, EndpointsAction } = require('./endpoints');

    expect(endpointsMap[EndpointsAction.SENSORS].path).toBe('/api/sensors');
    expect(endpointsMap[EndpointsAction.MONITORING].path).toBe('/api/monitoring');
    expect(endpointsMap[EndpointsAction.DIAGNOSE].path).toBe('/api/diagnose');
  });

  test('uses custom host from env', () => {
    process.env.REACT_APP_FASTAPI_HOST = 'custom-alb.amazonaws.com';
    process.env.REACT_APP_FASTAPI_PORT = '80';

    const { endpointsMap, EndpointsAction } = require('./endpoints');

    expect(endpointsMap[EndpointsAction.SENSORS].path).toBe('http://custom-alb.amazonaws.com/api/sensors');
  });

  test('includes port when not 80', () => {
    process.env.REACT_APP_FASTAPI_HOST = 'localhost';
    process.env.REACT_APP_FASTAPI_PORT = '5001';

    const { endpointsMap, EndpointsAction } = require('./endpoints');

    expect(endpointsMap[EndpointsAction.SENSORS].path).toBe('http://localhost:5001/api/sensors');
  });

  test('sensors path ends with /api/sensors', () => {
    const { endpointsMap, EndpointsAction } = require('./endpoints');
    expect(endpointsMap[EndpointsAction.SENSORS].path).toMatch(/\/api\/sensors$/);
  });

  test('monitoring path ends with /api/monitoring', () => {
    const { endpointsMap, EndpointsAction } = require('./endpoints');
    expect(endpointsMap[EndpointsAction.MONITORING].path).toMatch(/\/api\/monitoring$/);
  });

  test('diagnose path ends with /api/diagnose', () => {
    const { endpointsMap, EndpointsAction } = require('./endpoints');
    expect(endpointsMap[EndpointsAction.DIAGNOSE].path).toMatch(/\/api\/diagnose$/);
  });

  test('all endpoints use GET method', () => {
    const { endpointsMap } = require('./endpoints');
    for (const key of Object.keys(endpointsMap)) {
      expect(endpointsMap[key].config.method).toBe('GET');
    }
  });

  test('all endpoints include Content-Type header', () => {
    const { endpointsMap } = require('./endpoints');
    for (const key of Object.keys(endpointsMap)) {
      expect(endpointsMap[key].config.headers['Content-Type']).toBe('application/json');
    }
  });
});
