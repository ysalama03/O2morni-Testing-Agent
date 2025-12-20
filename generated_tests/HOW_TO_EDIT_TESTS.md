# How to Edit and Refactor Test Code

This guide explains how to edit generated test code and refactor it using the agent.

## Method 1: Edit Files Directly (Recommended)

### Step 1: Export the Tests

1. After generating test code, type: **`export tests`**
2. Test files will be saved to the `generated_tests/` directory

### Step 2: Edit the Test File

1. Open the test file in your editor:
   - Example: `generated_tests/test_tc_001.py`
2. Make your edits directly in the file
3. Save the file

### Step 3: Load the Edited Code

1. Type: **`load test TC-001`** (replace TC-001 with your test ID)
2. The agent will load your edited code and update the test

### Step 4: Run the Test

1. Type: **`run tests TC-001`** to test your edited code
2. The agent will use your edited version

## Method 2: Use Refactor Command

### Step 1: Request Refactoring

Type: **`refactor TC-001: fix the login selector`**

The agent will:

- Read the current test code
- Apply your feedback
- Generate updated code
- Update the test automatically

### Step 2: Review and Run

- The refactored code will be shown in the chat
- Type: **`run tests TC-001`** to test the refactored code

## Example Workflow

```
1. Generate code → "Generate code"
2. Export tests → "Export tests"
3. Edit file → Open generated_tests/test_tc_001.py in your editor
4. Make changes → Edit the Playwright code
5. Save file → Save your changes
6. Load edited code → "load test TC-001"
7. Test it → "run tests TC-001"
```

## Tips

- **Always export first** before editing to ensure you have the latest code
- **Test after editing** to make sure your changes work
- **Use refactor for quick fixes** instead of manual editing
- **Check the generated_tests/ directory** for all exported test files

## File Locations

- **Test Files**: `generated_tests/test_tc_XXX.py`
- **Reports**: `reports/test_execution_report_*.json`
- **Screenshots**: `reports/screenshots_*/`
- **Videos**: `reports/videos_*/`
