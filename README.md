# Mixed Model DOE Analysis API

A FastAPI-based web service for performing Design of Experiments (DOE) analysis using Mixed Models, optimized for L*a*b color space data analysis.

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app:app --reload

# Access API documentation
http://localhost:8000/docs
```

### Cloud Deployment
- **Live API**: https://mixedmodeldoe-v1.onrender.com
- **API Docs**: https://mixedmodeldoe-v1.onrender.com/docs

## 📡 API Endpoints

### 1. `/runDOE` (POST) - File Upload
Upload CSV files directly through multipart/form-data.

```bash
curl -X POST -F "file=@your_data.csv" https://mixedmodeldoe-v1.onrender.com/runDOE
```

### 2. `/runDOEjson` (POST) - JSON + Base64
Send CSV data as base64-encoded JSON.

```json
{
  "filename": "data.csv",
  "file_b64": "ZHllMSxkeWUyLFRpbWUsVGVtcCxMdmFsdWU..."
}
```

### 3. `/api/DoeAnalysis` (POST) - AI Foundry Compatible ⭐
Optimized for AI Foundry/Copilot Studio integration.

```json
{
  "data": "base64_encoded_csv_data",
  "response_column": "Lvalue,Avalue,Bvalue",
  "threshold": 1.5,
  "force_full_dataset": true
}
```

## 🔧 Data Format

Your CSV should include these columns:
- `dye1`, `dye2` - Dye concentrations
- `Time`, `Temp` - Process parameters  
- `Lvalue`, `Avalue`, `Bvalue` - Color measurements (response variables)

Example:
```csv
dye1,dye2,Time,Temp,Lvalue,Avalue,Bvalue
1.0,2.0,30,150,45.2,12.3,8.7
1.5,2.5,35,160,47.1,13.1,9.2
```

## 🤖 AI Agent Integration

### For AI Foundry/Copilot Studio:
1. Use the OpenAPI schema: `openapi_doe_analysis_ai_foundry.json`
2. Endpoint: `/api/DoeAnalysis`
3. **Important**: `response_column` must be comma-separated STRING, not array

### Example AI Foundry Call:
```json
{
  "data": "base64_csv_here",
  "response_column": "Lvalue,Avalue,Bvalue",
  "threshold": 1.5
}
```

## 📊 Output Files

The analysis generates:
- `fullmodel_logworth.csv` - Complete model results
- `simplified_logworth.csv` - Simplified significant factors
- `diagnostics_summary.csv` - Model diagnostics
- `mixed_model_variance_summary.csv` - Variance components
- And more...

## 🛠 Development

### Project Structure
```
├── app.py                          # Main API server
├── app_documented.py               # Documented version
├── MixedModelDOE_Function_*.py     # Core analysis logic
├── requirements.txt                # Dependencies
├── openapi*.json                   # API schemas
└── README.md                       # This file
```

### Core Dependencies
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pandas`, `numpy` - Data processing
- `statsmodels` - Statistical modeling
- `scikit-learn` - Machine learning utilities

## 📈 Performance

- **Analysis time**: < 60 seconds for typical datasets
- **Memory usage**: < 1MB for most analyses
- **Supported data size**: Up to 10,000 rows

## 🔗 Related Projects

- [Feasibility Report](MixedModelDOE_AI_Agent_Feasibility_Report.md)
- [English Version](MixedModelDOE_AI_Agent_Feasibility_Report_EN.md)

## 📞 Support

For issues or questions, please check the API documentation at `/docs` or contact the development team.

---

**Version**: 2.0.0  
**Last Updated**: August 2025
