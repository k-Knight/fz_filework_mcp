try {
    # Set environment variable to force Python engine into explicit UTF-8 mode
    $env:PYTHONUTF8 = "1"
    
    # Configure the standard stream profiles to utilize UTF-8 explicitly
    $OutputEncoding = [System.Text.Encoding]::UTF8
    [Console]::InputEncoding = [System.Text.Encoding]::UTF8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    
    $pythonPath = "C:\Users\k-Knight\Documents\Cline\Hooks\pre_tool_use.py"
    
    $rawInput = [Console]::In.ReadToEnd()
    
    # Pipe payload safely to the engine runtime
    $response = $rawInput | python $pythonPath
    
    Write-Output $response
} catch {
    @{
        cancel              = $true
        contextModification = ""
        errorMessage        = "[PreToolUse Proxy Exception Failed]: $($_.Exception.Message)"
    } | ConvertTo-Json -Compress
}
