# API Documentation

## Overview

This document provides detailed information about the Mixed Model DOE Analysis API endpoints, request/response formats, and integration guidelines.

## Base URL

- **Production**: `https://mixedmodeldoe-v1.onrender.com`
- **Local Development**: `http://localhost:8000`

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

## Endpoints

### 1. Health Check

#### `GET /runDOE`

Simple health check to verify API status.

**Response:**
```json
{
  "status": "ready"
}
```

### 2. File Upload Analysis

#### `POST /runDOE`

Upload CSV file for DOE analysis.

**Content-Type**: `multipart/form-data`

**Parameters:**
- `file` (required): CSV file containing DOE data

**Example Request:**
```bash
curl -X POST \
  -F "file=@sample_data.csv" \
  https://mixedmodeldoe-v1.onrender.com/runDOE
```

**Response:**
```json
{
  "status": "success",
  "input_file": "./input/sample_data.csv",
  "output_dir": "./outputDOE",
  "files": [
    "fullmodel_logworth.csv",
    "simplified_logworth.csv",
    "diagnostics_summary.csv"
  ]
}
```

### 3. JSON Base64 Analysis

#### `POST /runDOEjson`

Send CSV data as base64-encoded JSON.

**Content-Type**: `application/json`

**Request Body:**
```json
{
  "filename": "string",
  "file_b64": "string"
}
```

**Parameters:**
- `filename` (required): Original filename (for reference)
- `file_b64` (required): Base64-encoded CSV content

**Example Request:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test_data.csv",
    "file_b64": "ZHllMSxkeWUyLFRpbWUsVGVtcCxMdmFsdWU..."
  }' \
  https://mixedmodeldoe-v1.onrender.com/runDOEjson
```

### 4. AI Foundry Compatible Analysis

#### `POST /api/DoeAnalysis`

Advanced analysis endpoint optimized for AI Foundry integration.

**Content-Type**: `application/json`

**Request Body:**
```json
{
  "data": "string",
  "response_column": "string",
  "predictors": "string (optional)",
  "threshold": "number (optional, default: 1.5)",
  "force_full_dataset": "boolean (optional, default: true)"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `data` | string | Yes | Base64-encoded CSV data or raw CSV |
| `response_column` | string | Yes | Comma-separated response variables (e.g., "Lvalue,Avalue,Bvalue") |
| `predictors` | string | No | Comma-separated predictor variables |
| `threshold` | number | No | LogWorth threshold (default: 1.5) |
| `force_full_dataset` | boolean | No | Use complete dataset (default: true) |

**Important Notes:**
- `response_column` must be a comma-separated STRING, not an array
- For AI Foundry compatibility, always include the `threshold` parameter

**Example Request:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "data": "ZHllMSxkeWUyLFRpbWUsVGVtcCxMdmFsdWU...",
    "response_column": "Lvalue,Avalue,Bvalue",
    "predictors": "dye1,dye2,Time,Temp",
    "threshold": 1.5,
    "force_full_dataset": true
  }' \
  https://mixedmodeldoe-v1.onrender.com/api/DoeAnalysis
```

**Response:**
```json
{
  "status": "success",
  "summary": {
    "response_variables": ["Lvalue", "Avalue", "Bvalue"],
    "threshold": 1.5,
    "force_full_dataset": true,
    "analysis_completed": true
  },
  "input_file": "/tmp/temp_file.csv",
  "output_dir": "./outputDOE",
  "files": [
    "fullmodel_logworth.csv",
    "simplified_logworth.csv",
    "diagnostics_summary.csv",
    "mixed_model_variance_summary.csv"
  ]
}
```

## Error Handling

All endpoints return standardized error responses:

```json
{
  "status": "error",
  "message": "Error description"
}
```

### Common Error Codes

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters or missing data |
| 500 | Internal Server Error - Analysis failed or server error |

### Common Error Messages

- `"No file uploaded"` - File parameter missing in multipart request
- `"Invalid base64 data format"` - Malformed base64 data
- `"URL data input not supported yet"` - URL data input not implemented
- `"DOE analysis failed: [details]"` - Analysis engine error

## Data Format Requirements

### CSV Structure

Your CSV file should contain the following columns:

**Required Columns:**
- `dye1`, `dye2` - Dye concentration factors
- `Time`, `Temp` - Process parameter factors
- `Lvalue`, `Avalue`, `Bvalue` - Color response variables

**Example CSV:**
```csv
dye1,dye2,Time,Temp,Lvalue,Avalue,Bvalue
1.0,2.0,30,150,45.2,12.3,8.7
1.5,2.5,35,160,47.1,13.1,9.2
2.0,3.0,40,170,49.8,14.2,10.1
```

### Data Validation

- All numeric columns should contain valid numbers
- Missing values should be properly handled in your dataset
- Recommended dataset size: 20-1000 rows for optimal performance

## Rate Limiting

Currently, no rate limiting is implemented. For production use, consider implementing appropriate rate limiting based on your usage patterns.

## OpenAPI Specifications

Multiple OpenAPI specifications are available:

- `openapi.json` - Original file upload endpoint
- `openapi_runDOEjson.json` - JSON Base64 endpoint  
- `openapi_doe_analysis_ai_foundry.json` - AI Foundry compatible endpoint

## Integration Examples

### Python
```python
import requests
import base64

# Read CSV file
with open('data.csv', 'rb') as f:
    csv_data = base64.b64encode(f.read()).decode('utf-8')

# Call API
response = requests.post(
    'https://mixedmodeldoe-v1.onrender.com/api/DoeAnalysis',
    json={
        'data': csv_data,
        'response_column': 'Lvalue,Avalue,Bvalue',
        'threshold': 1.5
    }
)

result = response.json()
print(result)
```

### JavaScript
```javascript
// Convert file to base64
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = error => reject(error);
  });
};

// Call API
const analyzeData = async (csvFile) => {
  const base64Data = await fileToBase64(csvFile);
  
  const response = await fetch('https://mixedmodeldoe-v1.onrender.com/api/DoeAnalysis', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      data: base64Data,
      response_column: 'Lvalue,Avalue,Bvalue',
      threshold: 1.5
    })
  });
  
  return await response.json();
};
```

## Support

For API issues or questions:
1. Check the interactive documentation at `/docs`
2. Review this documentation
3. Contact the development team

---

*Last updated: August 2025*
