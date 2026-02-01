# Auto ICD - Medical Coding Assistant

> AI-powered ICD-10 disease code prediction with comprehensive patient analysis

A production-grade **Model Context Protocol (MCP) server** that predicts ICD-10 disease codes based on patient demographics, vital signs, symptoms, and medical history. Integrates seamlessly with Claude Desktop for AI-assisted medical coding.

## 🌟 Features

- **Comprehensive Patient Analysis**: Demographics, vitals (BP, HR, temp, RR), symptoms, medical history, comorbidities
- **Intelligent Scoring**: Multi-factor probability scoring with confidence levels (High/Medium/Low)
- **Rich Predictions**: ICD-10 codes with matched symptoms, vital sign analysis, and detailed explanations
- **Claude Desktop Integration**: Three powerful tools accessible via MCP protocol
- **Production Ready**: Async processing, JSON schemas, error handling, full documentation

## 🚀 Quick Start

### Installation

```bash
# Navigate to project directory
cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD"

# Activate the virtual environment (already created)
source mcp_venv/bin/activate

# Verify installation
which auto-icd-mcp
```

### Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "auto-icd": {
      "command": "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/python",
      "args": ["-m", "auto_icd_mcp.server"]
    }
  }
}
```

Restart Claude Desktop and start using the tools!

## 📖 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete setup and usage guide
- **[mcp_server/README.md](mcp_server/README.md)** - Technical documentation
- **[mcp_server/QUICKSTART.md](mcp_server/QUICKSTART.md)** - Quick start guide
- **[mcp_server/CONFIGURATION_GUIDE.md](mcp_server/CONFIGURATION_GUIDE.md)** - Configuration help

## 🎯 Available Tools

### 1. predict_icd_codes
Predict ICD-10 codes based on comprehensive patient details:
- **Input**: Age, sex, vitals, symptoms, medical history, comorbidities
- **Output**: Top N predictions with probability scores, confidence levels, matched symptoms

### 2. get_icd_info
Look up detailed information for a specific ICD-10 code

### 3. search_icd_by_description
Search the ICD-10 database by disease name or symptoms

## 💡 Usage Examples

### Example 1: Diabetes Patient

Ask Claude:
```
Use predict_icd_codes for a 58-year-old male with:
- Height: 175 cm, Weight: 95 kg
- Blood pressure: 145/92 mmHg
- Symptoms: frequent urination, increased thirst, fatigue, blurred vision
- Comorbidities: hypertension, obesity
- Doctor specialty: ENDOCRINOLOGY
```

### Example 2: Respiratory Infection

Ask Claude:
```
Use predict_icd_codes for a 7-year-old female with:
- Temperature: 38.9°C
- Heart rate: 110 bpm
- Respiratory rate: 28 breaths/min
- Symptoms: cough, fever, difficulty breathing, chest pain
- Doctor specialty: PEDIATRICS
```

## 🧪 Testing

Run the example scripts to see the prediction engine in action:

```bash
cd mcp_server
source ../mcp_venv/bin/activate
python examples.py
```

## 📊 Example Output

```json
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
  "matching_explanation": "Matched 3 of 4 symptoms. Relevant vitals indicate obesity and hypertension. Patient demographics: 58 years old, male, BMI 31.02."
}
```

## 🛠️ Technical Stack

- Python 3.10+
- MCP SDK (Model Context Protocol)
- NumPy & scikit-learn
- Async/await architecture
- ICD-10 2020 database (70,000+ codes)

## ⚠️ Medical Disclaimer

**IMPORTANT**: This tool is for **informational and educational purposes ONLY**. It should **NEVER** be used as a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified healthcare providers.

## 📄 License

GPL-3.0 License - See [LICENSE.md](LICENSE.md)

## 👨‍💻 Author

**Siddharth Mohanty**
- Email: siddharthmohantywk@gmail.com
- GitHub: @sidmocodes

## 🙏 Acknowledgments

- ICD-10 Classification System (WHO)
- Model Context Protocol (Anthropic)

---

**Ready to use!** See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete setup instructions.

