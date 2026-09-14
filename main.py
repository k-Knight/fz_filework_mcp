import sys
import re 
from typing import List
from mcp.types import TextContent
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
    """Reads a file's contents directly with zero system notice wrapping."""
    resolved_path = path_resolver.resolve_fuzzy_path(PROJECT_ROOT, path, is_creation=False)
    
    if not resolved_path or not resolved_path.exists() or not resolved_path.is_file():
        return f"ERROR: Could not resolve file path '{path}' down the directory tree."
    
    try:
        return resolved_path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return f"ERROR: Failed to read resolved file: {str(e)}"

@mcp.tool()
def fz_read_files(
    paths: Annotated[List[str], Field(description="The list of file paths to read. Misspellings or formatting anomalies will be fuzzy-resolved individually.")]
) -> List[TextContent]:
    """Reads the contents of multiple files safely, returning clean, isolated file content containers."""
    content_blocks = []
    
    for path in paths:
        resolved_path = path_resolver.resolve_fuzzy_path(PROJECT_ROOT, path, is_creation=False)
        
        if not resolved_path or not resolved_path.exists() or not resolved_path.is_file():
            content_blocks.append(TextContent(
                type="text",
                text=f"ERROR: Could not resolve file path '{path}' down the directory tree."
            ))
            continue
            
        try:
            content = resolved_path.read_text(encoding='utf-8', errors='replace')
            content_blocks.append(TextContent(type="text", text=content))
        except Exception as e:
            content_blocks.append(TextContent(
                type="text",
                text=f"ERROR: Failed to read resolved file '{path}': {str(e)}"
            ))

    return content_blocks

@mcp.tool()
def fz_file_touch(
    path: Annotated[str, Field(description="The folder structure and filename you want to create.")]
) -> str:
    """Touches/creates an empty file along the closest matching folder branches available."""
    resolved_path = path_resolver.resolve_fuzzy_path(PROJECT_ROOT, path, is_creation=True)
    
    if not resolved_path:
        return "ERROR: Path resolution failed for target creation space."
        
    try:
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.touch(exist_ok=True)
        return "SUCCESS"
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
        return "ERROR: Could not resolve target file path branch to apply patch."
    
    success, message = patch_engine.apply_unified_patch(resolved_path, diff_content)
    if success:
        return "SUCCESS"
    else:
        return f"ERROR: {message}"

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

@mcp.tool()
def fz_search_grep(
    query: Annotated[str, Field(description="The text query or regex pattern to search for inside all workspace files.")]
) -> str:
    """Searches file contents across the workspace for a specific text string or regex pattern."""
    ignored_dirs = {'.git', 'node_modules', '.venv', '__pycache__', 'dist', 'build', '.cline', '.pytest_cache'}
    output_lines = []
    
    try:
        compiled_regex = re.compile(query, re.IGNORECASE)
    except Exception:
        compiled_regex = re.compile(re.escape(query), re.IGNORECASE)

    for item in PROJECT_ROOT.rglob('*'):
        if not item.is_file():
            continue
        if any(ignored in item.parts for ignored in ignored_dirs):
            continue
            
        try:
            content_lines = item.read_text(encoding='utf-8', errors='replace').splitlines()
            for line_num, line in enumerate(content_lines, 1):
                if compiled_regex.search(line):
                    abs_path_str = item.resolve().as_posix()
                    root_path_str = PROJECT_ROOT.resolve().as_posix()
                    if abs_path_str.startswith(root_path_str):
                        rel_path = abs_path_str[len(root_path_str):].lstrip("/")
                    else:
                        rel_path = item.name
                    
                    if rel_path.startswith("temp/"):
                        rel_path = rel_path[5:]
                        
                    output_lines.append(f"{rel_path}:{line_num}: {line.strip()}")
        except Exception:
            continue

    if not output_lines:
        return f"No matches found for search pattern: '{query}'"
        
    return "\n".join(output_lines)

@mcp.tool()
def fz_file_search(
    query: Annotated[str, Field(description="The filename or partial path fragment pattern to locate inside the repository workspace tree.")]
) -> str:
    """Finds and lists files across the project workspace whose filenames or relative paths match the query pattern."""
    ignored_dirs = {'.git', 'node_modules', '.venv', '__pycache__', 'dist', 'build', '.cline', '.pytest_cache'}
    output_lines = []
    
    clean_query = query.strip().replace("\\", "/").lower()
    if not clean_query:
        return "ERROR: Empty file search query provided."

    for item in PROJECT_ROOT.rglob('*'):
        if not item.is_file():
            continue
        if any(ignored in item.parts for ignored in ignored_dirs):
            continue
            
        abs_path_str = item.resolve().as_posix()
        root_path_str = PROJECT_ROOT.resolve().as_posix()
        if abs_path_str.startswith(root_path_str):
            rel_path = abs_path_str[len(root_path_str):].lstrip("/")
        else:
            rel_path = item.name
            
        if rel_path.startswith("temp/"):
            rel_path = rel_path[5:]
        
        if clean_query in rel_path.lower() or clean_query in item.name.lower():
            output_lines.append(rel_path)

    if not output_lines:
        return f"No matching files discovered for layout query: '{query}'"
        
    return "\n".join(sorted(output_lines))

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=15432
    )
