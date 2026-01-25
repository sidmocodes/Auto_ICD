# Auto ICD - MCP Server Deployment Guide

## 🎉 Production-Ready Medical Coding Assistant

A production-grade MCP (Model Context Protocol) server for ICD-10 disease code prediction that integrates with Claude Desktop and other MCP-compatible clients.

## Components

### 1. **Prediction Engine** ([predictor.py](mcp_server/auto_icd_mcp/predictor.py))
- **PatientDetails**: Structured patient data with automatic BMI and blood pressure categorization
- **ICDPrediction**: Rich prediction results with probability scores and explanations
- **EnhancedICDPredictor**: Advanced prediction algorithm that:
  - Matches patient symptoms to disease descriptions
  - Analyzes vital sign relevance
  - Considers comorbidities and medical history
  - Generates probability scores (0-1 scale)
  - Provides confidence levels (High/Medium/Low)
  - Creates detailed matching explanations

### 2. **MCP Server** ([server.py](mcp_server/auto_icd_mcp/server.py))
Three powerful tools accessible via Claude Desktop:

#### Tool 1: `predict_icd_codes`
Predicts ICD-10 codes based on comprehensive patient details:
- **Demographics**: Age, sex, BMI
- **Vital Signs**: Blood pressure, heart rate, temperature, respiratory rate
- **Clinical Data**: Symptoms, complaints, medical history, comorbidities
- **Returns**: Top N predictions with scores, matched symptoms, and explanations

#### Tool 2: `get_icd_info`
Look up detailed information for a specific ICD-10 code

#### Tool 3: `search_icd_by_description`
Search the ICD-10 database by disease name or symptoms

### 3. **Complete Documentation**
- [README.md](mcp_server/README.md): Comprehensive documentation
- [QUICKSTART.md](mcp_server/QUICKSTART.md): Quick setup guide
- [examples.py](mcp_server/examples.py): Working code examples

## Installation & Setup

### Step 1: Verify Installation
The MCP server is already installed! Verify it:

```bash
cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD"
source mcp_venv/bin/activate
which auto-icd-mcp
# Should output: /Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/auto-icd-mcp
```

### Step 2: Configure Claude Desktop

Add this to your Claude Desktop configuration file:

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json`

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

### Step 3: Restart Claude Desktop

After adding the configuration, completely restart Claude Desktop.

## Usage Examples

### Example 1: Diabetes Patient Assessment

**Ask Claude:**
```
Use the predict_icd_codes tool with this patient:
- 58 year old male
- Height: 175 cm, Weight: 95 kg  
- Blood pressure: 145/92 mmHg
- Heart rate: 78 bpm
- Symptoms: frequent urination, increased thirst, fatigue, blurred vision
- Comorbidities: hypertension, obesity
- Doctor specialty: ENDOCRINOLOGY
- Return top 10 predictions
```

### Example 2: Pediatric Respiratory Assessment

**Ask Claude:**
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

### Example 3: Search for Specific Conditions

**Ask Claude:**
```
Use search_icd_by_description to find ICD codes related to "myocardial infarction"
```

### Example 4: Code Lookup

**Ask Claude:**
```
Use get_icd_info to look up ICD code "I21.9"
```

## Testing Locally

Run the example scripts to see the prediction engine in action:

```bash
cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_server"
source ../mcp_venv/bin/activate
python examples.py
```

This will run 4 comprehensive examples demonstrating:
1. Diabetes patient with hypertension
2. Pediatric respiratory infection
3. Cardiac patient with chest pain
4. ICD code search functionality

## Technical Architecture

```
Auto_ICD/
├── mcp_server/              # MCP server implementation
│   ├── auto_icd_mcp/
│   │   ├── __init__.py
│   │   ├── server.py        # MCP server with 3 tools
│   │   └── predictor.py     # Prediction engine
│   ├── setup.py             # Package configuration
│   ├── requirements.txt     # Dependencies
│   ├── README.md            # Full documentation
│   ├── QUICKSTART.md        # Quick start guide
│   └── examples.py          # Usage examples
├── mcp_venv/                # Virtual environment
├── icd_list.json            # ICD-10 database (70,000+ codes)
└── counts.pickle            # Historical diagnosis data
```

## Key Capabilities

### 1. **Comprehensive Patient Analysis**
Complete patient profile including:
- Demographics (age, sex, BMI)
- Vital signs (BP, HR, temperature, respiratory rate)
- Multiple symptoms and primary complaints
- Comorbidities and medical history
- Doctor specialty context

### 2. **Intelligent Scoring**
Multi-factor probability scoring:
- Symptom matching (0-50%)
- Vital sign relevance (0-20% per vital)
- Historical patterns (0-50%)
- Comorbidity matching (15% each)

### 3. **Rich Results**
Detailed predictions including:
- Probability score (0-1)
- Confidence level (High/Medium/Low)
- List of matched symptoms
- Relevant vital signs with interpretations
- Detailed matching explanation

### 4. **Production-Ready Architecture**
- MCP server for integration with Claude
- Structured API with JSON schemas
- Async processing
- Comprehensive error handling
- Full documentation

## How the Prediction Algorithm Works

### 1. Data Loading
Loads ICD-10 database and historical diagnosis patterns

### 2. Patient Analysis
```python
# Automatically calculates derived metrics
BMI = weight_kg / (height_m ^ 2)
BP Category = categorize(systolic, diastolic)
```

### 3. Symptom Matching
```
For each ICD code:
  - Search description for patient symptoms
  - Calculate match percentage
  - Track which symptoms matched
```

### 4. Probability Calculation
```python
probability = (
    base_prob_from_history +          # 0-0.5
    (symptom_match_score * 0.5) +     # 0-0.5  
    (relevant_vitals * 0.2 each) +    # 0-0.4+
    (comorbidity_matches * 0.15 each) # 0-0.3+
)
# Capped at 1.0
```

### 5. Confidence Levels
- **High** (≥70%): Strong evidence across multiple factors
- **Medium** (40-69%): Moderate evidence  
- **Low** (<40%): Weak evidence, consider as differential

## Data Requirements

The server requires these files (already present):
- `icd_list.json`: 70,000+ ICD-10 codes with descriptions
- `counts.pickle`: Historical diagnosis frequency data

## Security & Privacy Considerations

⚠️ **Important**: This tool processes medical information. When deploying:

1. **Never** log patient data
2. **Always** use encrypted connections
3. **Consider** HIPAA compliance requirements
4. **Implement** access controls
5. **Maintain** audit logs
6. **Review** data retention policies

## Medical Disclaimer

⚠️ **CRITICAL**: This tool is for **informational and educational purposes ONLY**. It should **NEVER** be used as:
- A substitute for professional medical diagnosis
- The sole basis for treatment decisions
- Emergency medical assessment
- Replacement for clinical judgment

**Always** seek advice from qualified healthcare providers for medical decisions.

## Limitations

1. **Keyword-Based**: Relies on text matching, not medical reasoning
2. **No Lab Data**: Cannot incorporate lab results or imaging
3. **Static Database**: Uses ICD-10 2020 version
4. **Historical Bias**: Based on past diagnosis patterns
5. **Single Condition**: Doesn't model multiple concurrent conditions
6. **No Severity**: Doesn't assess condition severity

## Future Enhancements

Potential improvements:
1. **ML Integration**: Train models on symptom-diagnosis patterns
2. **Lab Results**: Include blood work, imaging findings
3. **Multi-Diagnosis**: Support for multiple concurrent conditions
4. **Severity Scoring**: Add condition severity assessment
5. **ICD-11**: Update to latest ICD-11 standard
6. **Drug Interactions**: Include medication analysis
7. **Differential Diagnosis**: Ranked differential diagnosis lists

## Troubleshooting

### Server Not Appearing in Claude

1. **Check Config Path**: Ensure python path in config is correct
2. **Verify Installation**: Run `auto-icd-mcp --help`
3. **Check Logs**: Look in Claude Desktop logs for errors
4. **Test Server**: Run `python -m auto_icd_mcp.server` manually
5. **Restart Claude**: Completely quit and restart Claude Desktop

### Prediction Issues

1. **Use Descriptive Symptoms**: "shortness of breath" vs "breathing"
2. **Multiple Symptoms**: Provide 3+ symptoms for better matching
3. **Include Vitals**: Add vital signs when available
4. **Check Spelling**: Verify symptom descriptions
5. **Try Variations**: Use different phrasings

### Performance Issues

1. **Reduce top_n**: Request fewer predictions (e.g., top 5 instead of 20)
2. **Limit Symptoms**: Focus on most relevant symptoms
3. **Check File Access**: Ensure icd_list.json and counts.pickle are accessible

## Support & Contribution

- **Author**: Siddharth Mohanty
- **Email**: siddharthmohantywk@gmail.com
- **GitHub**: @sidmocodes
- **Original Project**: Auto ICD (2019)

## License

MIT License - See [LICENSE.md](../LICENSE.md)

## Acknowledgments

- ICD-10 Classification System (WHO)
- Model Context Protocol (Anthropic)

---

## Quick Reference Card

### Installation Commands
```bash
cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD"
source mcp_venv/bin/activate
cd mcp_server
python examples.py  # Test the server
```

### Claude Desktop Config Location
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Python Path for Config
```
/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/python
```

### Available Tools in Claude
1. `predict_icd_codes` - Main prediction tool
2. `get_icd_info` - Look up specific ICD codes  
3. `search_icd_by_description` - Search by disease name

---

**🎊 Ready to use!** Start using the medical coding assistant in Claude Desktop by following the setup steps above.
