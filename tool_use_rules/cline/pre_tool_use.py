import sys
import json
import traceback
from pathlib import Path

# Explicit log path
LOG_PATH = Path(r"C:\Users\k-Knight\Documents\Cline\Hooks\hook_debug.txt")

def log(message: str):
    """Appends clean UTF-8 text strings to the log file natively."""
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        pass

def main():
    try:
        # Force reconfiguring streams to UTF-8
        sys.stdin.reconfigure(encoding='utf-8', errors='substitute')
        sys.stdout.reconfigure(encoding='utf-8')
        
        # CRITICAL FIX: Read raw input, strip whitespace, AND clean leading BOM markers
        raw_input = sys.stdin.read().strip().lstrip('\ufeff')
        
        log("\n" + "="*50)
        log("=== NEW HOOK INVOCATION TRACE ===")
        log(f"Raw Input Payload:\n{raw_input}")

        if not raw_input:
            print(json.dumps({"cancel": False, "contextModification": "", "errorMessage": ""}))
            return

        data = json.loads(raw_input)
        requested_tool = data.get("preToolUse", {}).get("toolName", "")
        log(f"📥 Parsed Tool Target: '{requested_tool}'")

        cancel = False
        error_message = ""
        context_modification = ""

        # --- Case A: Native File Reads -> Clean Translation Routing ---
        if requested_tool in ("read_files", "read_file"):
            params = data.get("preToolUse", {}).get("parameters", {})
            target_paths = []
            
            # Extract target paths from standard parameters
            if "files" in params:
                try:
                    files_val = params["files"]
                    files_array = json.loads(files_val) if isinstance(files_val, str) and files_val.startswith("[") else files_val
                    for item in files_array:
                        if isinstance(item, dict) and "path" in item:
                            target_paths.append(item["path"])
                        else:
                            target_paths.append(str(item))
                except Exception:
                    pass
            elif "path" in params:
                target_paths.append(params["path"])

            # Map the native call to its matching fuzzy-patcher-service equivalent
            cancel = True
            if requested_tool == "read_files" or len(target_paths) > 1:
                paths_str = json.dumps(target_paths)
                error_message = f"MANDATORY ROUTING: Native multiple file reading is restricted."
                context_modification = (
                    f"CRITICAL: Do not use '{requested_tool}'. You must instead invoke your custom tool "
                    f"'fuzzy-patcher-service__fz_read_files' with paths='{paths_str}' immediately."
                )
                log(f"🔄 Routing: Directed Cline to fz_read_files for {target_paths}")
            else:
                single_path = target_paths[0] if target_paths else "."
                error_message = f"MANDATORY ROUTING: Native single file reading is restricted."
                context_modification = (
                    f"CRITICAL: Do not use '{requested_tool}'. You must instead invoke your custom tool "
                    f"'fuzzy-patcher-service__fz_file_read' with path='{single_path}' immediately."
                )
                log(f"🔄 Routing: Directed Cline to fz_file_read for '{single_path}'")

        # --- Case B: Terminal Explorer Execution (dir, ls) -> Custom List Routing ---
        elif requested_tool in ("execute_command", "run_commands", "run_command"):
            params = data.get("preToolUse", {}).get("parameters", {})
            command_string = params.get("command", "") or params.get("commands", "")
            
            clean_cmd = str(command_string).strip().lower().replace('"', '').replace("'", "")
            log(f"🔍 Normalized Terminal Command: '{clean_cmd}'")
            
            if clean_cmd in ("dir", "ls", "get-childitem"):
                # Get the workspace root from Cline's request payload or fallback safely to "."
                workspace_roots = data.get("workspaceRoots", [])
                target_workspace = workspace_roots[0] if workspace_roots else "."
                
                cancel = True
                error_message = f"MANDATORY ROUTING: Direct folder exploration via shell command execution is prohibited."
                context_modification = (
                    f"CRITICAL: Do not run terminal directory listing commands like '{clean_cmd}'. "
                    f"You must instead invoke your custom tool 'fuzzy-patcher-service__fz_file_list' "
                    f"with parameters path='{target_workspace}' and recursive='true' immediately."
                )
                log(f"🔄 Routing: Intercepted '{clean_cmd}', directing Cline to fz_file_list for '{target_workspace}'")
            else:
                cancel = True
                error_message = "HARD BLOCK: Using terminal command execution utilities is strictly prohibited by project configuration."
                log("❌ Status: Hard Blocked unverified generic shell execution task.")

        # --- Case C: Generic structural fallback blocks ---
        else:
            lower_tool = requested_tool.lower()
            if any(forbidden in lower_tool for forbidden in ["write", "replace", "command", "shell"]):
                cancel = True
                error_message = f"HARD BLOCK: Native tool '{requested_tool}' is prohibited. Use your custom fuzzy tools."
                log(f"❌ Status: Hard Blocked native file writing string pattern signature.")

        # Print clean output back to Cline
        response = {
            "cancel": cancel,
            "contextModification": context_modification,
            "errorMessage": error_message
        }
        print(json.dumps(response))

    except Exception as e:
        error_trace = traceback.format_exc()
        log(f"🚨 Critical Hook Exception Encountered:\n{error_trace}")
        print(json.dumps({
            "cancel": True,
            "contextModification": "",
            "errorMessage": f"[PreToolUse Python Hook Error]: {str(e)}"
        }))

if __name__ == "__main__":
    main()
