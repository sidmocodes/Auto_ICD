# Auto ICD - Production MCP Server

**AI-powered ICD-10 disease code prediction** integrated with Claude Desktop via Model Context Protocol (MCP).

## 🚀 Overview

This is a production-grade MCP server that provides AI-assisted medical coding through comprehensive patient analysis.

### Key Features
- **Integration with Claude Desktop** for AI-assisted diagnosis coding
- **Comprehensive patient analysis** including vitals, symptoms, comorbidities
- **Intelligent probability scoring** with confidence levels
- **Detailed explanations** of how symptoms match conditions
- **Three powerful tools** for medical coding workflows

## 📁 Project Structure

```
Auto_ICD/
├── mcp_server/                # Production MCP server
│   ├── auto_icd_mcp/
│   │   ├── server.py          # MCP server implementation
│   │   └── predictor.py       # Enhanced prediction engine
│   ├── README.md              # Full documentation
│   ├── QUICKSTART.md          # Quick setup guide
│   └── examples.py            # Usage examples
│
├── mcp_venv/                  # Virtual environment
├── DEPLOYMENT_GUIDE.md        # Complete deployment guide
├── icd_list.json              # ICD-10 database (70,000+ codes)
└── counts.pickle              # Historical diagnosis data
```

## 🎯 Quick Start

### For the MCP Server (Recommended)

1. **Server is already installed!** Just configure Claude Desktop:

2. **Add to Claude config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

3. **Restart Claude Desktop**

4. **Start using it!** Ask Claude:
```
Use the predict_icd_codes tool for a 45-year-old male with:
- Blood pressure: 150/95 mmHg
- Symptoms: headache, dizziness, chest pain
- Comorbidities: diabetes
```



## 🛠️ Available Tools in Claude

### 1. `predict_icd_codes`
Comprehensive disease prediction based on patient details:
- Demographics (age, sex, BMI)
- Vital signs (BP, heart rate, temperature, etc.)
- Symptoms and complaints
- Medical history and comorbidities
- Returns top N predictions with probability scores

### 2. `get_icd_info`
Look up detailed information for specific ICD-10 codes

### 3. `search_icd_by_description`
Search the database by disease name or symptoms

## 📊 Example Results

When you ask Claude to predict ICD codes, you get:

```json
{
  "icd_code": "I10",
  "description": "Essential (primary) hypertension",
  "probability_score": 0.875,
  "confidence_level": "High",
  "matched_symptoms": ["headache", "dizziness"],
  "related_vitals": {
    "blood_pressure": "150/95 mmHg (Stage 2 Hypertension)"
  },
  "matching_explanation": "Matched 2 of 3 reported symptoms. Relevant vital signs indicate Stage 2 Hypertension. Patient has comorbidity: diabetes."
}
```

## 🎓 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete setup and usage guide
- **[mcp_server/README.md](mcp_server/README.md)** - Technical documentation
- **[mcp_server/QUICKSTART.md](mcp_server/QUICKSTART.md)** - Quick start guide
- **[mcp_server/examples.py](mcp_server/examples.py)** - Working code examples

## ✨ Key Features

### Intelligent Scoring
- Multi-factor probability calculation
- Symptom matching algorithm
- Vital sign relevance analysis
- Historical pattern recognition
- Comorbidity consideration

### Rich Results
- Probability scores (0-1 scale)
- Confidence levels (High/Medium/Low)
- Matched symptoms tracking
- Vital sign interpretations
- Detailed matching explanations

### Production Ready
- MCP protocol compliance
- Async processing
- JSON schema validation
- Comprehensive error handling
- Full documentation

## ⚠️ Medical Disclaimer

**IMPORTANT**: This tool is for **informational and educational purposes ONLY**. It should **NEVER** be used as a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified health providers.

## 🧪 Testing

Test the MCP server locally:

```bash
cd mcp_server
source ../mcp_venv/bin/activate
python examples.py
```

This runs 4 comprehensive examples demonstrating the prediction engine.

## 📈 Key Capabilities

| Feature | Capability |
|---------|------------|
| Input | Full patient profile with demographics, vitals, symptoms |
| Vitals | BP, HR, temperature, respiratory rate |
| Scoring | Multi-factor probability with confidence levels |
| Output | Detailed predictions with matched symptoms and explanations |
| Integration | Claude Desktop via MCP protocol |
| Medical History | Comprehensive history and comorbidities tracking |

## 🔧 Tech Stack

- Python 3.10+
- MCP SDK (Model Context Protocol)
- NumPy & scikit-learn
- Async/await architecture
- JSON schema validation
- ICD-10 2020 database

## 👨‍💻 Author

**Siddharth Mohanty**
- Email: siddharthmohantywk@gmail.com
- GitHub: @sidmocodes

## 📄 License

MIT License - See [LICENSE.md](LICENSE.md)

## 🙏 Acknowledgments

- ICD-10 Classification System (WHO)
- Model Context Protocol (Anthropic)

---

## 🎯 Next Steps

1. ✅ **Server is installed** - No additional installation needed
2. 📝 **Configure Claude** - Add server to Claude Desktop config
3. 🔄 **Restart Claude** - Restart the application
4. 🚀 **Start using** - Ask Claude to predict ICD codes!

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

---

**Production-ready medical coding assistant powered by AI**
