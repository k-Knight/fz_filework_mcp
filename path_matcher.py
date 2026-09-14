import os
import difflib
from pathlib import Path
from typing import List, Optional

def get_all_relative_paths(root: Path) -> List[str]:
    """Scans the directory for all files, returning them relative to the root (forward slashes)."""
    paths = []
    # Block testing caches and dynamic sandboxes from being used as target paths
    ignored_dirs = {'.git', 'node_modules', '.venv', '__pycache__', 'dist', 'build', '.cline', '.pytest_cache', 'temp'}
    for p in root.rglob('*'):
        if p.is_file():
            if any(ignored in p.parts for ignored in ignored_dirs):
                continue
            paths.append(p.relative_to(root).as_posix())
    return paths

def get_all_directories(root: Path) -> List[str]:
    """Scans and returns all relative directory paths inside the workspace root."""
    dirs = []
    # Explicitly block .pytest_cache here so it won't steal file creations
    ignored_dirs = {'.git', 'node_modules', '.venv', '__pycache__', 'dist', 'build', '.cline', '.pytest_cache', 'temp'}
    for p in root.rglob('*'):
        if p.is_dir():
            if any(ignored in p.parts for ignored in ignored_dirs):
                continue
            dirs.append(p.relative_to(root).as_posix())
    return dirs

def find_best_fuzzy_match(requested_path: str, choices: List[str]) -> Optional[str]:
    """Cleans up paths and uses SequenceMatcher to resolve depth and string mistakes."""
    normalized = requested_path.replace("\\", "/").strip("/")
    
    # Strip common fuzzy noise anomalies
    normalized = normalized.replace("temp~", "temp")
    normalized = normalized.rstrip("~")
    
    if not choices:
        return None

    # First check: Case-insensitive trailing match
    for choice in choices:
        if choice.lower() == normalized.lower() or choice.lower().endswith(normalized.lower()):
            return choice

    # Second check: Structural string gestalt distance matching
    matches = difflib.get_close_matches(normalized, choices, n=1, cutoff=0.2)
    return matches[0] if matches else None
