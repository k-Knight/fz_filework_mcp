# FZFileworkMCP Server

An MCP server designed for local LLMs (like Qwen 2.5 Coder) running inside Cline. It replaces default, rigid file-writing tools with typo-tolerant searching, resilient code patching via `mpatch`, and pre-execution evaluation hooks. This stops infinite token-burning retry loops caused by indentation shifts, broken diff syntax, or poor tool execution choices.

## Features
- **Cline Pre-Tool-Use Hook:** Integrates custom scripts to validate and optimize context before tools execute, drastically improving overall tool use reliability.
- **Deep Typo Resolution:** Resolves folder and file path typos at any depth step-by-step (e.g., `src1/comp0nents/bttons/` -> `src/components/buttons/`).
- **Resilient Diff Patching:** Uses a compiled Rust engine (`mpatch`) with an aggressive fuzz threshold (`0.5`) to force messy, malformed AI diffs to merge cleanly.
- **Clean File Listings:** Outputs flat, sorted file trees matching Linux `find` command syntax without leading `./` noise.

## Tools Included

1. `fz_file_read(path)` – Reads a file's contents directly with zero system notice wrapping. Misspellings at any depth will be resolved.
2. `fz_read_files(paths)` – Reads the contents of multiple files safely, returning clean, isolated file content containers. Misspellings are fuzzy-resolved individually.
3. `fz_file_touch(path)` – Touches/creates an empty file along the closest matching folder branches available.
4. `fz_file_diff_apply(path, diff_content)` – Maps an input unified diff block to a step-resolved path match and merges lines cleanly.
5. `fz_file_list(path, recursive)` – Lists all files and directories under a target path, resolving layout typos automatically.
6. `fz_search_grep(query)` – Searches file contents across the workspace for a specific text string or regex pattern.
7. `fz_file_search(query)` – Finds and lists files across the project workspace whose filenames or relative paths match the query pattern.

---

## Setup & Installation

### 1. Dependencies
```bash
pip install mcp[cli] pydantic mpatch pytest
```

### 2. Cline Pre-Tool-Use Hook Setup
The repository includes pre-tool-use optimization configurations to maximize LLM performance:
* `tool_use_rules/cline/PreToolUse.ps1` – PowerShell entry script for tool-execution orchestration.
* `tool_use_rules/cline/pre_tool_use.py` – Python execution guard managing system context evaluation.
* `tool_use_rules/cline/tool_use_rules.md` – Behavioral rulebook and prompt definitions enforced before tools execute.

### 3. Configuration (`cline_mcp_settings.json`)
```json
{
  "mcpServers": {
    "fuzzy-patcher-service": {
      "type": "streamableHttp",
      "url": "http://localhost:15432/mcp",
      "disabled": false,
      "alwaysAllow": [
        "fz_file_read",
        "fz_read_files",
        "fz_file_touch",
        "fz_file_diff_apply",
        "fz_file_list",
        "fz_search_grep",
        "fz_file_search"
      ]
    }
  }
}
```

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
