import os
import difflib
from pathlib import Path
from typing import Optional

def resolve_fuzzy_path(project_root: Path, raw_path: str, is_creation: bool = False) -> Optional[Path]:
    """
    Step-by-step walks and resolves a highly typo-ridden or hallucinated path layout.
    Cleans up redundant root directory duplication, leading slashes, and handles creations.
    """
    # 1. Standardize slashes and clean surrounding white spaces
    clean_raw = raw_path.strip().replace("\\", "/")
    
    # Direct bypass loopback if the AI requests the current directory root
    if clean_raw in {".", "./", "", "/"}:
        return project_root

    # 2. Check for true OS Absolute Paths (contains Windows drive letter like C:)
    if len(clean_raw) > 1 and clean_raw[1] == ":":
        try:
            incoming_path = Path(clean_raw).resolve()
            if incoming_path == project_root:
                return project_root
            elif project_root in incoming_path.parents:
                clean_raw = incoming_path.relative_to(project_root).as_posix()
            else:
                return None  # Out-of-bounds security escape attempt
        except Exception:
            return None

    # 3. Clean root-relative leading slashes and extract path segments
    normalized = clean_raw.strip("/")
    segments = [s for s in normalized.split("/") if s]
    
    if not segments:
        return project_root

    # 4. CRITICAL FIX: Handle redundant root-folder prefix duplication hallucinations
    # If the first segment matches our project root folder name or its typo variants, drop it!
    root_folder_name = project_root.name.lower()  # e.g., "temp"
    first_seg_clean = segments[0].lower().rstrip("~")
    
    if first_seg_clean == root_folder_name:
        segments = segments[1:]
        
    if not segments:
        return project_root

    current_cursor = project_root

    # 5. Segment-by-segment fuzzy directory walk
    for i, segment in enumerate(segments):
        is_last_segment = (i == len(segments) - 1)
        
        if segment == ".":
            continue
            
        # For creations, simply append the target filename at the final layer
        if is_last_segment and is_creation:
            current_cursor = current_cursor / segment
            break

        try:
            if current_cursor.is_file():
                return None
            children = list(current_cursor.iterdir())
        except (PermissionError, FileNotFoundError):
            return None

        # Isolate child directory options
        dirs = [c.name for c in children if c.is_dir() and c.name not in {'.git', '.pytest_cache', 'node_modules'}]
        files = [c.name for c in children if c.is_file()]

        if is_last_segment:
            choices = files + dirs
        else:
            choices = dirs

        clean_segment = segment.rstrip("~")

        best_match = None
        if choices:
            # 1st pass: Case-insensitive match
            for choice in choices:
                if choice.lower() == clean_segment.lower():
                    best_match = choice
                    break
            # 2nd pass: Fallback string matching distance
            if not best_match:
                matches = difflib.get_close_matches(clean_segment, choices, n=1, cutoff=0.3)
                if matches:
                    best_match = matches[0]

        if best_match:
            current_cursor = current_cursor / best_match
        else:
            # Segment not found: create directories dynamically if in creation mode
            if is_creation:
                current_cursor = current_cursor / segment
                if not is_last_segment:
                    current_cursor.mkdir(parents=True, exist_ok=True)
            else:
                return None

    return current_cursor
