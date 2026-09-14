import os
import difflib
from pathlib import Path
from typing import Optional

def resolve_fuzzy_path(project_root: Path, raw_path: str, is_creation: bool = False) -> Optional[Path]:
    """
    Step-by-step walks and resolves a highly typo-ridden or hallucinated path layout.
    
    Args:
        project_root: The absolute Path of the project workspace.
        raw_path: The uncleaned string sent by the AI/Client.
        is_creation: If True, allows creating directories dynamically on the closest matching branch.
    """
    # 1. Normalize path slashes and eliminate absolute root indicators
    normalized = raw_path.replace("\\", "/").strip("/")
    segments = [s for s in normalized.split("/") if s]
    
    if not segments:
        return project_root

    current_cursor = project_root

    # 2. Iterate and fix every individual directory segment step-by-step along the path
    for i, segment in enumerate(segments):
        is_last_segment = (i == len(segments) - 1)
        
        # Collect all immediate child folders/files available at our current location
        try:
            children = list(current_cursor.iterdir())
        except (PermissionError, FileNotFoundError):
            return None

        # Separate items to ensure we don't accidentally match a folder name for a file target
        dirs = [c.name for c in children if c.is_dir() and c.name not in {'.git', '.pytest_cache', 'node_modules'}]
        files = [c.name for c in children if c.is_file()]

        # Determine our matching pool based on location depth
        if is_last_segment and not is_creation:
            # Looking for a file to read/patch
            choices = files + dirs
        else:
            # Looking for directories to descend into
            choices = dirs

        # Clean the segment slightly of backup characters before string matching
        clean_segment = segment.rstrip("~")

        # Attempt to match the segment against available real options
        best_match = None
        if choices:
            # 1st pass: Exact case-insensitive matching
            for choice in choices:
                if choice.lower() == clean_segment.lower():
                    best_match = choice
                    break
            
            # 2nd pass: Fallback to close Gestalt string distance matches
            if not best_match:
                matches = difflib.get_close_matches(clean_segment, choices, n=1, cutoff=0.3)
                if matches:
                    best_match = matches[0]

        if best_match:
            current_cursor = current_cursor / best_match
        else:
            # Match failed at this folder layer
            if is_creation:
                # If creating a file, generate the rest of the path branches exactly as requested
                current_cursor = current_cursor / segment
                if not is_last_segment:
                    current_cursor.mkdir(parents=True, exist_ok=True)
            else:
                # If reading/patching an existing item, we cannot proceed down a broken path branch
                return None

    return current_cursor
