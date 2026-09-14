# FZFileworkMCP Server

An MCP server designed for local LLMs (like Qwen 2.5 Coder) running inside Cline. It replaces default, rigid file-writing tools with typo-tolerant searching and resilient code patching via `mpatch`. This stops infinite token-burning retry loops caused by indentation shifts or broken diff syntax.

## Features
- **Deep Typo Resolution:** Resolves folder and file path typos at any depth step-by-step (e.g., `src1/comp0nents/bttons/` -> `src/components/buttons/`).
- **Resilient Diff Patching:** Uses a compiled Rust engine (`mpatch`) with an aggressive fuzz threshold (`0.5`) to force messy, malformed AI diffs to merge cleanly.
- **Clean File Listings:** Outputs flat, sorted file trees matching Linux `find` command syntax without leading `./` noise.
- **Pre-Tool-Use Hook:** Includes a pre-execution hook infrastructure for Cline to dramatically improve tool-use reliability and validation before commands fire.

## Tools Included
1. `fz_file_list(path, recursive)` – Returns clean file paths, skipping noise directories.
2. `fz_file_touch(path)` – Creates empty files and builds missing directories automatically.
3. `fz_file_read(path)` – Reads file contents via typo-corrected paths.
4. `fz_file_diff_apply(path, diff_content)` – Systematically merges messy unified diffs directly onto code.

---

## Setup & Installation

### 1. Dependencies
```bash
pip install mcp[cli] pydantic mpatch pytest
```

### 2. Configuration (`cline_mcp_settings.json`)
```json
{
  "mcpServers": {
    "fuzzy-patcher-service": {
      "type": "streamableHttp",
      "url": "http://localhost:15432/mcp",
      "disabled": false,
      "alwaysAllow": [
        "fz_file_read",
        "fz_file_touch",
        "fz_file_diff_apply",
        "fz_file_list",
        "fz_search_grep",
        "fz_file_search",
        "fz_read_files"
      ]
    }
  }
}
```

### 3. Cline Pre-Tool-Use Hook Setup
To ensure strict tool validation and enhance reliability, add the Pre-Tool-Use hooks located in `tool_use_rules/cline/`. 
- **PowerShell Wrapper:** `tool_use_rules/cline/PreToolUse.ps1`
- **Python Execution Engine:** `tool_use_rules/cline/pre_tool_use.py`
- **Rule Definitions:** `tool_use_rules/cline/tool_use_rules.md`

---

## Running the Project

### Start Server
Run the server passing your project workspace absolute path:
```bash
python main.py "C:\Path\To\Your\Project"
```

### Run Tests
The verification script spawns its own server instance in a separate console window, runs isolated file tests inside a temporary `./temp` directory, validates exact text mutations, and cleans up everything automatically:
```bash
pytest -v -s -p no:asyncio .\test.py
```
