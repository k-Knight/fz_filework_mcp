import os
import shutil
import pytest
import time
from pathlib import Path
import subprocess
from mcp.client import Client

TEST_SANDBOX = Path("./test").resolve()
SERVER_ROOT_URL = "http://localhost:15432/mcp"

@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown_sandbox():
    """
    1. Creates a pristine isolated 'temp' directory layout.
    2. Changes directory (cd) directly into the test folder context.
    3. Background launches main.py in a NEW visible CMD window bound tightly to '.'.
    4. Automatically pops execution back, runs tests, kills server process, and sweeps 'temp'.
    """
    original_cwd = os.getcwd()
    main_script_path = Path("./main.py").resolve()

    if TEST_SANDBOX.exists():
        shutil.rmtree(TEST_SANDBOX)
    TEST_SANDBOX.mkdir(parents=True, exist_ok=True)
    
    os.chdir(TEST_SANDBOX)
    print(f"\n📂 Changed directory context -> {os.getcwd()}")

    server_process = subprocess.Popen(
        ["python", str(main_script_path), "."],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    print("🚀 Spawned background FuzzyPatcher MCP server in a NEW visible CMD window bound to '.'")
    
    time.sleep(5)

    yield
    
    print("\n🛑 Initiating Post-test teardown sequence...")
    
    try:
        server_process.terminate()
        server_process.wait(timeout=5)
        print("✅ Background server process terminated successfully.")
    except Exception as e:
        print(f"⚠️ Warning during server termination sequence: {e}")
        server_process.kill()

    os.chdir(original_cwd)
    print(f"📂 Changed directory context back -> {os.getcwd()}")
    
    if TEST_SANDBOX.exists():
        shutil.rmtree(TEST_SANDBOX)
        print(f"🧹 Successfully deleted testing sandbox directory tree structure.")

@pytest.fixture
def anyio_backend():
    """Forces pytest to use anyio asyncio runtime loops instead of standard pluggy packages."""
    return "asyncio"

@pytest.mark.anyio
async def test_touch_and_directory_creation_precision():
    """Test 1: Normal file creation along deep nested directories."""
    deep_path = "temp/src/components/buttons/SubmitButton.tsx"
    
    async with Client(SERVER_ROOT_URL) as client:
        result = await client.call_tool("fz_file_touch", {"path": deep_path})
        tool_output_text = result.content[0].text
        
        assert "SUCCESS" in tool_output_text
        expected_file = Path("temp/src/components/buttons/SubmitButton.tsx").resolve()
        assert expected_file.exists() and expected_file.is_file()

@pytest.mark.anyio
async def test_touch_resolves_deceptive_mismatched_paths():
    """Test 2: Verifies creating files passing anomalies like 'temp~' or '/temp' resolves to actual 'temp' directory."""
    
    async with Client(SERVER_ROOT_URL) as client:
        typo_path = "temp~/src/components/buttons/AbortButton.tsx"
        result_a = await client.call_tool("fz_file_touch", {"path": typo_path})
        
        output_text_a = result_a.content[0].text
        print(f"\n📢 Scenario A Response: {output_text_a}")
        assert "SUCCESS" in output_text_a
        
        expected_file_a = Path("temp/src/components/buttons/AbortButton.tsx").resolve()
        assert expected_file_a.exists() and expected_file_a.is_file()
        assert not Path("./temp~").exists()

        slash_path = "/temp/src/components/buttons/ApplyButton.tsx"
        result_b = await client.call_tool("fz_file_touch", {"path": slash_path})
        
        output_text_b = result_b.content[0].text
        print(f"📢 Scenario B Response: {output_text_b}")
        assert "SUCCESS" in output_text_b
        
        expected_file_b = Path("temp/src/components/buttons/ApplyButton.tsx").resolve()
        assert expected_file_b.exists() and expected_file_b.is_file()

@pytest.mark.anyio
async def test_diff_apply_resolves_severe_path_and_folder_typos():
    """
    Test 3: Populates content and runs three separate diff modifications.
    Validates that path resolution catches typos deep in the subdirectories
    (e.g., 'comp0nents', 'bttons', 'src1') during editing phase.
    """
    file_submit = Path("temp/src/components/buttons/SubmitButton.tsx").resolve()
    file_abort = Path("temp/src/components/buttons/AbortButton.tsx").resolve()
    file_apply = Path("temp/src/components/buttons/ApplyButton.tsx").resolve()

    file_submit.write_text("// Submit Component\nexport const Submit = () => {};\n", encoding="utf-8")
    file_abort.write_text("// Abort Component\nexport const Abort = () => {};\n", encoding="utf-8")
    file_apply.write_text("// Apply Component\nexport const Apply = () => {};\n", encoding="utf-8")

    async with Client(SERVER_ROOT_URL) as client:
        
        path_1 = "temp/src/components/buttons/SubmitButton.tsx"
        diff_1 = (
            "--- temp/src/components/buttons/SubmitButton.tsx\n"
            "+++ temp/src/components/buttons/SubmitButton.tsx\n"
            "@@ -2,1 +2,1 @@\n"
            "-export const Submit = () => {};\n"
            "+export const Submit = () => { console.log('Submitted!'); };\n"
        )
        res_1 = await client.call_tool("fz_file_diff_apply", {"path": path_1, "diff_content": diff_1})
        print(f"\n📢 Edit 1 Response: {res_1.content[0].text}")
        assert "SUCCESS" in res_1.content[0].text
        assert "console.log('Submitted!')" in file_submit.read_text(encoding="utf-8")

        path_2 = "temp~/src/comp0nents/bttons/AbortButton.tsx"
        diff_2 = (
            "--- temp~/src/comp0nents/bttons/AbortButton.tsx\n"
            "+++ temp~/src/comp0nents/bttons/AbortButton.tsx\n"
            "@@ -2,1 +2,1 @@\n"
            "-export const Abort = () => {};\n"
            "+export const Abort = () => { alert('Aborted process'); };\n"
        )
        res_2 = await client.call_tool("fz_file_diff_apply", {"path": path_2, "diff_content": diff_2})
        print(f"📢 Edit 2 Response: {res_2.content[0].text}")
        assert "SUCCESS" in res_2.content[0].text
        assert "alert('Aborted process')" in file_abort.read_text(encoding="utf-8")

        path_3 = "/temp/src1/components/butons/ApplyButton.tsx"
        diff_3 = (
            "--- /temp/src1/components/butons/ApplyButton.tsx\n"
            "+++ /temp/src1/components/butons/ApplyButton.tsx\n"
            "@@ -2,1 +2,1 @@\n"
            "-export const Apply = () => {};\n"
            "+export const Apply = () => { return true; };\n"
        )
        res_3 = await client.call_tool("fz_file_diff_apply", {"path": path_3, "diff_content": diff_3})
        print(f"📢 Edit 3 Response: {res_3.content[0].text}")
        assert "SUCCESS" in res_3.content[0].text
        assert "return true;" in file_apply.read_text(encoding="utf-8")

@pytest.mark.anyio
async def test_diff_apply_handles_flawed_and_fuzzy_diffs():
    """
    Test 4: Applies modified diffs with explicit mistakes to the files.
    - File 1 (SubmitButton): Broken string/quote escaping rules.
    - File 2 (AbortButton): Slight typos within the source line match text.
    - File 3 (ApplyButton): Drastically incorrect unified diff line numbers.
    """
    file_submit = Path("temp/src/components/buttons/SubmitButton.tsx").resolve()
    file_abort = Path("temp/src/components/buttons/AbortButton.tsx").resolve()
    file_apply = Path("temp/src/components/buttons/ApplyButton.tsx").resolve()

    file_submit.write_text("// Submit Header\nexport const Submit = () => { console.log('Submitted!'); };\n// Footer\n", encoding="utf-8")
    file_abort.write_text("// Abort Header\nexport const Abort = () => { alert('Aborted process'); };\n// Footer\n", encoding="utf-8")
    file_apply.write_text("// Apply Header\nexport const Apply = () => { return true; };\n// Footer\n", encoding="utf-8")

    async with Client(SERVER_ROOT_URL) as client:

        path_1 = "temp/src/components/buttons/SubmitButton.tsx"
        diff_1 = (
            "--- temp/src/components/buttons/SubmitButton.tsx\n"
            "+++ temp/src/components/buttons/SubmitButton.tsx\n"
            "@@ -2,1 +2,1 @@\n"
            "- export const Submit = () => { console.log('Submitted!'); }; \n"
            "+export const Submit = () => { console.log(\"Escaping \\\"Test\\\" 'Passed'\"); };\n"
        )
        res_1 = await client.call_tool("fz_file_diff_apply", {"path": path_1, "diff_content": diff_1})
        print(f"\n📢 Flawed Diff 1 (Escaping) Response: {res_1.content[0].text}")
        assert "SUCCESS" in res_1.content[0].text

        path_2 = "temp/src/components/buttons/AbortButton.tsx"
        diff_2 = (
            "--- temp/src/components/buttons/AbortButton.tsx\n"
            "+++ temp/src/components/buttons/AbortButton.tsx\n"
            "@@ -2,1 +2,1 @@\n"
            "-export const Abort = () => { alert('Ab0rted pr0cess'); };\n"
            "+export const Abort = () => { alert('Fuzzy Char Fix!'); };\n"
        )
        res_2 = await client.call_tool("fz_file_diff_apply", {"path": path_2, "diff_content": diff_2})
        print(f"📢 Flawed Diff 2 (Char Typo) Response: {res_2.content[0].text}")
        assert "SUCCESS" in res_2.content[0].text

        path_3 = "temp/src/components/buttons/ApplyButton.tsx"
        diff_3 = (
            "--- temp/src/components/buttons/ApplyButton.tsx\n"
            "+++ temp/src/components/buttons/ApplyButton.tsx\n"
            "@@ -99,1 +99,1 @@\n"
            "-export const Apply = () => { return true; };\n"
            "+export const Apply = () => { return 'Offset Fixed!'; };\n"
        )
        res_3 = await client.call_tool("fz_file_diff_apply", {"path": path_3, "diff_content": diff_3})
        print(f"📢 Flawed Diff 3 (Line Offset) Response: {res_3.content[0].text}")
        assert "SUCCESS" in res_3.content[0].text

        print("\n🔎 Verifying final file content states over network via exact string match...")

        read_submit = await client.call_tool("fz_file_read", {"path": "temp/src/components/buttons/SubmitButton.tsx"})
        assert read_submit.content[0].text == (
            "[SYSTEM NOTICE: Automatically resolved path 'temp/src/components/buttons/SubmitButton.tsx' -> 'temp/src/components/buttons/SubmitButton.tsx']\n\n"
            '// Submit Header\nexport const Submit = () => { console.log("Escaping \\"Test\\" \'Passed\'"); };\n// Footer\n'
        )

        read_abort = await client.call_tool("fz_file_read", {"path": "temp/src/components/buttons/AbortButton.tsx"})
        assert read_abort.content[0].text == (
            "[SYSTEM NOTICE: Automatically resolved path 'temp/src/components/buttons/AbortButton.tsx' -> 'temp/src/components/buttons/AbortButton.tsx']\n\n"
            "// Abort Header\nexport const Abort = () => { alert('Fuzzy Char Fix!'); };\n// Footer\n"
        )

        read_apply = await client.call_tool("fz_file_read", {"path": "/temp/src/components/buttons/ApplyButton.tsx"})
        assert read_apply.content[0].text == (
            "[SYSTEM NOTICE: Automatically resolved path '/temp/src/components/buttons/ApplyButton.tsx' -> 'temp/src/components/buttons/ApplyButton.tsx']\n\n"
            "// Apply Header\nexport const Apply = () => { return 'Offset Fixed!'; };\n// Footer\n"
        )

@pytest.mark.anyio
async def test_file_list_resolves_deceptive_paths():
    """
    Test 5: Validates fz_file_list exact raw string outputs.
    - Deep recursive listings matching all directory steps and files perfectly.
    - Shallow single-level listings matching targeted subdirectory snapshots.
    """
    async with Client(SERVER_ROOT_URL) as client:

        expected_recursive_output = (
            "temp/src/\n"
            "temp/src/components/\n"
            "temp/src/components/buttons/\n"
            "temp/src/components/buttons/AbortButton.tsx\n"
            "temp/src/components/buttons/ApplyButton.tsx\n"
            "temp/src/components/buttons/SubmitButton.tsx"
        )

        res_root_typo = await client.call_tool("fz_file_list", {"path": "temp~", "recursive": True})
        print(f"\n📢 Recursive Listing (temp~) Raw Output:\n{res_root_typo.content[0].text}")
        assert res_root_typo.content[0].text == expected_recursive_output

        res_root_slash = await client.call_tool("fz_file_list", {"path": "/temp", "recursive": True})
        print(f"📢 Recursive Listing (/temp) Raw Output:\n{res_root_slash.content[0].text}")
        assert res_root_slash.content[0].text == expected_recursive_output


        expected_shallow_output = "temp/src/components/"

        res_sub_typo1 = await client.call_tool("fz_file_list", {"path": "temp~/src", "recursive": False})
        print(f"📢 Shallow Listing (temp~/src) Raw Output:\n{res_sub_typo1.content[0].text}")
        assert res_sub_typo1.content[0].text == expected_shallow_output

        res_sub_typo2 = await client.call_tool("fz_file_list", {"path": "/temp/src", "recursive": False})
        assert res_sub_typo2.content[0].text == expected_shallow_output

        res_sub_typo3 = await client.call_tool("fz_file_list", {"path": "temp~/src~", "recursive": False})
        assert res_sub_typo3.content[0].text == expected_shallow_output

        res_sub_typo4 = await client.call_tool("fz_file_list", {"path": "/temp/src/", "recursive": False})
        assert res_sub_typo4.content[0].text == expected_shallow_output

        res_sub_typo5 = await client.call_tool("fz_file_list", {"path": "/temp/src~", "recursive": False})
        assert res_sub_typo5.content[0].text == expected_shallow_output
