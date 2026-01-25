# Claude Desktop Configuration Guide

## Step-by-Step Setup

### 1. Locate the Configuration File

**macOS**: 
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### 2. Open the File

**macOS Terminal**:
```bash
# Create the file if it doesn't exist
mkdir -p ~/Library/Application\ Support/Claude
touch ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Open with default editor
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Or use VS Code:
```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### 3. Add the Configuration

If the file is **empty**, paste this entire content:

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

If the file **already has content**, add the `auto-icd` entry to the existing `mcpServers` section:

```json
{
  "mcpServers": {
    "existing-server": {
      "command": "...",
      "args": ["..."]
    },
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

### 4. Verify the Python Path

Make sure the path is correct for your system:

```bash
# Check that this path exists
ls -l "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/python"

# Should output something like:
# lrwxr-xr-x  1 user  staff  7 Jan 25 12:00 /Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/python -> python3
```

### 5. Save and Close

Save the file (Cmd+S in VS Code) and close it.

### 6. Restart Claude Desktop

**Important**: You must **completely quit** and restart Claude Desktop:

1. Quit Claude Desktop (Cmd+Q on macOS)
2. Wait 5 seconds
3. Reopen Claude Desktop

### 7. Verify Installation

Once Claude Desktop restarts, you should see the MCP server connected. You can verify by asking Claude:

```
What MCP tools do you have available?
```

Claude should list:
- `predict_icd_codes`
- `get_icd_info`
- `search_icd_by_description`

## Testing the Server

### Test 1: Simple Prediction

Ask Claude:
```
Use the predict_icd_codes tool with:
- 30 year old female
- Symptoms: headache, fever, fatigue
- Return top 5 predictions
```

### Test 2: Complex Patient

Ask Claude:
```
Use predict_icd_codes for:
- 55 year old male
- Height: 180 cm, Weight: 95 kg
- Blood pressure: 145/90 mmHg
- Heart rate: 85 bpm
- Symptoms: chest pain, shortness of breath, sweating
- Comorbidities: diabetes, hypertension
- Medical history: coronary artery disease
- Doctor specialty: CARDIOLOGY
- Return top 10 predictions
```

### Test 3: Code Lookup

Ask Claude:
```
Use get_icd_info to look up code "I21.9"
```

### Test 4: Search

Ask Claude:
```
Use search_icd_by_description to find codes related to "diabetes"
```

## Troubleshooting

### Server Not Appearing

**Problem**: MCP server doesn't show up in Claude

**Solutions**:
1. Check JSON syntax in config file (use a JSON validator)
2. Verify the Python path exists
3. Ensure you completely restarted Claude Desktop
4. Check Claude Desktop logs for errors

**Check logs on macOS**:
```bash
# View recent logs
cat ~/Library/Logs/Claude/mcp*.log
```

### Invalid JSON Error

**Problem**: Config file has syntax error

**Solution**: Validate your JSON at jsonlint.com or use:
```bash
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
```

### Server Starts But Errors

**Problem**: Server connects but tools don't work

**Solutions**:
1. Verify data files exist:
   ```bash
   ls -l "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/icd_list.json"
   ls -l "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/counts.pickle"
   ```

2. Test the server manually:
   ```bash
   cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD"
   source mcp_venv/bin/activate
   python -m auto_icd_mcp.server
   # Press Ctrl+C to stop
   ```

3. Run the examples:
   ```bash
   cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_server"
   source ../mcp_venv/bin/activate
   python examples.py
   ```

### Permissions Error

**Problem**: Permission denied when accessing files

**Solution**: Ensure the virtual environment has correct permissions:
```bash
chmod +x "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/python"
```

## Advanced Configuration

### Custom Environment Variables

If you need to pass environment variables to the server:

```json
{
  "mcpServers": {
    "auto-icd": {
      "command": "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/python",
      "args": [
        "-m",
        "auto_icd_mcp.server"
      ],
      "env": {
        "LOG_LEVEL": "DEBUG",
        "MAX_PREDICTIONS": "20"
      }
    }
  }
}
```

### Multiple Servers

You can have multiple MCP servers:

```json
{
  "mcpServers": {
    "auto-icd": {
      "command": "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/python",
      "args": ["-m", "auto_icd_mcp.server"]
    },
    "another-server": {
      "command": "/path/to/another/server",
      "args": ["arg1", "arg2"]
    }
  }
}
```

## Configuration Template

Copy this template and replace the path with your actual path:

```json
{
  "mcpServers": {
    "auto-icd": {
      "command": "/REPLACE/WITH/YOUR/PATH/mcp_venv/bin/python",
      "args": [
        "-m",
        "auto_icd_mcp.server"
      ],
      "env": {}
    }
  }
}
```

**Find your path**:
```bash
cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD"
pwd
# Use the output + "/mcp_venv/bin/python"
```

## Success Indicators

✅ **Configuration successful if**:
1. No errors when Claude Desktop starts
2. Claude lists the MCP tools when asked
3. Tools execute successfully when called
4. Predictions return valid ICD codes

❌ **Configuration failed if**:
1. Claude Desktop shows connection errors
2. Tools don't appear in tool list
3. Error messages when using tools
4. Claude says it doesn't have access to MCP servers

## Getting Help

If you're still having issues:

1. **Check the logs**: Look in Claude Desktop logs for specific errors
2. **Test manually**: Run `python -m auto_icd_mcp.server` to see if server starts
3. **Verify installation**: Run `auto-icd-mcp --help` to check if installed
4. **Review paths**: Double-check all file paths are correct
5. **Restart everything**: Restart both terminal and Claude Desktop

## Quick Reference

**Config file location (macOS)**:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Python path**:
```
/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_venv/bin/python
```

**Test command**:
```bash
cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD/mcp_server"
source ../mcp_venv/bin/activate
python examples.py
```

**Manual server start**:
```bash
cd "/Users/siddharthmohanty/Auto ICD code/Auto_ICD"
source mcp_venv/bin/activate
python -m auto_icd_mcp.server
```

---

**Ready to use!** Once configured, you can start asking Claude to predict ICD codes immediately.
