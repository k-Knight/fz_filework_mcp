# CRITICAL OPERATIONS AND SECURITY PROHIBITIONS

1. EXPLICIT COMMAND EXECUTION BAN:
   - You are STRICTLY FORBIDDEN from using 'execute_command' or 'run_commands' to execute terminal commands.
   - You are STRICTLY PROHIBITED from running shell commands like 'dir', 'ls', or 'Get-ChildItem' to look up project files. 
   - Never attempt to compile code, run tests, install packages, or spin up terminals.
   - To inspect directory trees or check file locations, you MUST use 'fz_file_list' instead of any shell listing command.

2. NATIVE FILE ACCESS BAN:
   - You are STRICTLY FORBIDDEN from using the native tools: 'write_to_file', 'replace_in_file', 'read_file', and 'read_files'.
   - Attempting to access, read, or overwrite files using native extension tools is blocked.

3. EXPOSED FUZZY-PATCHER-SERVICE WORKFLOW:
   - To inspect directory trees or check file locations, you MUST use 'fz_file_list'.
   - To create a brand new file path tracker, you MUST use 'fz_file_touch' (creates an empty file).
   - To read or view the contents of an existing file, you MUST use 'fz_file_read'.
   - To read or view the contents of multiple files simultaneously, you MUST use 'fz_read_files'.
   - To modify, edit, or append code to an existing file, you MUST generate a standard Unified Diff/Patch format block and pass it to 'fz_file_diff_apply'. 

4. EXCEPTION FOR STRING HUNTING:
   - You are explicitly allowed to use the built-in native 'search_grep' tool when you need to hunt for internal text patterns or function references across multiple files in the workspace.
