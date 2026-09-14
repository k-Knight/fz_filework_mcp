import sys
import argparse
from pathlib import Path
from typing import Annotated

from pydantic import Field

from mcp.server.mcpserver import MCPServer

import path_resolver
import path_matcher
import patch_engine

parser = argparse.ArgumentParser(description="Fuzzy Path-Correcting MCP Server for v2.x.")
parser.add_argument("root_dir", type=str, help="Absolute path to the Windows project root directory")
args = parser.parse_args()

PROJECT_ROOT = Path(args.root_dir).resolve()
if not PROJECT_ROOT.exists() or not PROJECT_ROOT.is_dir():
    print(f"❌ Error: Root directory '{PROJECT_ROOT}' does not exist or is not a folder.", file=sys.stderr)
    sys.exit(1)

print(f"🚀 Initializing Modular Fuzzy MCP Server (v2.x) bound to: {PROJECT_ROOT}")

mcp = MCPServer(
    name="FuzzyPatcher"
)

@mcp.tool()
def fz_file_read(
    path: Annotated[str, Field(description="The file path to read. Misspellings at any depth will be resolved.")]
) -> str:
    """Reads a file's contents by resolving typos step-by-step through every subfolder."""
    resolved_path = path_resolver.resolve_fuzzy_path(PROJECT_ROOT, path, is_creation=False)
    
    if not resolved_path or not resolved_path.exists() or not resolved_path.is_file():
        return f"ERROR: Could not resolve file path '{path}' down the directory tree."
    
    try:
        content = resolved_path.read_text(encoding='utf-8', errors='replace')
        rel_match = resolved_path.relative_to(PROJECT_ROOT).as_posix()
        return f"[SYSTEM NOTICE: Automatically resolved path '{path}' -> '{rel_match}']\n\n{content}"
    except Exception as e:
        return f"ERROR: Failed to read resolved file: {str(e)}"


@mcp.tool()
def fz_file_touch(
    path: Annotated[str, Field(description="The folder structure and filename you want to create.")]
) -> str:
    """Touches/creates an empty file along the closest matching folder branches available."""
    resolved_path = path_resolver.resolve_fuzzy_path(PROJECT_ROOT, path, is_creation=True)
    
    if not resolved_path:
        return f"ERROR: Path resolution failed for target creation space '{path}'."
        
    try:
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.touch(exist_ok=True)
        rel_match = resolved_path.relative_to(PROJECT_ROOT).as_posix()
        return f"SUCCESS: Target folder structure resolved.\nRequested: '{path}'\nTouched at: '{rel_match}'"
    except Exception as e:
        return f"ERROR: Failed touching file at destination: {str(e)}"

@mcp.tool()
def fz_file_diff_apply(
    path: Annotated[str, Field(description="The file path target for the code patch. Mismatched folders will be resolved.")],
    diff_content: Annotated[str, Field(description="The raw unified diff/patch content block containing the changes.")]
) -> str:
    """Maps an input unified diff block to a step-resolved path match and merges lines cleanly."""
    resolved_path = path_resolver.resolve_fuzzy_path(PROJECT_ROOT, path, is_creation=False)
    
    if not resolved_path or not resolved_path.exists() or not resolved_path.is_file():
        return f"PATCH FAILED: Could not resolve file path branch for '{path}'."
    
    success, message = patch_engine.apply_unified_patch(resolved_path, diff_content)
    rel_match = resolved_path.relative_to(PROJECT_ROOT).as_posix()
    if success:
        return f"SUCCESS: [Fuzzy Fixed Target -> '{rel_match}']: {message}"
    else:
        return f"ERROR: [Fuzzy Fixed Target -> '{rel_match}']: {message}"

@mcp.tool()
def fz_file_list(
    path: Annotated[str, Field(description="The directory path to list files from.")] = ".",
    recursive: Annotated[bool, Field(description="Whether to scan subfolders recursively.")] = True
) -> str:
    """Lists all files and directories under a target path, resolving layout typos automatically."""
    resolved_path = path_resolver.resolve_fuzzy_path(PROJECT_ROOT, path, is_creation=False)
    
    if not resolved_path or not resolved_path.exists() or not resolved_path.is_dir():
        return f"ERROR: Target directory '{path}' could not be resolved."

    ignored_dirs = {'.git', 'node_modules', '.venv', '__pycache__', 'dist', 'build', '.cline', '.pytest_cache'}
    output_lines = []
    pattern = "**/*" if recursive else "*"
    
    for item in resolved_path.glob(pattern):
        if any(ignored in item.parts for ignored in ignored_dirs):
            continue
            
        rel_to_root = item.relative_to(PROJECT_ROOT).as_posix()
        
        if item.is_file():
            output_lines.append(rel_to_root)
        elif item.is_dir():
            output_lines.append(f"{rel_to_root}/")

    if not output_lines:
        rel_root = resolved_path.relative_to(PROJECT_ROOT).as_posix()
        return f"{rel_root}/" if rel_root and rel_root != "." else ""
        
    return "\n".join(sorted(output_lines))

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=15432
    )
