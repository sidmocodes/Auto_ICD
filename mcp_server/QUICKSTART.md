# Auto ICD MCP Server - Quick Start Guide

## Installation

1. **Navigate to the project directory**:
   ```bash
   cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD"
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv mcp_venv
   source mcp_venv/bin/activate
   ```

3. **Install the server**:
   ```bash
   cd mcp_server
   pip install -e .
   ```

## Configuration for Claude Desktop

### macOS Configuration

1. Open the configuration file:
   ```bash
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Add the server configuration:
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

3. Restart Claude Desktop

## Testing

Run the example scripts to verify everything works:

```bash
cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_server"
python examples.py
```

## Usage in Claude

Once configured, you can use these tools in Claude:

### Example Prompts

1. **Predict ICD codes**:
   ```
   Use the predict_icd_codes tool with this patient:
   - 45 year old female
   - Height: 165 cm, Weight: 70 kg
   - BP: 130/85
   - Symptoms: headache, dizziness, fatigue
   ```

2. **Look up a code**:
   ```
   Use get_icd_info to look up code "E11.9"
   ```

3. **Search for conditions**:
   ```
   Use search_icd_by_description to find codes related to "heart failure"
   ```

## Troubleshooting

If the server doesn't appear in Claude:
1. Check that the python path in the config is correct
2. Verify the virtual environment is created
3. Ensure all dependencies are installed
4. Restart Claude Desktop completely

## Next Steps

See the full README.md for:
- Detailed tool documentation
- More complex examples
- Technical architecture
- Development guidelines
