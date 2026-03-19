# Features and Usage

- [Access URLs](#access-urls)
  - [Ports](#ports)
  - [Other Modules](#other-modules)
- [API Usage Examples](#api-usage-examples)
  - [REST API Examples](#rest-api-examples)
- [MCP through Claude](#mcp-through-claude)
  - [Configuration Notes](#configuration-notes)
  - [Verification Steps](#verification-steps)
  - [Troubleshooting](#troubleshooting)
  - [Available Functions](#available-functions)
- [Embedding Model Options](#embedding-model-options)
- [Troubleshooting](#troubleshooting-1)
  - [Common Issues](#common-issues)
  - [Logs](#logs)
- [Development](#development)

## Access URLs

### Ports
- **UI**: http://localhost:3001
- **API**: http://localhost:5001 (configurable via `REACT_APP_FASTAPI_PORT`)
- **Docs**: http://localhost:5001/docs

## API Usage Examples

### REST API Examples

The Predictions API provides several endpoints for model inference, diagnostics, monitoring, and more. Below are example usages for each endpoint.

---

#### 1. Health Check

Check if the API server is running:

```bash
curl http://localhost:5001/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "predictive_maintenance"
}
```

---

#### 2. List Available Models

Get all trained prediction models:

```bash
curl http://localhost:5001/api/models
```

**Response:**
```json
{
    "models": [
        "Logistic_Regression-cooler_condition",
        "Logistic_Regression-internal_pump_leakage",
        "Random_Forest-hydraulic_accumulator",
        "Random_Forest-valve_condition",
        "Random_Forest-stable_flag",
        "Random_Forest-motor_power"
    ],
    "count": 6
}
```

---

#### 3. List Sensor Collections

List all available sensor monitoring collections:

```bash
curl http://localhost:5001/api/sensors
```

**Response:**
```json
{
  "collections": [
    "cooler_condition",
    "valve_condition",
    "internal_pump_leakage",
    "hydraulic_accumulator",
    "stable_flag",
    "motor_power"
  ]
}
```

---

#### 4. Get Sensor Monitoring Data

Retrieve recent sensor data and predictions:

```bash
curl "http://localhost:5001/api/monitoring?sensor=cooler_condition&limit=1"
```

**Response:**
```json
{
    "_id": "68b7528fa8d48c318b903b0e",
    "PS1": 156.25,
    "PS2": 105.17,
    "PS3": 1.68,
    "PS4": 0.0,
    "PS5": 8.4,
    "PS6": 8.36,
    "EPS1": 2366.35,
    "FS1": 6.57,
    "FS2": 8.92,
    "TS1": 57.32,
    "TS2": 61.45,
    "TS3": 58.71,
    "TS4": 52.58,
    "VS1": 0.72,
    "CE": 18.86,
    "CP": 1.47,
    "SE": 59.96,
    "encoded_prediction": 0,
    "model_used": "Logistic_Regression-cooler_condition",
    "prediction": 3,
    "description": "close to total failure",
    "color": "#dc3545",
    "icon": "❄️",
    "datetime": "2025-09-02 14:24:47"
}
```

---

#### 5. Make Prediction

Generate a prediction using a trained model:

```bash
curl -X POST "http://localhost:5001/api/predict" \
  -H "Content-Type: application/json" \
  -d '{
  "independent_variables": [
    174.89, 124.5, 1.04, 0.0, 8.54, 8.48, 2676.66, 
    3.02, 9.2, 54.14, 58.59, 55.78, 49.56, 0.74, 
    19.97, 1.54, 27.13
  ],
  "model_identifier": "Logistic_Regression-cooler_condition"
}'
```

**Response:**
```json
{
  "encoded_prediction": 0,
  "model_used": "Logistic_Regression-cooler_condition",
  "prediction": 3
}
```

---

#### 6. Diagnose Technical Issue

Get AI-powered diagnostic recommendations:

```bash
curl "http://localhost:5001/api/diagnose?issue=close%20to%20total%20failure%20-%20cooler%20condition%20-%20prediction%3A%203&model=us.amazon.nova-lite-v1%3A0"
```

**Response:**
```json
{
    "diagnosis": "Based on the provided contexts, here is a step-by-step guide to solving the issue of a cooler condition close to total failure with a prediction value of 3:\n\n### Step-by-Step Solution:\n\n#### 1. **Immediate Actions:**\n   - **Shut Down the System:** To prevent further damage, immediately shut down the hydraulic system if it is still operational.\n   - **Cool Down the System:** Allow the system to cool down to a safe temperature before performing any maintenance or inspection.\n\n#### 2. **Visual Inspection:**\n   - **Check for Leaks:** Inspect the oil cooler for any visible leaks or damage on the cooler core or fittings.\n   - **Inspect for Debris:** Look for debris or dirt on the cooler fins that could be blocking airflow and reducing cooling efficiency.\n\n#### 3. **Temperature Monitoring:**\n   - **Gauge Reading:** Check the temperature gauge against manufacturer specifications. A persistently high reading indicates a cooling problem.\n   - **Fluid Outlet Temperature:** Monitor the fluid outlet temperature during operation. A significantly higher-than-normal temperature implies poor cooling.\n\n#### 4. **Maintenance Records Review:**\n   - **Last Cleaning:** Review maintenance records to determine when the cooler was last cleaned.\n   - **Flow/Pressure Test:** If available, perform a flow or pressure test to verify that the coolant or hydraulic fluid circulates correctly through the cooler.\n\n#### 5. **Cleaning the Cooler:**\n   - **Remove Dirt and Debris:** Use low-pressure compressed air or a soft brush to blow out or brush off accumulated dirt and debris from the cooler fins.\n   - **Light Water Spray:** A light water spray can help dislodge stubborn mud. Avoid using high-pressure wash which can bend the fins.\n   - **Professional Cleaning:** In severe cases, consider professional cleaning methods such as ultrasonic cleaning.\n\n#### 6. **Inspection and Repair:**\n   - **Inspect for Corrosion/Leaks:** After cleaning, inspect the cooler for corrosion, leaks, or bent fins.\n   - **Tighten Fittings:** Tighten any loose fittings and replace worn seals.\n   - **Patch Small Holes:** Small holes or fin damage may be patched with epoxy.\n   - **Replace Major Leaks:** Major core leaks require immediate cooler replacement.\n\n#### 7. **Preventive Measures:**\n   - **Ensure Free Airflow:** Make sure there is free airflow around the cooler and remove any obstructions from nearby structures.\n   - **Maintain Clean Fluid:** Keep the hydraulic oil clean and at the correct viscosity to prevent overheating and clogging.\n   - **Regular Cleaning:** Schedule regular cleaning based on the environment, with more frequent service in dusty or mobile applications.\n\n#### 8. **Final Decision:**\n   - **Replace Cooler:** Since the cooler condition is close to total failure with a prediction value of 3, it is crucial to replace the cooler immediately to avoid system damage.\n\n### Conclusion:\nGiven the severity of the cooler condition, the best course of action is to replace the cooler. This will restore the system's cooling efficiency and prevent further damage to the hydraulic system. Regular maintenance and proactive inspections can help prevent such issues in the future."
}
```

---

#### 7. Generate Text with AI

Generate text using an AI model:

```bash
curl "http://localhost:5001/api/text_gen?text=Explain%20cooler%20condition%20level%203&model=us.amazon.nova-lite-v1%3A0"
```

**Response:**
```json
{
    "answer": "\"Cooler condition level 3\" is not a standard term in any widely recognized field such as meteorology, HVAC (heating, ventilation, and air conditioning), or environmental science. However, it could potentially be a term used in a specific context or industry, such as in a manufacturing process, a data center, or a particular type of storage facility. Without additional context, it's challenging to provide a precise explanation.\n\nHere are a few possible interpretations based on different contexts:\n\n### 1. **Manufacturing or Industrial Processes:**\nIn some manufacturing processes, \"cooler condition level 3\" might refer to a specific temperature setting or range that is used to control the cooling of materials or products during production. This could be part of a quality control system to ensure that products are cooled to a precise temperature to meet specific standards.\n\n### 2. **Data Centers:**\nIn the context of data centers, \"cooler condition level 3\" might refer to a specific cooling tier or setting within the facility's climate control system. Data centers often have multiple levels of cooling to ensure that servers and other equipment operate within their optimal temperature ranges. Level 3 might indicate a higher or more intensive cooling setting than levels 1 or 2.\n\n### 3. **Food Storage:**\nIn food storage facilities, \"cooler condition level 3\" might refer to a specific temperature setting used to store perishable items. For example, different levels might correspond to different temperature ranges, with level 3 being a cooler setting than level 1 or 2.\n\n### 4. **HVAC Systems:**\nIn HVAC systems, \"cooler condition level 3\" might refer to a specific setting on an air conditioning unit. For instance, it could indicate a higher fan speed, a lower set temperature, or a more aggressive cooling mode compared to levels 1 or 2.\n\n### Hypothetical Example:\nLet's assume \"cooler condition level 3\" is used in a data center:\n\n- **Level 1:** Basic cooling, suitable for normal operating conditions.\n- **Level 2:** Moderate cooling, used when the ambient temperature is higher than usual.\n- **Level 3:** Intensive cooling, used during peak load conditions or when the ambient temperature is extremely high.\n\nIn this case, \"cooler condition level 3\" would mean that the data center's cooling system is operating at its highest capacity to maintain optimal temperatures for the equipment.\n\n### Conclusion:\nTo provide a more accurate explanation, it would be helpful to have more context about where and how \"cooler condition level 3\" is being used. If you can provide additional details, I can offer a more precise explanation."
}
```

---

> **Note:** Replace `localhost:5001` with your API fastapi-mcp host and port if different.

### MCP through Claude

> Easy MCP access through Claude configuration for seamless integration.

Run fastapi-mcp beforehand

Go to Claude Developer Settings, clicking on "Edit Config" and open claude_desktop_config.json
Follow this example for setting the JSON configuration:

```json
{
    "mcpServers": {
        "predictions-mcp": {
            "command": "npx",
            "args": [
                "-y",
                "mcp-remote",
                "http://127.0.0.1:5001/mcp/"
            ]
        }
    }
}
```

> Note: Set the same host and port that the fastapi-mcp uses.

#### Configuration Notes:

- Adjust paths according to your system and installation directory
- Ensure all required environment variables are properly set
- The port can be customized but must match your server configuration

#### Verification Steps:

1. Save the configuration file
2. Restart Claude Desktop application
3. Go to Claude interface
4. Under "Search and tools", "Predictive Maintenance MCP Server" should appear
5. Test the connection with a simple health check

#### Troubleshooting:

- If you encounter errors, check the logs folder: File > Settings > Developer > View Logs
- Verify all file paths are correct and accessible
- Ensure Python environment has all required dependencies installed
- Check MongoDB connection string is valid and database is accessible
- Verify AWS credentials have proper permissions for Bedrock services

#### Available Functions

**1. Health Check**

Purpose: Verify server status and connectivity.

Endpoint: health_check_health_get
```json
// Request
{}

// Response
{
  "status": "healthy",
  "service": "predictive_maintenance"
}
```

**2. List Available Models**

Purpose: Get all trained prediction models.

Endpoint: list_available_models
```json
// Request
{}

// Response
{
  "models":[
    "Logistic_Regression-cooler_condition",
    "Logistic_Regression-internal_pump_leakage",
    "Random_Forest-hydraulic_accumulator",
    "Random_Forest-valve_condition",
    "Random_Forest-stable_flag",
    "Random_Forest-motor_power"
  ],
  "count":6
}
```

**3. List Sensor Collections**

Purpose: Get available sensor monitoring collections.

Endpoint: list_sensor_collections
```json
// Request
{}

// Response
{
  "collections": [
    "cooler_condition",
    "valve_condition",
    "internal_pump_leakage",
    "hydraulic_accumulator",
    "stable_flag",
    "motor_power"
  ]
}
```
**4. Get Sensor Monitoring Data**

Purpose: Retrieve historical sensor data and predictions.

Endpoint: get_sensor_monitoring_data

Parameters:
- sensor (required): Sensor collection name
- limit (optional): Number of records (default: 10)
- excludeId (optional): Exclude specific document ID

```json
// Request
{
  "sensor": "cooler_condition",
  "limit": 1
}

// Response
{
  "result": [
    {
      "_id": "68a79b6e1f9ec571bb1aa757",
      "PS1": 161.04,
      "PS2": 109.59,
      "PS3": 2,
      "PS4": 0.34,
      "PS5": 9.96,
      "PS6": 9.83,
      "EPS1": 2546.75,
      "FS1": 6.71,
      "FS2": 10.19,
      "TS1": 35.48,
      "TS2": 41.09,
      "TS3": 38.4,
      "TS4": 30.57,
      "VS1": 0.55,
      "CE": 46.64,
      "CP": 2.15,
      "SE": 59.11,
      "encoded_prediction": 2,
      "model_used": "Logistic_Regression-cooler_condition",
      "prediction": 100,
      "description": "full efficiency",
      "color": "#00ED64",
      "icon": "❄️",
      "datetime": "2025-08-21 16:19:26"
    }
  ]
}
```
**5. Make Prediction**

Purpose: Generate predictions using trained models

Endpoint: make_prediction

Parameters:
  - independent_variables (required): Input features array
  - model_identifier (required): Model name from available models
  - dependent_variables (optional): Known outcomes for validation

```json
// Request
{
  "independent_variables": [
    174.89, 124.5, 1.04, 0.0, 8.54, 8.48, 2676.66, 
    3.02, 9.2, 54.14, 58.59, 55.78, 49.56, 0.74, 
    19.97, 1.54, 27.13
  ],
  "model_identifier": "Logistic_Regression-cooler_condition"
}

// Response
{
  "encoded_prediction": 0,
  "model_used": "Logistic_Regression-cooler_condition",
  "prediction": 3
}
```
Prediction Interpretations (by sensor type):
- **cooler_condition**: 3 = Close to total failure, 20 = Reduced efficiency, 100 = Full efficiency
- **valve_condition**: 73 = Close to total failure, 80 = Severe lag, 90 = Small lag, 100 = Optimal
- **internal_pump_leakage**: 0 = No leakage, 1 = Weak leakage, 2 = Severe leakage
- **hydraulic_accumulator**: 90 = Close to total failure, 100 = Severely reduced, 115 = Slightly reduced, 130 = Optimal
- **stable_flag**: 0 = System unstable, 1 = System stable
- **motor_power**: 0 = Severely degraded, 1 = Slightly degraded, 2 = Full efficiency

**6. Diagnose Technical Issue**

Purpose: Get AI-powered diagnostic recommendations

Endpoint: diagnose_technical_issue

Parameters:
  - issue (required): Problem description
  - model (optional): Completion model to use
  - reranker (optional): Reranker model to use

```json
// Request
{
  "issue": "close to total failure - cooler condition - prediction: 3",
  "model": "us.amazon.nova-lite-v1:0"
}

// Response
{
  "diagnosis":"Based on the provided contexts from the manuals, the issue of a \"close to total failure - cooler condition - prediction: 3\" indicates that the oil cooler is severely inefficient and is likely to fail soon. Here is a step-by-step guide on how to solve this issue:\n\n### Immediate Actions to Take:\n\n1. **Shut Down the System**:\n   - To prevent further damage, immediately shut down the hydraulic system to avoid overheating and potential damage to other components.\n\n2. **Visual Inspection**:\n   - Perform a visual inspection of the oil cooler. Look for visible leaks, damage to the cooler core or fittings, and any debris or dirt on the fins that could be blocking airflow.\n\n### Detailed Steps to Resolve the Issue:\n\n1. **Clean the Cooler**:\n   - **Remove Dirt and Debris**: Use low-pressure compressed air or a soft brush to remove accumulated grime from the cooler fins. A light water spray can help dislodge stubborn mud, but avoid high-pressure washing which can bend the fins.\n   - **Professional Cleaning**: If the cooler is heavily soiled, consider professional cleaning methods such as ultrasonic cleaning.\n\n2. **Inspect the Cooler**:\n   - **Check for Corrosion and Leaks**: After cleaning, inspect the cooler for any signs of corrosion, leaks, or bent fins.\n   - **Tighten Fittings and Replace Seals**: Tighten any loose fittings and replace worn seals. Small holes or fin damage can be patched with epoxy, but major core leaks require immediate replacement.\n\n3. **Flow or Pressure Test**:\n   - **Verify Fluid Circulation**: Perform a flow or pressure test to ensure that the coolant or hydraulic fluid circulates correctly through the cooler. This will help confirm that the cooler is functioning properly after cleaning.\n\n4. **Oil Analysis**:\n   - **Check for Overheating By-products**: An oil analysis may reveal overheating by-products or degradation of additives, further indicating cooling loss.\n\n### Preventive Measures:\n\n1. **Ensure Free Airflow**:\n   - Make sure there is free airflow around the cooler and remove any obstructions from nearby structures.\n\n2. **Maintain Clean Hydraulic Oil**:\n   - Keep hydraulic oil clean and at the correct viscosity. Contaminated or degraded oil holds more heat and can clog coolers.\n\n3. **Regular Cleaning**:\n   - Schedule regular cleaning based on the environment. Dusty or mobile applications need more frequent service.\n\n### Final Step:\n\nIf the cooler condition is still at a value of 3 after cleaning and inspection, it is crucial to **replace the cooler immediately** to avoid further system damage. A failing cooler can lead to system overheating, poor performance, and rapid wear of other components.\n\nBy following these steps, you can address the issue of a failing oil cooler and prevent further damage to the hydraulic system."
}
```

**7. Generate Text with AI**

Purpose: Generate text using AI models

Endpoint: generate_text_with_ai

Parameters:
- text (required): Input prompt
- model (optional): AI model to use

```json
// Request
{
  "text": "Generate a brief explanation of what cooler condition prediction level 3 means in an industrial hydraulic system",
  "model": "bedrock/amazon.titan-text-lite-v1"
}

// Response
{
  "answer": "Coolant temperature prediction level 3 in an industrial hydraulic system indicates that the coolant temperature is predicted to be within +/- 10 °C of the setpoint..."
}
```

## Embedding Model

The embedding model is configured at indexing time via the `EMBEDDING_MODEL` environment variable (default: `voyage/voyage-3`). It is **not selectable from the UI** — changing the embedding model requires re-running `indexing.py` to re-embed all documents.

Supported providers (via LiteLLM):
```bash
# Voyage AI (default)
EMBEDDING_MODEL=voyage/voyage-3

# AWS Bedrock
EMBEDDING_MODEL=bedrock/amazon.titan-embed-text-v2:0

# Any other model supported by LiteLLM
EMBEDDING_MODEL=your-provider/model-name
```

> **Note:** The query embedding model must match the model used during indexing. Mismatched models produce vectors in different spaces, causing poor or broken search results.

## Troubleshooting

### Common Issues

**1. MongoDB Connection Issues:**
```bash
# Check if MongoDB is running
mongosh --eval "db.runCommand('ping')"

# Verify connection string
echo $MONGODB_URI
```

**2. Model Loading Issues:**
```bash
# Check if models exist
ls -la backend/models/

# Retrain models if missing
cd backend
python generate_models.py
```

**3. Port Conflicts:**
```bash
# Check if port is in use
lsof -i :5001

# Kill process if needed
kill -9 <PID>
```

**4. Environment Variable Issues:**
```bash
# Verify environment variables are set
env | grep -E "(MONGODB|FASTAPI|EMBEDDING|MODEL)"

# Set missing variables
export MONGODB_URI=mongodb://localhost:27017
```

### Logs

All backend services log to the console (stdout/stderr). There are no log files by default.

When running locally, logs appear in the terminal where each process was started. On ECS, logs are sent to CloudWatch (log group with 30-day retention).

## Development

### Testing



**Manual Testing:**
```bash
# Test health check
curl http://localhost:5001/health

# Test equipment prediction
curl -X POST "http://localhost:5001/api/predict" \
  -H "Content-Type: application/json" \
  -d '{
  "independent_variables": [174.89, 124.5, 1.04, 0.0, 8.54, 8.48, 2676.66, 3.02, 9.2, 54.14, 58.59, 55.78, 49.56, 0.74, 19.97, 1.54, 27.13],
  "model_identifier": "Logistic_Regression-cooler_condition"
}'

# Test diagnosis
curl "http://localhost:5001/api/diagnose?issue=cooler%20condition%20failure&model=us.amazon.nova-lite-v1:0"
```


