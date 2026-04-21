export interface SensorAbout {
  summary: string;
  measures: string;
  readings: string[];
  states: string[];
}

export interface SensorMetadata {
  title: string;
  assetClass: string;
  about: SensorAbout;
}

export const sensorMetadata: Record<string, SensorMetadata> = {
  cooler_condition: {
    title: 'Compressor Cooling Loop',
    assetClass: 'Compression Train',
    about: {
      summary: 'Tracks the cooling loop serving a compressor or rotating equipment skid. Cooling degradation can accelerate wear, destabilize fluid properties, and raise shutdown risk during sustained operations.',
      measures: 'Thermal performance across the cooling circuit using temperature differentials, coolant flow, and cooling power output.',
      readings: [
        'TS1–TS4 — Temperature points across the cooling loop',
        'FS1, FS2 — Coolant flow behaviour through the skid',
        'CP — Cooling power available to remove heat load',
      ],
      states: [
        'Full efficiency (100) — Cooling loop operating in its normal envelope',
        'Reduced efficiency (20) — Heat removal is degrading; inspection should be scheduled',
        'Close to total failure (3) — Cooling loss may justify controlled shutdown',
      ],
    },
  },
  valve_condition: {
    title: 'Wellhead Control Valve Response',
    assetClass: 'Control System',
    about: {
      summary: 'Represents the actuation health of a hydraulic or process control valve. Valve lag can impair flow control, response time, and safe isolation performance.',
      measures: 'Switching lag and hydraulic response inferred from pressure and flow behaviour around the control path.',
      readings: [
        'PS1–PS6 — Pressure behaviour before and after the valve path',
        'FS1, FS2 — Flow changes during switching',
        'VS1 — Vibration near the valve body or actuator',
      ],
      states: [
        'Optimal switching behavior (100) — Valve is responding as expected',
        'Small lag (90) — Minor delay detected; continue monitoring',
        'Severe lag (80) — Noticeable actuation degradation; maintenance planning required',
        'Close to total failure (73) — Isolation reliability is at risk',
      ],
    },
  },
  internal_pump_leakage: {
    title: 'Produced Water Pump Leakage',
    assetClass: 'Pumping System',
    about: {
      summary: 'Estimates internal leakage severity in a pump or pump-driven subsystem. Leakage lowers volumetric efficiency, raises energy consumption, and can reduce line pressure at critical operating points.',
      measures: 'Pump efficiency loss using pressure differential, motor power draw, and system efficiency signals.',
      readings: [
        'PS1–PS3 — Suction and discharge pressure behaviour',
        'EPS1 — Electrical load associated with pumping effort',
        'CE, SE — Cooling and system efficiency indicators',
      ],
      states: [
        'No leakage (0) — Pump internals are operating within expected tolerance',
        'Weak leakage (1) — Early wear or bypass behaviour is present',
        'Severe leakage (2) — Significant internal loss; intervention is likely required',
      ],
    },
  },
  hydraulic_accumulator: {
    title: 'Accumulator Pressure Integrity',
    assetClass: 'Hydraulic Safety System',
    about: {
      summary: 'Monitors the charge state of a hydraulic accumulator used for damping, surge control, or actuator reserve energy. Loss of pressure can reduce control authority and increase trip risk.',
      measures: 'Accumulator pressure health inferred from pressure-wave behaviour, vibration, and system load response.',
      readings: [
        'PS1–PS6 — Pressure behaviour across the hydraulic circuit',
        'VS1 — Vibration signature near the accumulator assembly',
        'EPS1 — Motor or pump loading associated with pressure compensation',
      ],
      states: [
        'Optimal pressure (130 bar) — Accumulator is in its target operating range',
        'Slightly reduced pressure (115 bar) — Degradation is visible; recharge planning recommended',
        'Severely reduced pressure (100 bar) — Pressure reserve is compromised',
        'Close to total failure (90 bar) — Immediate operator review is warranted',
      ],
    },
  },
  stable_flag: {
    title: 'Platform Stability Index',
    assetClass: 'Asset Health Aggregate',
    about: {
      summary: 'A combined stability signal that indicates whether the monitored asset is operating within a normal and coherent control envelope.',
      measures: 'A cross-sensor stability score derived from pressure, temperature, flow, vibration, and efficiency channels.',
      readings: [
        'All PS, TS, FS, VS, CE, CP, and SE channels contribute to the stability score',
        'The model looks for drift, oscillation, and abnormal cross-signal relationships',
      ],
      states: [
        'System stable (1) — Operating conditions are internally consistent',
        'System unstable (0) — Correlated anomalies suggest broader asset risk',
      ],
    },
  },
  motor_power: {
    title: 'Drive Motor Performance',
    assetClass: 'Rotating Equipment',
    about: {
      summary: 'Assesses the electric drive motor supporting a pump or compressor package. Degraded motor output can propagate into pressure loss, unstable response, and higher thermal stress.',
      measures: 'Motor power efficiency estimated from electrical draw, pressure response, and overall efficiency signals.',
      readings: [
        'EPS1 — Electrical power draw for the motor',
        'PS1–PS6 — Pressure response under changing load',
        'CE, SE — Efficiency signals indicating secondary impacts',
      ],
      states: [
        'Full power efficiency (2) — Motor is delivering expected performance',
        'Slightly degraded power (1) — Mild performance loss is detectable',
        'Severely degraded power (0) — Power deficit may affect safe operation',
      ],
    },
  },
  methane_ppm: {
    title: 'Methane Emissions Monitor',
    assetClass: 'Gas Detection',
    about: {
      summary: 'Represents methane concentration monitoring for process areas, well pads, or compressor sites. It is useful for leak detection, safety escalation, and environmental response workflows in the workshop.',
      measures: 'Estimated methane concentration based on a multi-sensor gas signature and supporting hydrocarbon response channels.',
      readings: [
        'S1–S16 — Sensor array channels feeding the methane model',
        'Ethylene_ppm — Companion gas signal included as context',
        'Methane_ppm — Predicted methane concentration band used for alerts',
      ],
      states: [
        'Green bands — Background or normal operating emissions',
        'Yellow and orange bands — Elevated methane requiring investigation',
        'Red bands — Critical methane concentration requiring immediate response',
      ],
    },
  },
};

export const getSensorMetadata = (sensor: string): SensorMetadata | undefined =>
  sensorMetadata[sensor];

export const getSensorTitle = (sensor: string): string =>
  sensorMetadata[sensor]?.title ??
  sensor.replace(/_/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase());
