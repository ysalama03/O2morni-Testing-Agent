# Testing Agent Flow Documentation

## Complete Workflow Overview

The testing agent follows a **4-Phase Human-in-the-Loop Testing Workflow**:

---

## Phase 1: Exploration & Knowledge Acquisition

**What happens:**

1. User provides a URL (e.g., `https://github.com/`)
2. Agent navigates to the URL and analyzes the page
3. Extracts page structure:
   - Forms (with inputs, IDs, names)
   - Buttons (with text, IDs, classes)
   - Links and navigation elements
   - Interactive elements
4. Creates `PageGroundTruth` objects for each explored URL
5. Stores locator information (selectors) for elements

**Output:** Ground truth data about page structure and element locators

---

## Phase 2: Collaborative Test Design

**What happens:**

1. Agent proposes test cases based on discovered forms/buttons
2. Focuses on "reasonable" URLs (sign-in, sign-up, checkout, etc.)
3. User reviews and approves/rejects test cases
4. Test cases are stored with steps like:
   - "Fill email with valid data"
   - "Click submit button"
   - "Wait for response"

**Output:** Approved test cases with step descriptions (not actual code yet)

---

## Phase 3: Implementation (Code Generation)

**What happens:**

1. User says "generate code" or "implement tests"
2. Agent uses `GenerateTestCodeTool` to generate Python Playwright code
3. Code generation process:
   - Takes approved test case steps
   - Uses LLM (code model) to generate Python code
   - Includes selectors from Phase 1 ground truth
   - Generates code like:
     ```python
     await page.goto("https://github.com/")
     await page.fill("[data-testid='email']", "test@example.com")
     await page.click("button[type='submit']")
     ```
4. **Code is saved to `generated_tests/test_tc_XXX.py` files**
5. Code may contain **incorrect selectors** (LLM guesses based on test steps)

**Output:** Python test files in `generated_tests/` directory

**Important:** The generated code may have wrong selectors because the LLM is guessing based on test case descriptions, not analyzing the actual page.

---

## Phase 4: Verification (Test Execution)

**What happens when you run tests:**

### Step 1: LLM-Based Selector Extraction (FIRST - Most Accurate) ✅

1. **Navigate to test URL** (if not already there)
2. **Extract HTML structure** from the actual page:
   - Gets forms, inputs, buttons with their HTML
   - Extracts element attributes (id, name, class, data-testid)
3. **Send to LLM** with:
   - Test case steps
   - Actual page HTML structure
   - Request: "Extract correct CSS selectors for each step"
4. **LLM analyzes** and returns correct selectors based on actual page elements
5. **Execute actions** using LLM-extracted selectors
6. **If successful:** Test completes, returns results

**Example:**

```
🤖 Trying LLM-based selector extraction (analyzing page HTML)...
📍 Navigated to https://github.com/login for LLM-based selector extraction
   ✓ LLM extracted 5 selectors from page HTML
  → Fill [name="login"] with test data
  → Fill [name="password"] with test data
  → Click [type="submit"]
✅ Executed 3 actions using LLM-extracted selectors
```

### Step 2: Regex Extraction (Fallback)

**If LLM extraction fails:**

1. Extract selectors from the generated Python code using regex
2. Looks for patterns like:
   - `page.goto("url")`
   - `page.fill("selector", "value")`
   - `page.click("selector")`
   - `page.wait_for_selector("selector")`
3. Execute actions using regex-extracted selectors
4. **Problem:** Selectors may be wrong if generated code had incorrect selectors

### Step 3: Basic Step Execution (Last Resort)

**If both LLM and regex fail:**

1. Parse test case step descriptions
2. Try to extract URLs, field names from text
3. Execute basic actions
4. **Limited functionality:** Can only do simple navigation and basic interactions

---

## Current Execution Flow (When Running Tests)

```
User: "run tests" or "run tests TC-001"
  ↓
execute_tests() called
  ↓
For each test:
  1. Load generated code from self.generated_code[test_id]
  2. Call _execute_generated_test_code()
     ↓
     STEP 1: Try LLM-based extraction (NEW - FIRST!)
     ├─ Navigate to test URL
     ├─ Extract page HTML
     ├─ Send HTML + test steps to LLM
     ├─ Get correct selectors from LLM
     ├─ Execute actions
     └─ ✅ SUCCESS → Return results
     ↓
     STEP 2: Fallback to regex extraction
     ├─ Parse generated Python code with regex
     ├─ Extract selectors from code
     ├─ Execute actions
     └─ ✅ SUCCESS → Return results
     ↓
     STEP 3: Fallback to basic step execution
     ├─ Parse test case step descriptions
     ├─ Try basic actions
     └─ Return results
  ↓
Return execution results
```

---

## Key Points

1. **Test Scripts are Created in Phase 3:**

   - Generated code is saved to `generated_tests/test_tc_XXX.py`
   - These files contain Python Playwright code
   - Selectors in these files may be incorrect

2. **LLM Extraction Runs in Phase 4 (Execution):**

   - **Always tries LLM extraction FIRST** when running tests
   - Analyzes actual page HTML (not the generated code)
   - Gets correct selectors based on real page elements
   - More accurate than regex extraction from potentially wrong code

3. **Why LLM First is Better:**
   - Generated code may have wrong selectors (LLM guesses during code generation)
   - LLM extraction analyzes actual page HTML (sees real elements)
   - Produces correct selectors that actually exist on the page
   - Reduces test failures due to incorrect selectors

---

## Example Flow

```
1. User: "test https://github.com/login"
   → Phase 1: Explores page, finds login form

2. User: "propose test cases"
   → Phase 2: Proposes "Valid form_0 Submission (login)"

3. User: "approve all"
   → Phase 2: Test case approved

4. User: "generate code"
   → Phase 3: Generates test_tc_001.py with code like:
      await page.fill("#email", "test")  ← May be wrong selector!

5. User: "run tests TC-001"
   → Phase 4: Execution
     → STEP 1: LLM extraction
        - Navigates to https://github.com/login
        - Extracts HTML: finds <input name="login" id="login_field">
        - LLM returns: selector = "[name='login']" or "#login_field"
        - Uses correct selector ✅
     → If LLM fails: Falls back to regex (extracts from code)
     → If regex fails: Falls back to basic steps
```

---

## Files Involved

- **Generated Test Files:** `generated_tests/test_tc_XXX.py`

  - Created in Phase 3
  - Contains Python Playwright code
  - May have incorrect selectors

- **Execution Code:** `backend/agents/llm_agent.py`

  - `_execute_generated_test_code()` - Main execution method
  - `_extract_selectors_using_llm()` - LLM-based selector extraction
  - Tries LLM first, then regex, then basic steps

- **Browser Control:** `backend/browser/browser_control.py`
  - `get_page_html()` - Extracts HTML structure for LLM analysis
  - `navigate_to()`, `click_element()`, `type_text()` - Executes actions
