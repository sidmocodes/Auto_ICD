# Auto ICD MCP Server

A production-grade Model Context Protocol (MCP) server for ICD-10 disease code prediction based on comprehensive patient details.

## Overview

This MCP server transforms the original Auto ICD project into a professional medical coding tool that analyzes patient information to predict potential ICD-10 disease codes with probability scores and detailed explanations.

## Features

### 🏥 Comprehensive Patient Analysis
- **Demographics**: Age, sex, BMI calculation
- **Vital Signs**: Blood pressure, heart rate, temperature, respiratory rate
- **Clinical Data**: Symptoms, chief complaints, medical history, comorbidities
- **Specialty Context**: Doctor specialty for context-aware predictions

### 🎯 Intelligent Prediction
- **Probability Scoring**: Statistical analysis based on symptom matching and historical data
- **Confidence Levels**: High/Medium/Low confidence ratings
- **Symptom Matching**: Identifies which patient symptoms match each condition
- **Vital Sign Analysis**: Correlates vital signs with disease descriptions
- **Context Awareness**: Considers comorbidities and medical history

### 📊 Detailed Results
Each prediction includes:
- ICD-10 code and full description
- Probability score (0-1 scale)
- Confidence level
- List of matched symptoms
- Relevant vital signs with interpretations
- Detailed matching explanation

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Setup

1. **Clone or navigate to the repository**:
```bash
cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD"
```

2. **Create and activate a virtual environment**:
```bash
python3 -m venv mcp_venv
source mcp_venv/bin/activate  # On macOS/Linux
# or
mcp_venv\Scripts\activate  # On Windows
```

3. **Install the MCP server**:
```bash
cd mcp_server
pip install -e .
```

4. **Verify installation**:
```bash
auto-icd-mcp --help
```

## Configuration

### For Claude Desktop

Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "auto-icd": {
      "command": "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/python",
      "args": [
        "-m",
        "auto_icd_mcp.server"
      ],
      "env": {}
    }
  }
}
```

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "auto-icd": {
      "command": "C:\\Users\\YourUsername\\Auto ICD code\\Auto_ICD\\mcp_venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "auto_icd_mcp.server"
      ],
      "env": {}
    }
  }
}
```

After adding the configuration, restart Claude Desktop.

## Usage

### Available Tools

#### 1. predict_icd_codes

Predict ICD-10 disease codes based on comprehensive patient details.

**Required Parameters**:
- `age` (integer): Patient age in years
- `sex` (string): Patient biological sex ('M' or 'F')
- `symptoms` (array): List of symptoms the patient is experiencing

**Optional Parameters**:
- `height_cm` (number): Patient height in centimeters
- `weight_kg` (number): Patient weight in kilograms
- `systolic_bp` (integer): Systolic blood pressure in mmHg
- `diastolic_bp` (integer): Diastolic blood pressure in mmHg
- `heart_rate` (integer): Heart rate in beats per minute
- `temperature_c` (number): Body temperature in Celsius
- `respiratory_rate` (integer): Respiratory rate in breaths per minute
- `primary_complaints` (array): Primary complaints or chief concerns
- `medical_history` (array): Past medical conditions or surgeries
- `comorbidities` (array): Existing chronic conditions
- `doctor_specialty` (string): Medical specialty (e.g., 'CARDIOLOGY', 'GENERAL')
- `top_n` (integer): Number of top predictions to return (default: 10)

#### 2. get_icd_info

Get detailed information about a specific ICD-10 code.

**Parameters**:
- `code` (string): The ICD-10 code to look up (e.g., 'G91.2')

#### 3. search_icd_by_description

Search for ICD-10 codes by disease description or symptoms.

**Parameters**:
- `query` (string): Search query (disease name, symptom, or description)
- `limit` (integer): Maximum number of results to return (default: 20)

## Examples

### Example 1: Diabetes Patient with Hypertension

**Prompt to Claude**:
```
Use the predict_icd_codes tool with this patient data:
- 58 year old male
- Height: 175 cm, Weight: 95 kg
- Blood pressure: 145/92 mmHg
- Symptoms: frequent urination, increased thirst, fatigue, blurred vision
- Comorbidities: hypertension, obesity
- Doctor specialty: ENDOCRINOLOGY
```

**Expected Output Structure**:
```json
{
  "patient_summary": {
    "age": 58,
    "sex": "M",
    "bmi": 31.02,
    "bmi_category": "Obese",
    "blood_pressure_category": "Stage 2 Hypertension",
    "symptoms_count": 4,
    "comorbidities_count": 2
  },
  "predictions": [
    {
      "icd_code": "E11.9",
      "description": "Type 2 diabetes mellitus without complications",
      "probability_score": 0.875,
      "confidence_level": "High",
      "matched_symptoms": ["frequent urination", "increased thirst", "fatigue"],
      "related_vitals": {
        "bmi": "31.02 (Obese)",
        "blood_pressure": "145/92 mmHg (Stage 2 Hypertension)"
      },
      "matching_explanation": "Matched 3 of 4 reported symptoms: frequent urination, increased thirst, fatigue. Relevant vital signs: bmi: 31.02 (Obese); blood_pressure: 145/92 mmHg (Stage 2 Hypertension). Patient has comorbidities: hypertension, obesity. Patient demographics: 58 years old, M, BMI 31.02."
    }
  ],
  "total_predictions": 10
}
```

### Example 2: Pediatric Respiratory Infection

**Prompt to Claude**:
```
Use the predict_icd_codes tool for:
- 7 year old female
- Temperature: 38.9°C
- Heart rate: 110 bpm
- Respiratory rate: 28 breaths/min
- Symptoms: cough, fever, difficulty breathing, chest pain
- Primary complaints: persistent cough for 3 days
- Doctor specialty: PEDIATRICS
```

### Example 3: Search for a Specific Condition

**Prompt to Claude**:
```
Use the search_icd_by_description tool to find ICD codes related to "pneumonia"
```

### Example 4: Look Up a Code

**Prompt to Claude**:
```
Use the get_icd_info tool to look up code "G91.2"
```

## How It Works

### 1. Data Loading
- Loads ICD-10 code database from `icd_list.json`
- Loads historical diagnosis patterns from `counts.pickle`

### 2. Patient Analysis
- Calculates derived metrics (BMI, BP category)
- Normalizes and validates input data
- Combines all symptoms and complaints

### 3. Code Matching
- Searches ICD database for symptom matches
- Analyzes description text for keyword matching
- Scores each potential diagnosis

### 4. Probability Calculation
Base probability factors:
- **Historical Data** (0-0.5): Based on age, sex, and doctor specialty patterns
- **Symptom Matching** (0-0.5): Percentage of patient symptoms found in disease description
- **Vital Signs** (0-0.2 per vital): Relevance of vital sign abnormalities
- **Comorbidities** (0.15 each): Matching comorbid conditions

Total probability is capped at 1.0.

### 5. Confidence Levels
- **High** (≥0.7): Strong match across multiple factors
- **Medium** (0.4-0.69): Moderate match with some uncertainty
- **Low** (<0.4): Weak match, consider as differential diagnosis

### 6. Result Generation
- Sorts predictions by probability
- Generates detailed explanations
- Returns top N results

## Technical Architecture

```
mcp_server/
├── auto_icd_mcp/
│   ├── __init__.py          # Package initialization
│   ├── server.py            # MCP server implementation
│   └── predictor.py         # Disease prediction engine
├── pyproject.toml           # Python package configuration
└── package.json             # Node.js compatibility (optional)
```

### Key Components

1. **PatientDetails** (dataclass)
   - Structured patient information
   - Automatic BMI and BP categorization
   - Input validation

2. **ICDPrediction** (dataclass)
   - Prediction result structure
   - JSON serialization
   - Comprehensive metadata

3. **EnhancedICDPredictor** (class)
   - Core prediction engine
   - Symptom matching algorithm
   - Probability calculation
   - Explanation generation

4. **AutoICDMCPServer** (class)
   - MCP protocol implementation
   - Tool registration and handling
   - Async request processing

## Data Requirements

The server requires the following files in the parent directory:
- `icd_list.json`: ICD-10 code database (already present)
- `counts.pickle`: Historical diagnosis frequency data (already present)

## Limitations and Disclaimers

⚠️ **Medical Disclaimer**: This tool is for informational and educational purposes only. It should NOT be used as a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified health providers.

### Known Limitations
- Predictions are based on keyword matching and statistical patterns
- Does not incorporate lab results or imaging findings
- Limited to ICD-10 codes in the database (2020 version)
- Historical data may not reflect current medical practices
- Requires quality symptom descriptions for best results

## Development

### Running in Development Mode

```bash
cd mcp_server
python -m auto_icd_mcp.server
```

### Testing the Server

You can test the server using the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python -m auto_icd_mcp.server
```

### Adding New Features

To extend the server:
1. Add new methods to `EnhancedICDPredictor` class
2. Register new tools in `AutoICDMCPServer._setup_handlers()`
3. Update documentation

## Troubleshooting

### Server Not Appearing in Claude

1. Check configuration file path and JSON syntax
2. Verify virtual environment path is correct
3. Ensure all dependencies are installed
4. Restart Claude Desktop completely
5. Check Claude Desktop logs for errors

### Prediction Issues

1. Ensure symptoms are descriptive (e.g., "shortness of breath" vs "breathing")
2. Provide multiple symptoms for better matching
3. Include vital signs when relevant
4. Check for typos in symptom descriptions

### Performance Issues

- Reduce `top_n` parameter if responses are slow
- Consider limiting symptom count to most relevant ones
- Ensure data files (pickle, json) are accessible

## License

MIT License - See LICENSE.md in the root directory

## Author

**Siddharth Mohanty**
- Email: siddharthmohantywk@gmail.com
- GitHub: @sidmocodes

## Acknowledgments

- Original Auto ICD project (2019)
- ICD-10 classification system (WHO)
- Model Context Protocol (Anthropic)

## Version History

- **v1.0.0** (2026-01-25): Initial production release
  - Full MCP server implementation
  - Comprehensive patient analysis
  - Probability-based predictions
  - Detailed matching explanations
