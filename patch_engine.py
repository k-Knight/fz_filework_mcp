import mpatch
from pathlib import Path

def apply_unified_patch(target_file: Path, diff_content: str) -> tuple[bool, str]:
    """
    Systematically applies messy, hallucinated AI diff blocks to a target file
    using the official Python `mpatch.patch_content` binding.
    """
    try:
        # Read the current file contents off disk
        original_code = target_file.read_text(encoding='utf-8')
        
        # Execute the pythonic patch function passing configuration values as keyword args
        # fuzz_factor: 0.0 is exact match only, 1.0 is maximum relaxation
        new_code = mpatch.patch_content(
            diff_content, 
            original=original_code,
            fuzz_factor=0.5
        )
        
        # Write the successfully patched text back onto disk
        target_file.write_text(new_code, encoding='utf-8')
        return True, "Unified diff successfully matched and applied via mpatch!"
        
    except Exception as e:
        return False, f"Mpatch processing exception: {str(e)}"
