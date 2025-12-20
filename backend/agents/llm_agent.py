"""
LLM Agent Module
Implements smolagents-based web testing agent with multi-model architecture
following the 4-Phase Human-in-the-Loop Testing Workflow:

Phase 1: Exploration & Knowledge Acquisition
Phase 2: Collaborative Test Design
Phase 3: Implementation (Code Generation)
Phase 4: Verification & Trust Building

Models:
- Qwen2-VL-72B for visual web reasoning
- DeepSeek-Coder-V2-Instruct for test code generation
- Llama-3.1-70B-Instruct for orchestration and general reasoning
"""

import os
import re
import json
import base64
from io import BytesIO
from time import sleep, time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from PIL import Image

from smolagents import CodeAgent, Tool, tool, InferenceClientModel, LiteLLMModel
from smolagents.agents import ActionStep

from routes.chat_routes import truncate_screenshot


# ============================================================================
# WORKFLOW PHASE DEFINITIONS
# ============================================================================

class WorkflowPhase(Enum):
    """Enum representing the 4 phases of the testing workflow"""
    IDLE = "idle"
    EXPLORATION = "exploration"           # Phase 1: Understand the page
    COLLABORATIVE_DESIGN = "design"       # Phase 2: Plan test cases with human
    IMPLEMENTATION = "implementation"      # Phase 3: Generate test code
    VERIFICATION = "verification"          # Phase 4: Execute and validate


@dataclass
class PageElement:
    """Represents a discovered page element with locator strategies"""
    tag: str
    text: str
    element_type: str  # button, input, link, form, etc.
    locators: Dict[str, str]  # id, css, xpath, semantic
    attributes: Dict[str, str]
    is_interactive: bool
    description: str


@dataclass
class TestCase:
    """Represents a proposed test case"""
    id: str
    name: str
    description: str
    preconditions: List[str]
    steps: List[str]
    expected_results: List[str]
    priority: str  # high, medium, low
    status: str  # proposed, approved, rejected, needs_revision
    human_feedback: Optional[str] = None


@dataclass
class PageGroundTruth:
    """Structured representation of page analysis (Phase 1 output)"""
    url: str
    title: str
    description: str
    elements: List[PageElement]
    forms: List[Dict]
    navigation: List[Dict]
    interactive_areas: List[Dict]
    screenshot_b64: Optional[str] = None
    dom_summary: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass 
class TestExecutionResult:
    """Result of test execution (Phase 4 output)"""
    test_name: str
    status: str  # passed, failed, error
    duration_ms: float
    steps_executed: List[Dict]
    screenshots: List[str]  # base64 encoded
    error_message: Optional[str] = None
    video_path: Optional[str] = None


@dataclass
class MetricsTracker:
    """Tracks real-time metrics for response time and token usage"""
    total_requests: int = 0
    total_response_time_ms: float = 0
    total_tokens_consumed: int = 0
    request_times: List[float] = field(default_factory=list)
    token_counts: List[int] = field(default_factory=list)
    
    @property
    def average_response_time(self) -> float:
        if not self.request_times:
            return 0
        return sum(self.request_times) / len(self.request_times)
    
    @property
    def tokens_per_request(self) -> float:
        if self.total_requests == 0:
            return 0
        return self.total_tokens_consumed / self.total_requests
    
    def record_request(self, response_time_ms: float, tokens: int = 0):
        self.total_requests += 1
        self.total_response_time_ms += response_time_ms
        self.total_tokens_consumed += tokens
        self.request_times.append(response_time_ms)
        self.token_counts.append(tokens)
        # Keep only last 100 for moving average
        if len(self.request_times) > 100:
            self.request_times = self.request_times[-100:]
            self.token_counts = self.token_counts[-100:]
    
    def to_dict(self) -> Dict:
        avg_ms = 0 if self.total_response_time_ms == 0 else self.total_response_time_ms / self.total_requests
        return {
            'total_requests': self.total_requests,
            'average_response_time_ms': round(avg_ms, 2),
            "average_response_time": round(avg_ms / 1000, 2),
            'total_tokens_consumed': self.total_tokens_consumed,
            'tokens_per_request': round(self.tokens_per_request, 2),
            'last_response_time_ms': self.request_times[-1] if self.request_times else 0
        }


# ============================================================================
# PHASE 1: EXPLORATION TOOLS
# Tools for analyzing page structure, DOM, and creating ground truth
# ============================================================================

class ExplorePageTool(Tool):
    """Tool for deep exploration of a webpage - Phase 1"""
    name = "explore_page"
    description = """
    Performs deep exploration of a webpage to understand its structure.
    Analyzes the DOM, identifies interactive elements, forms, navigation,
    and creates a structured 'ground truth' representation.
    Use this as the FIRST step when given a URL to test.
    """
    inputs = {
        "url": {
            "type": "string",
            "description": "The URL to explore and analyze"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, url: str) -> Dict:
        # Check if we're already on the correct page (navigation already done by start_exploration)
        current_url = self.browser_controller.page.url if self.browser_controller.page else None
        
        # Only navigate if we're not already on the page
        if not current_url or not current_url.startswith(url.rstrip('/')):
            nav_result = self.browser_controller.navigate_to(url)
            if not nav_result.get('success'):
                return {'success': False, 'error': f"Failed to navigate: {nav_result.get('error')}"}
            sleep(1)  # Allow page to fully load
        
        # Comprehensive DOM analysis script
        analysis_script = """
        (() => {
            const result = {
                title: document.title,
                url: window.location.href,
                forms: [],
                buttons: [],
                inputs: [],
                links: [],
                navigation: [],
                headings: [],
                images: [],
                tables: [],
                interactive_elements: []
            };
            
            // Analyze forms
            document.querySelectorAll('form').forEach((form, idx) => {
                const formData = {
                    id: form.id || `form_${idx}`,
                    action: form.action,
                    method: form.method,
                    inputs: []
                };
                form.querySelectorAll('input, select, textarea').forEach(input => {
                    formData.inputs.push({
                        type: input.type || input.tagName.toLowerCase(),
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder,
                        required: input.required,
                        locator_id: input.id ? `#${input.id}` : null,
                        locator_name: input.name ? `[name="${input.name}"]` : null
                    });
                });
                result.forms.push(formData);
            });
            
            // Analyze buttons
            document.querySelectorAll('button, input[type="submit"], input[type="button"], [role="button"]').forEach((btn, idx) => {
                result.buttons.push({
                    text: btn.textContent?.trim().substring(0, 50) || btn.value || '',
                    type: btn.type || 'button',
                    id: btn.id,
                    class: btn.className,
                    locator_id: btn.id ? `#${btn.id}` : null,
                    locator_text: btn.textContent?.trim() ? `text=${btn.textContent.trim().substring(0, 30)}` : null,
                    locator_css: btn.className ? `.${btn.className.split(' ')[0]}` : `button:nth-of-type(${idx + 1})`
                });
            });
            
            // Analyze inputs (outside forms)
            document.querySelectorAll('input:not(form input), textarea:not(form textarea)').forEach(input => {
                result.inputs.push({
                    type: input.type || 'text',
                    name: input.name,
                    id: input.id,
                    placeholder: input.placeholder,
                    locator_id: input.id ? `#${input.id}` : null,
                    locator_name: input.name ? `[name="${input.name}"]` : null
                });
            });
            
            // Analyze links
            document.querySelectorAll('a[href]').forEach(link => {
                if (link.textContent?.trim()) {
                    result.links.push({
                        text: link.textContent.trim().substring(0, 50),
                        href: link.href,
                        id: link.id,
                        locator_text: `text=${link.textContent.trim().substring(0, 30)}`
                    });
                }
            });
            
            // Analyze navigation
            document.querySelectorAll('nav, [role="navigation"]').forEach((nav, idx) => {
                result.navigation.push({
                    id: nav.id || `nav_${idx}`,
                    links: Array.from(nav.querySelectorAll('a')).map(a => ({
                        text: a.textContent?.trim(),
                        href: a.href
                    })).slice(0, 10)
                });
            });
            
            // Analyze headings for page structure
            document.querySelectorAll('h1, h2, h3').forEach(h => {
                result.headings.push({
                    level: h.tagName,
                    text: h.textContent?.trim().substring(0, 100)
                });
            });
            
            // Find interactive elements
            document.querySelectorAll('[onclick], [data-action], [tabindex]:not([tabindex="-1"])').forEach(el => {
                result.interactive_elements.push({
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent?.trim().substring(0, 50),
                    id: el.id,
                    class: el.className
                });
            });
            
            return result;
        })()
        """
        
        dom_result = self.browser_controller.evaluate_script(analysis_script)
        if not dom_result.get('success'):
            return {'success': False, 'error': "Failed to analyze page."}

        # 1. Save the huge data to an internal variable for later use
        res = dom_result.get('result')
        self.browser_controller.last_ground_truth = res
        
        # 2. Trigger the screenshot save-to-disk
        self.browser_controller.capture_screenshot(name="exploration")

        # 3. RETURN ONLY A SUMMARY TO THE LLM
        summary = (f"Exploration successful. Page Title: '{res.get('title', 'No Title')}'. "
                   f"Found {len(res.get('buttons', []))} buttons, {len(res.get('inputs', []))} inputs, "
                   f"and {len(res.get('forms', []))} forms.")

        # FIX: RETURN A DICTIONARY
        return {
            'success': True,
            'ground_truth': res,
            'screenshot': self.browser_controller.last_screenshot_b64,
            'message': summary
        }


class AnalyzeElementsTool(Tool):
    """Tool for detailed analysis of specific elements"""
    name = "analyze_elements"
    description = """
    Analyzes specific elements on the page to determine the best locator strategy.
    Returns multiple locator options (ID, CSS, XPath, semantic) for each element.
    Use this to find reliable selectors for test implementation.
    """
    inputs = {
        "element_description": {
            "type": "string",
            "description": "Description of elements to analyze (e.g., 'login button', 'email input')"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, element_description: str) -> Dict:
        script = f"""
        (() => {{
            const description = "{element_description}".toLowerCase();
            const elements = [];
            
            // Search by common patterns
            const allElements = document.querySelectorAll('button, input, a, [role="button"], select, textarea');
            
            allElements.forEach((el, idx) => {{
                const text = (el.textContent || el.value || el.placeholder || '').toLowerCase();
                const attrs = (el.id + ' ' + el.className + ' ' + el.name).toLowerCase();
                
                if (text.includes(description) || attrs.includes(description) || 
                    description.includes(text.substring(0, 10))) {{
                    
                    // Generate multiple locator strategies
                    const locators = {{}};
                    
                    // ID-based (most reliable)
                    if (el.id) locators.id = '#' + el.id;
                    
                    // CSS-based
                    if (el.className) {{
                        locators.css = el.tagName.toLowerCase() + '.' + el.className.split(' ')[0];
                    }}
                    
                    // Attribute-based
                    if (el.name) locators.name = `${{el.tagName.toLowerCase()}}[name="${{el.name}}"]`;
                    if (el.getAttribute('data-testid')) {{
                        locators.testid = `${{el.tagName.toLowerCase()}}[data-testid="${{el.getAttribute('data-testid')}}"]`;
                    }}
                    
                    // Text-based (semantic)
                    if (el.textContent?.trim()) {{
                        locators.text = `text=${{el.textContent.trim().substring(0, 30)}}`;
                    }}
                    
                    // XPath
                    locators.xpath = `//${{el.tagName.toLowerCase()}}[${{idx + 1}}]`;
                    
                    elements.push({{
                        tag: el.tagName.toLowerCase(),
                        text: (el.textContent || el.value || '').substring(0, 50),
                        type: el.type || el.getAttribute('role') || 'unknown',
                        locators: locators,
                        recommended: locators.testid || locators.id || locators.name || locators.text || locators.css,
                        attributes: {{
                            id: el.id,
                            class: el.className,
                            name: el.name,
                            type: el.type,
                            placeholder: el.placeholder
                        }}
                    }});
                }}
            }});
            
            return {{ found: elements.length, elements: elements.slice(0, 10) }};
        }})()
        """
        
        result = self.browser_controller.evaluate_script(script)
        if result.get('success'):
            analysis = result.get('result')
            elements = analysis.get('elements', [])
            summary = [f"- {e['tag']} '{e['text']}': recommended locator: {e['recommended']}" for e in elements]
            return f"Found {analysis['found']} elements. Top matches:\n" + "\n".join(summary)
        return result


# ============================================================================
# PLAYWRIGHT BROWSER TOOLS
# These tools wrap the BrowserController for use with smolagents
# ============================================================================

class NavigateTool(Tool):
    """Tool for navigating to URLs using Playwright"""
    name = "navigate_to_url"
    description = """
    Navigates the browser to a specified URL.
    Use this tool when you need to visit a webpage.
    It returns the page title and final URL after navigation.
    """
    inputs = {
        "url": {
            "type": "string",
            "description": "The URL to navigate to (e.g., 'https://example.com')"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, url: str) -> Dict:
        result = self.browser_controller.navigate_to(url)
        return result


class ClickElementTool(Tool):
    """Tool for clicking elements on the page"""
    name = "click_element"
    description = """
    Clicks on an element on the current webpage.
    Use CSS selectors or text-based selectors to identify elements.
    Examples: 'button.submit', '#login-btn', 'text=Login', '[data-testid="submit"]'
    """
    inputs = {
        "selector": {
            "type": "string",
            "description": "CSS selector or Playwright selector to identify the element to click"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, selector: str) -> Dict:
        result = self.browser_controller.click_element(selector)
        return result


class TypeTextTool(Tool):
    """Tool for typing text into input fields"""
    name = "type_text"
    description = """
    Types text into an input field on the current webpage.
    First specify the selector to identify the input field, then the text to type.
    This will clear the field first and then type the new text.
    """
    inputs = {
        "selector": {
            "type": "string",
            "description": "CSS selector or Playwright selector for the input field"
        },
        "text": {
            "type": "string",
            "description": "The text to type into the input field"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, selector: str, text: str) -> Dict:
        result = self.browser_controller.type_text(selector, text)
        return result


class GetElementTextTool(Tool):
    """Tool for extracting text content from elements"""
    name = "get_element_text"
    description = """
    Gets the text content of an element on the current webpage.
    Useful for extracting information, verifying content, or reading labels.
    """
    inputs = {
        "selector": {
            "type": "string",
            "description": "CSS selector or Playwright selector for the element"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, selector: str) -> Dict:
        result = self.browser_controller.get_element_text(selector)
        return result


class WaitForElementTool(Tool):
    """Tool for waiting for elements to appear"""
    name = "wait_for_element"
    description = """
    Waits for an element to appear on the page.
    Useful after navigation or dynamic content loading.
    Returns success when element is found, or error if timeout occurs.
    """
    inputs = {
        "selector": {
            "type": "string",
            "description": "CSS selector or Playwright selector for the element to wait for"
        },
        "timeout": {
            "type": "integer",
            "description": "Maximum time to wait in milliseconds (default: 30000)",
            "nullable": True
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, selector: str, timeout: int = 30000) -> Dict:
        result = self.browser_controller.wait_for_selector(selector, timeout)
        return result


class EvaluateScriptTool(Tool):
    """Tool for executing JavaScript on the page"""
    name = "evaluate_javascript"
    description = """
    Executes JavaScript code on the current webpage.
    Useful for complex interactions, extracting data from the DOM,
    or performing actions not covered by other tools.
    Returns the result of the script execution.
    """
    inputs = {
        "script": {
            "type": "string",
            "description": "JavaScript code to execute on the page"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, script: str) -> Dict:
        result = self.browser_controller.evaluate_script(script)
        return result


class GetBrowserStateTool(Tool):
    """Tool for getting current browser state and screenshot"""
    name = "get_browser_state"
    description = """
    Gets the current state of the browser including the URL and a screenshot.
    Use this to understand what is currently displayed in the browser
    before deciding on next actions.
    """
    inputs = {}
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self) -> Dict:
        state = self.browser_controller.get_browser_state()
        # Return URL and simplified state (image will be handled separately)
        return {
            'url': state.get('url'),
            'has_screenshot': state.get('screenshot') is not None,
            'loading': state.get('loading', False),
            'error': state.get('error')
        }


class ScrollPageTool(Tool):
    """Tool for scrolling the page"""
    name = "scroll_page"
    description = """
    Scrolls the page up or down by a specified amount of pixels.
    Positive values scroll down, negative values scroll up.
    Use this to reveal content that is not currently visible.
    """
    inputs = {
        "pixels": {
            "type": "integer",
            "description": "Number of pixels to scroll (positive=down, negative=up)"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, pixels: int) -> Dict:
        script = f"window.scrollBy(0, {pixels})"
        result = self.browser_controller.evaluate_script(script)
        return {'success': True, 'scrolled_pixels': pixels}


class SearchInPageTool(Tool):
    """Tool for searching text within the page"""
    name = "search_in_page"
    description = """
    Searches for text on the current page and returns matching elements.
    Useful for finding specific content or verifying text presence.
    """
    inputs = {
        "text": {
            "type": "string",
            "description": "Text to search for on the page"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, text: str) -> Dict:
        script = f"""
        (() => {{
            const elements = document.querySelectorAll('*');
            const matches = [];
            elements.forEach((el, idx) => {{
                if (el.textContent && el.textContent.includes('{text}')) {{
                    matches.push({{
                        tag: el.tagName.toLowerCase(),
                        text: el.textContent.substring(0, 100),
                        index: idx
                    }});
                }}
            }});
            return {{ found: matches.length, matches: matches.slice(0, 10) }};
        }})()
        """
        result = self.browser_controller.evaluate_script(script)
        if result.get('success'):
            return {'success': True, 'result': result.get('result')}
        return result


# ============================================================================
# PHASE 3: TEST CODE GENERATION TOOL
# Uses DeepSeek-Coder for generating Playwright test code with smart locators
# ============================================================================

class GenerateTestCodeTool(Tool):
    """Tool for generating Playwright test code using DeepSeek-Coder - Phase 3"""
    name = "generate_test_code"
    description = """
    Generates clean, maintainable Playwright Python test code based on approved test cases.
    Uses smart locator strategy: prefers data-testid > id > name > CSS > XPath.
    Includes self-correction by validating selectors exist on the page.
    Use this AFTER test cases are approved in Phase 2.
    """
    inputs = {
        "test_case": {
            "type": "object",
            "description": "The approved test case object with name, steps, and expected results"
        },
        "url": {
            "type": "string",
            "description": "The URL of the page to test"
        },
        "element_locators": {
            "type": "object",
            "description": "Dictionary of element locators discovered in Phase 1",
            "nullable": True
        }
    }
    output_type = "string"

    def __init__(self, code_model: InferenceClientModel, browser_controller=None):
        super().__init__()
        self.code_model = code_model
        self.browser_controller = browser_controller

    def forward(self, test_case: Dict, url: str, element_locators: Dict = None) -> str:
        # Build the prompt with locator strategy guidance
        locator_info = ""
        if element_locators:
            locator_info = f"\nAvailable element locators:\n{json.dumps(element_locators, indent=2)}\n"
        
        prompt = f"""Generate a complete Playwright Python test for the following approved test case:

Test Case: {test_case.get('name', 'Unnamed Test')}
URL: {url}
Description: {test_case.get('description', '')}

Steps:
{chr(10).join(f"  {i+1}. {step}" for i, step in enumerate(test_case.get('steps', [])))}

Expected Results:
{chr(10).join(f"  - {result}" for result in test_case.get('expected_results', []))}

{locator_info}

LOCATOR STRATEGY (use in this priority order):
1. data-testid attribute: [data-testid="..."] (most stable)
2. ID selector: #element-id (stable if present)
3. Name attribute: [name="..."] (good for form fields)
4. Role + text: role=button[name="Submit"] (semantic, accessible)
5. CSS selector: .class-name or tag.class (less stable)
6. XPath: //tag[@attr="value"] (last resort)

Requirements:
1. Use pytest-playwright with async pattern
2. Use page.wait_for_selector() before interactions
3. Include meaningful assertions for each expected result
4. Add descriptive comments and docstring
5. Use explicit waits, avoid time.sleep()
6. Handle potential errors gracefully
7. Take screenshots at key verification points

Generate ONLY the Python code:
"""
        messages = [{"role": "user", "content": prompt}]
        response = self.code_model(messages)
        
        # Extract code from response
        code = response.content if hasattr(response, 'content') else str(response)
        
        # Clean up the response
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
        elif "```" in code:
            code = code.split("```")[1].split("```")[0]
        
        return code.strip()


class ValidateTestCodeTool(Tool):
    """Tool for validating generated test code by checking selectors exist"""
    name = "validate_test_code"
    description = """
    Validates generated test code by checking if the selectors used actually exist on the page.
    This enables self-correction before finalizing the test code.
    Use this after generating test code to ensure it will work.
    """
    inputs = {
        "code": {
            "type": "string",
            "description": "The generated test code to validate"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, code: str) -> Dict:
        # Extract selectors from code
        selector_patterns = [
            r'page\.locator\(["\']([^"\']+)["\']\)',
            r'page\.click\(["\']([^"\']+)["\']\)',
            r'page\.fill\(["\']([^"\']+)["\']\)',
            r'page\.wait_for_selector\(["\']([^"\']+)["\']\)',
            r'page\.query_selector\(["\']([^"\']+)["\']\)'
        ]
        
        selectors = set()
        for pattern in selector_patterns:
            matches = re.findall(pattern, code)
            selectors.update(matches)
        
        # Validate each selector
        validation_results = []
        for selector in selectors:
            try:
                # Check if element exists
                check_script = f"""
                (() => {{
                    try {{
                        const el = document.querySelector('{selector}');
                        return {{ exists: el !== null, selector: '{selector}' }};
                    }} catch(e) {{
                        return {{ exists: false, selector: '{selector}', error: e.message }};
                    }}
                }})()
                """
                result = self.browser_controller.evaluate_script(check_script)
                if result.get('success'):
                    validation_results.append(result.get('result'))
            except Exception as e:
                validation_results.append({'selector': selector, 'exists': False, 'error': str(e)})
        
        valid_count = sum(1 for r in validation_results if r.get('exists', False))
        
        return {
            'success': True,
            'total_selectors': len(selectors),
            'valid_selectors': valid_count,
            'invalid_selectors': len(selectors) - valid_count,
            'details': validation_results,
            'is_valid': valid_count == len(selectors)
        }


# ============================================================================
# PHASE 4: VERIFICATION & EXECUTION TOOLS
# Tools for running tests and collecting evidence
# ============================================================================

class ExecuteTestTool(Tool):
    """Tool for executing a test and collecting evidence - Phase 4"""
    name = "execute_test"
    description = """
    Executes a generated test in the visible browser and collects evidence.
    Captures screenshots at each step and generates an execution report.
    Use this in Phase 4 to verify the tests work correctly.
    """
    inputs = {
        "test_steps": {
            "type": "array",
            "description": "List of test steps to execute"
        },
        "test_name": {
            "type": "string",
            "description": "Name of the test being executed"
        }
    }
    output_type = "object"

    def __init__(self, browser_controller):
        super().__init__()
        self.browser_controller = browser_controller

    def forward(self, test_steps: List[str], test_name: str) -> Dict:
        execution_result = {
            'test_name': test_name,
            'status': 'passed',
            'start_time': datetime.now(timezone.utc).isoformat(),
            'steps': [],
            'screenshots': [],
            'errors': []
        }
        
        for i, step in enumerate(test_steps):
            step_result = {
                'step_number': i + 1,
                'description': step,
                'status': 'pending',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            try:
                # Parse and execute the step
                step_lower = step.lower()
                
                if 'navigate' in step_lower or 'go to' in step_lower:
                    url_match = re.search(r'https?://[^\s]+', step)
                    if url_match:
                        result = self.browser_controller.navigate_to(url_match.group())
                        step_result['status'] = 'passed' if result.get('success') else 'failed'
                        
                elif 'click' in step_lower:
                    # Extract selector from step
                    selector_match = re.search(r'["\']([^"\']+)["\']', step)
                    if selector_match:
                        result = self.browser_controller.click_element(selector_match.group(1))
                        step_result['status'] = 'passed' if result.get('success') else 'failed'
                        
                elif 'type' in step_lower or 'enter' in step_lower or 'fill' in step_lower:
                    # This would need more sophisticated parsing
                    step_result['status'] = 'manual_verification_needed'
                    
                elif 'verify' in step_lower or 'assert' in step_lower or 'check' in step_lower:
                    step_result['status'] = 'verification_point'
                    
                else:
                    step_result['status'] = 'executed'
                
                # Capture screenshot after each step for evidence
                sleep(0.5)
                self.browser_controller.capture_screenshot(full_page=False)
                screenshot_for_report = self.browser_controller.last_screenshot_b64
                
                if screenshot_for_report:
                    execution_result['screenshots'].append({
                        'step': i + 1,
                        'screenshot': screenshot_for_report
                    })
                
            except Exception as e:
                step_result['status'] = 'error'
                step_result['error'] = str(e)
                execution_result['status'] = 'failed'
                execution_result['errors'].append({
                    'step': i + 1,
                    'error': str(e)
                })
            
            execution_result['steps'].append(step_result)
        
        execution_result['end_time'] = datetime.now(timezone.utc).isoformat()
        status = "PASSED" if execution_result['status'] == 'passed' else "FAILED"
        return f"Test '{test_name}' execution {status}. Ran {len(execution_result['steps'])} steps. Screenshots were saved for the report."


class GenerateReportTool(Tool):
    """Tool for generating execution report with evidence"""
    name = "generate_report"
    description = """
    Generates a detailed execution report including screenshots and step-by-step log.
    Creates evidence for the user to review the test execution.
    """
    inputs = {
        "execution_result": {
            "type": "object",
            "description": "The result from test execution"
        }
    }
    output_type = "string"

    def __init__(self):
        super().__init__()

    def forward(self, execution_result: Any) -> str:
        """
        Generates a detailed test execution report. 
        Handles both raw dictionary data and summary strings by checking the controller cache.
        """
        # 1. Check if the LLM passed the summary string instead of the raw data dictionary
        if isinstance(execution_result, str):
            # Retrieve the full dictionary we saved in ExecuteTestTool.forward()
            execution_result = getattr(self.browser_controller, 'last_execution_result', None)
        
        # 2. Safety check: If we still don't have a valid dictionary, exit gracefully
        if not execution_result or not isinstance(execution_result, dict):
            return ("Error: No detailed execution data found. "
                    "Please ensure 'execute_test' was run before calling this tool.")

        # 3. Proceed with the report generation using the dictionary data
        report_lines = [
            "# Test Execution Report",
            f"\n**Test Name:** {execution_result.get('test_name', 'Unknown')}",
            f"**Status:** {'✅ PASSED' if execution_result.get('status') == 'passed' else '❌ FAILED'}",
            f"**Start Time:** {execution_result.get('start_time', 'N/A')}",
            f"**End Time:** {execution_result.get('end_time', 'N/A')}",
            "\n## Step-by-Step Execution Log\n"
        ]
        
        # Format the step logs
        for step in execution_result.get('steps', []):
            status_icon = {
                'passed': '✅',
                'failed': '❌',
                'error': '⚠️',
                'pending': '⏳',
                'executed': '▶️',
                'verification_point': '🔍'
            }.get(step.get('status', ''), '❓')
            
            report_lines.append(
                f"{step.get('step_number', '?')}. {status_icon} {step.get('description', 'No description')}"
            )
            if step.get('error'):
                report_lines.append(f"   Error: {step.get('error')}")
        
        # Add summary of errors if they exist
        if execution_result.get('errors'):
            report_lines.append("\n## Errors\n")
            for error in execution_result.get('errors', []):
                report_lines.append(f"- Step {error.get('step', '?')}: {error.get('error', 'Unknown error')}")
        
        # Add evidence summary
        report_lines.append(f"\n## Evidence\n")
        screenshots = execution_result.get('screenshots', [])
        report_lines.append(f"- Screenshots captured: {len(screenshots)}")
        
        return '\n'.join(report_lines)


# ============================================================================
# LLM AGENT CLASS
# Main orchestrator implementing the 4-Phase Testing Workflow
# ============================================================================

class LLMAgent:
    """
    Smolagents-based web testing agent implementing the 4-Phase Workflow:
    
    Phase 1: Exploration - Analyze page structure and create ground truth
    Phase 2: Collaborative Design - Propose and refine test cases with human
    Phase 3: Implementation - Generate test code with smart locator strategy
    Phase 4: Verification - Execute tests and provide evidence
    
    Models (Free Tier):
    - Qwen2-VL-7B-Instruct: Visual web reasoning and understanding screenshots
    - Starcoder2-15B: Test code generation
    - Llama-3.1-8B-Instruct: General orchestration and reasoning
    """
    
    def __init__(self, browser_controller=None):
        self.chat_history: List[Dict] = []
        self.browser_controller = browser_controller
        self.agent: Optional[CodeAgent] = None
        self.vision_agent: Optional[CodeAgent] = None
        self.code_model: Optional[InferenceClientModel] = None
        self.is_initialized = False
        
        # Workflow state
        self.current_phase = WorkflowPhase.IDLE
        self.ground_truth: Optional[PageGroundTruth] = None
        self.proposed_test_cases: List[TestCase] = []
        self.approved_test_cases: List[TestCase] = []
        self.generated_code: Dict[str, str] = {}  # test_id -> code
        self.execution_results: List[TestExecutionResult] = []
        
        # Metrics tracking
        self.metrics = MetricsTracker()
        
        # HuggingFace API token
        self.hf_token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
        
    def initialize(self, browser_controller=None):
        """Initialize the smolagents with all models and tools"""
        if browser_controller:
            self.browser_controller = browser_controller
            
        if not self.browser_controller:
            raise ValueError("Browser controller is required for initialization")
        
        try:
            # Initialize models (using free-tier models to avoid payment limits)
            self.main_model = InferenceClientModel(
            model_id="meta-llama/Llama-3.1-8B-Instruct",
            token=self.hf_token
            )
            
            self.vision_model = InferenceClientModel(
            model_id="Qwen/Qwen2.5-VL-7B-Instruct",
            token=self.hf_token
            )
            
            self.code_model = InferenceClientModel(
            model_id="Qwen/Qwen2.5-Coder-32B-Instruct",
            token=self.hf_token
            )
            
            # Create all tools for the workflow
            self.tools = [
                # Phase 1: Exploration
                ExplorePageTool(self.browser_controller),
                AnalyzeElementsTool(self.browser_controller),
                # Browser interaction
                NavigateTool(self.browser_controller),
                ClickElementTool(self.browser_controller),
                TypeTextTool(self.browser_controller),
                GetElementTextTool(self.browser_controller),
                WaitForElementTool(self.browser_controller),
                EvaluateScriptTool(self.browser_controller),
                GetBrowserStateTool(self.browser_controller),
                ScrollPageTool(self.browser_controller),
                SearchInPageTool(self.browser_controller),
                # Phase 3: Code generation
                GenerateTestCodeTool(self.code_model, self.browser_controller),
                ValidateTestCodeTool(self.browser_controller),
                # Phase 4: Verification
                ExecuteTestTool(self.browser_controller),
                GenerateReportTool(),
            ]
            
            # Create main orchestration agent
            self.agent = CodeAgent(
                tools=self.tools,
                model=self.main_model,
                additional_authorized_imports=["playwright", "time", "json", "re", "datetime"],
                max_steps=15,
                verbosity_level=1,
            )
            
            # Create vision agent for visual analysis
            self.vision_agent = CodeAgent(
                tools=self.tools,
                model=self.vision_model,
                additional_authorized_imports=["playwright", "time", "json", "re"],
                step_callbacks=[self._save_screenshot_callback],
                max_steps=15,
                verbosity_level=1,
            )
            
            self.is_initialized = True
            self.current_phase = WorkflowPhase.IDLE
            print("LLM Agent initialized with 4-Phase Workflow support")
            
        except Exception as e:
            print(f"Failed to initialize LLM Agent: {e}")
            self.is_initialized = False
            raise
    
    def _save_screenshot_callback(self, memory_step: ActionStep, agent: CodeAgent) -> None:
        """Callback to capture screenshots after each agent step"""
        sleep(0.5)
        
        if self.browser_controller and self.browser_controller.page:
            try:
                current_step = memory_step.step_number
                
                for previous_step in agent.memory.steps:
                    if isinstance(previous_step, ActionStep) and previous_step.step_number <= current_step - 2:
                        previous_step.observations_images = None
                
                screenshot_bytes = self.browser_controller.page.screenshot(full_page=False)
                image = Image.open(BytesIO(screenshot_bytes))
                memory_step.observations_images = [image.copy()]
                
                url_info = f"Current URL: {self.browser_controller.page.url}"
                memory_step.observations = (
                    url_info if memory_step.observations is None 
                    else memory_step.observations + "\n" + url_info
                )
                
            except Exception as e:
                print(f"Error capturing screenshot: {e}")

    # =========================================================================
    # PHASE 1: EXPLORATION
    # =========================================================================
    
    def start_exploration(self, url: str) -> Dict:
        """
        Phase 1: Explore a URL to understand page structure and create ground truth.
        """
        start_time = time()
        self.current_phase = WorkflowPhase.EXPLORATION
        
        try:
            # First try to navigate to the URL directly
            nav_result = self.browser_controller.navigate_to(url)
            
            # Handle navigation errors gracefully
            if not nav_result.get('success'):
                error_type = nav_result.get('error_type', '')
                error_msg = nav_result.get('error', 'Unknown error')
                
                # Handle DNS errors - URL doesn't exist
                if error_type == 'dns_error':
                    suggestions = nav_result.get('suggestions', [])
                    suggestion_text = '\n'.join(f"  - {s}" for s in suggestions)
                    
                    return {
                        'success': False,
                        'phase': 'idle',  # Return to idle so user can try again
                        'error_type': 'dns_error',
                        'message': f"❌ **Could not reach the website**\n\n"
                                  f"The URL `{url}` could not be found. This might mean:\n"
                                  f"- The URL is misspelled\n"
                                  f"- The website doesn't exist\n"
                                  f"- The website is down\n\n"
                                  f"**What would you like to do?**\n"
                                  f"1. **Re-enter the correct URL** - Just type it and I'll try again\n"
                                  f"2. **Search on Google** - Type 'search [website name]' and I'll help you find it\n\n"
                                  f"💡 Suggestions:\n{suggestion_text}",
                        'actions': ['re-enter URL', 'search on Google'],
                        'metrics': self.metrics.to_dict()
                    }
                
                # Handle session recovered - browser was restarted
                elif error_type == 'session_recovered':
                    return {
                        'success': False,
                        'phase': 'idle',
                        'message': f"🔄 **Browser session was recovered**\n\n"
                                  f"The browser had an issue but has been restarted.\n"
                                  f"Please try your request again by entering the URL.",
                        'metrics': self.metrics.to_dict()
                    }
                
                # Handle timeout
                elif error_type == 'timeout':
                    return {
                        'success': False,
                        'phase': 'idle',
                        'message': f"⏱️ **Website took too long to respond**\n\n"
                                  f"The website `{url}` didn't respond in time.\n"
                                  f"This could mean the website is slow or experiencing issues.\n\n"
                                  f"Would you like to:\n"
                                  f"1. **Try again** - Just send the URL again\n"
                                  f"2. **Try a different URL**",
                        'metrics': self.metrics.to_dict()
                    }
                
                # Generic error
                else:
                    return {
                        'success': False,
                        'phase': 'idle',
                        'error': error_msg,
                        'message': f"❌ **Navigation failed**\n\n"
                                  f"Could not open `{url}`.\n"
                                  f"Error: {error_msg}\n\n"
                                  f"Please check the URL and try again.",
                        'metrics': self.metrics.to_dict()
                    }
            
            # Navigation succeeded - now explore the page
            nav_screenshot = nav_result.get('screenshot')  # Save screenshot from navigation
            
            explore_tool = ExplorePageTool(self.browser_controller)
            result = explore_tool.forward(url)
            
            if result.get('success'):
                ground_truth_data = result.get('ground_truth', {})
                
                # Use screenshot from exploration, fallback to navigation screenshot
                screenshot = result.get('screenshot') or nav_screenshot
                
                # Store ground truth
                self.ground_truth = PageGroundTruth(
                    url=url,
                    title=ground_truth_data.get('title', ''),
                    description=f"Page with {len(ground_truth_data.get('forms', []))} forms, "
                               f"{len(ground_truth_data.get('buttons', []))} buttons, "
                               f"{len(ground_truth_data.get('links', []))} links",
                    elements=[],
                    forms=ground_truth_data.get('forms', []),
                    navigation=ground_truth_data.get('navigation', []),
                    interactive_areas=ground_truth_data.get('interactive_elements', []),
                    screenshot_b64=screenshot,
                    dom_summary=json.dumps(ground_truth_data, indent=2)[:2000]
                )
                
                # Generate summary for human
                summary = summary = result.get('message', "Exploration complete.")
                
                response_time = (time() - start_time) * 1000
                self.metrics.record_request(response_time, tokens=500)  # Estimate
                
                return {
                    'success': True,
                    'phase': 'exploration',
                    'summary': summary,
                    'ground_truth': ground_truth_data,
                    'screenshot': screenshot,
                    'message': f"✅ **Phase 1 Complete: Exploration**\n\n{summary}\n\n"
                              f"Ready to proceed to **Phase 2: Collaborative Design**. "
                              f"I will now propose test cases based on this analysis.",
                    'metrics': self.metrics.to_dict()
                }
            else:
                return {
                    'success': False,
                    'phase': 'exploration',
                    'error': result.get('error', 'Unknown error during exploration'),
                    'metrics': self.metrics.to_dict()
                }
                
        except Exception as e:
            return {
                'success': False,
                'phase': 'exploration',
                'error': str(e),
                'metrics': self.metrics.to_dict()
            }
    
    def _generate_exploration_summary(self, ground_truth: Dict) -> str:
        """Generate a human-readable summary of the exploration results"""
        lines = ["## 📋 Page Analysis Summary\n"]
        
        lines.append(f"**Title:** {ground_truth.get('title', 'N/A')}")
        lines.append(f"**URL:** {ground_truth.get('url', 'N/A')}\n")
        
        # Forms
        forms = ground_truth.get('forms', [])
        if forms:
            lines.append(f"### 📝 Forms Found: {len(forms)}")
            for form in forms[:3]:
                lines.append(f"- **{form.get('id', 'unnamed')}**: {len(form.get('inputs', []))} inputs")
        
        # Buttons
        buttons = ground_truth.get('buttons', [])
        if buttons:
            lines.append(f"\n### 🔘 Interactive Buttons: {len(buttons)}")
            for btn in buttons[:5]:
                lines.append(f"- `{btn.get('text', 'No text')[:30]}` → {btn.get('recommended', btn.get('locator_css', 'N/A'))}")
        
        # Links
        links = ground_truth.get('links', [])
        if links:
            lines.append(f"\n### 🔗 Navigation Links: {len(links)}")
            for link in links[:5]:
                lines.append(f"- {link.get('text', 'No text')[:30]}")
        
        # Headings
        headings = ground_truth.get('headings', [])
        if headings:
            lines.append(f"\n### 📑 Page Structure:")
            for h in headings[:5]:
                lines.append(f"- {h.get('level', 'H?')}: {h.get('text', 'No text')[:50]}")
        
        return '\n'.join(lines)

    # =========================================================================
    # PHASE 2: COLLABORATIVE TEST DESIGN
    # =========================================================================
    
    def propose_test_cases(self) -> Dict:
        """
        Phase 2: Propose test cases based on ground truth for human review.
        """
        start_time = time()
        self.current_phase = WorkflowPhase.COLLABORATIVE_DESIGN
        
        if not self.ground_truth:
            return {
                'success': False,
                'error': 'No ground truth available. Please run exploration first.',
                'metrics': self.metrics.to_dict()
            }
        
        try:
            # Generate test cases based on page structure
            test_cases = self._generate_test_case_proposals()
            self.proposed_test_cases = test_cases
            
            # Format as table for human review
            table = self._format_test_cases_table(test_cases)
            
            response_time = (time() - start_time) * 1000
            self.metrics.record_request(response_time, tokens=800)
            
            return {
                'success': True,
                'phase': 'collaborative_design',
                'test_cases': [self._test_case_to_dict(tc) for tc in test_cases],
                'table': table,
                'message': f"## 📝 Phase 2: Proposed Test Cases\n\n{table}\n\n"
                          f"Please review and provide feedback:\n"
                          f"- 'approve TC-001' to approve a test case\n"
                          f"- 'revise TC-002: add validation for...' to request changes\n"
                          f"- 'reject TC-003' to remove a test case\n"
                          f"- 'approve all' to approve all test cases",
                'metrics': self.metrics.to_dict()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'metrics': self.metrics.to_dict()
            }
    
    def _generate_test_case_proposals(self) -> List[TestCase]:
        """Generate test case proposals based on ground truth"""
        test_cases = []
        tc_id = 1
        
        # Generate tests for forms
        for form in self.ground_truth.forms[:3]:
            form_id = form.get('id', 'form')
            inputs = form.get('inputs', [])
            
            # Valid submission test
            test_cases.append(TestCase(
                id=f"TC-{tc_id:03d}",
                name=f"Valid {form_id} Submission",
                description=f"Test successful form submission with valid data",
                preconditions=[f"Navigate to {self.ground_truth.url}"],
                steps=[
                    f"Fill {inp.get('name', inp.get('type', 'field'))} with valid data"
                    for inp in inputs[:5]
                ] + ["Click submit button", "Wait for response"],
                expected_results=["Form submits successfully", "Success message displayed or redirect occurs"],
                priority="high",
                status="proposed"
            ))
            tc_id += 1
            
            # Validation test for required fields
            required_inputs = [inp for inp in inputs if inp.get('required')]
            if required_inputs:
                test_cases.append(TestCase(
                    id=f"TC-{tc_id:03d}",
                    name=f"{form_id} Required Field Validation",
                    description=f"Test that required fields show validation errors when empty",
                    preconditions=[f"Navigate to {self.ground_truth.url}"],
                    steps=["Leave required fields empty", "Click submit button"],
                    expected_results=["Validation errors are displayed", "Form is not submitted"],
                    priority="high",
                    status="proposed"
                ))
                tc_id += 1
        
        # Generate navigation tests
        nav_items = self.ground_truth.navigation[:1]
        for nav in nav_items:
            links = nav.get('links', [])[:3]
            for link in links:
                if link.get('text'):
                    test_cases.append(TestCase(
                        id=f"TC-{tc_id:03d}",
                        name=f"Navigation to {link.get('text', 'Page')[:20]}",
                        description=f"Test that navigation link works correctly",
                        preconditions=[f"Navigate to {self.ground_truth.url}"],
                        steps=[f"Click on '{link.get('text', 'link')}'", "Wait for page load"],
                        expected_results=["Page navigates successfully", "Expected content is displayed"],
                        priority="medium",
                        status="proposed"
                    ))
                    tc_id += 1
        
        # Generate button interaction tests
        buttons = [b for b in (self.ground_truth.dom_summary and 
                   json.loads(self.ground_truth.dom_summary).get('buttons', []) or [])
                  if b.get('text')][:2]
        
        return test_cases[:8]  # Limit to 8 test cases initially
    
    def _test_case_to_dict(self, tc: TestCase) -> Dict:
        return {
            'id': tc.id,
            'name': tc.name,
            'description': tc.description,
            'steps': tc.steps,
            'expected_results': tc.expected_results,
            'priority': tc.priority,
            'status': tc.status,
            'human_feedback': tc.human_feedback
        }
    
    def _format_test_cases_table(self, test_cases: List[TestCase]) -> str:
        """Format test cases as a markdown table"""
        lines = [
            "| ID | Name | Priority | Steps | Status |",
            "|-----|------|----------|-------|--------|"
        ]
        for tc in test_cases:
            steps_count = len(tc.steps)
            lines.append(f"| {tc.id} | {tc.name[:30]} | {tc.priority} | {steps_count} steps | {tc.status} |")
        
        return '\n'.join(lines)
    
    def handle_test_case_feedback(self, feedback: str) -> Dict:
        """Handle human feedback on test cases"""
        start_time = time()
        feedback_lower = feedback.lower()
        
        response_messages = []
        
        if 'approve all' in feedback_lower:
            for tc in self.proposed_test_cases:
                tc.status = 'approved'
            self.approved_test_cases = self.proposed_test_cases.copy()
            response_messages.append(f"✅ All {len(self.approved_test_cases)} test cases approved!")
            
        else:
            # Parse individual approvals/rejections/revisions
            for tc in self.proposed_test_cases:
                if f'approve {tc.id.lower()}' in feedback_lower:
                    tc.status = 'approved'
                    self.approved_test_cases.append(tc)
                    response_messages.append(f"✅ {tc.id} approved")
                    
                elif f'reject {tc.id.lower()}' in feedback_lower:
                    tc.status = 'rejected'
                    response_messages.append(f"❌ {tc.id} rejected")
                    
                elif f'revise {tc.id.lower()}' in feedback_lower:
                    tc.status = 'needs_revision'
                    # Extract revision notes
                    revision_match = re.search(f'{tc.id.lower()}[:\\s]+(.+?)(?=(?:approve|reject|revise|$))', 
                                              feedback_lower, re.IGNORECASE)
                    if revision_match:
                        tc.human_feedback = revision_match.group(1).strip()
                    response_messages.append(f"📝 {tc.id} marked for revision")
        
        response_time = (time() - start_time) * 1000
        self.metrics.record_request(response_time, tokens=100)
        
        # Check if ready to proceed
        approved_count = len([tc for tc in self.proposed_test_cases if tc.status == 'approved'])
        revision_count = len([tc for tc in self.proposed_test_cases if tc.status == 'needs_revision'])
        
        table = self._format_test_cases_table(self.proposed_test_cases)
        
        next_steps = ""
        if approved_count > 0 and revision_count == 0:
            next_steps = (f"\n\n**Ready for Phase 3!** Say 'generate code' to proceed to implementation, "
                         f"or continue refining test cases.")
        elif revision_count > 0:
            next_steps = f"\n\n**{revision_count} test cases need revision.** I'll update them based on your feedback."
        
        return {
            'success': True,
            'phase': 'collaborative_design',
            'feedback_processed': response_messages,
            'approved_count': approved_count,
            'test_cases': [self._test_case_to_dict(tc) for tc in self.proposed_test_cases],
            'message': f"## Feedback Processed\n\n" + '\n'.join(response_messages) + 
                      f"\n\n### Updated Test Cases\n{table}" + next_steps,
            'metrics': self.metrics.to_dict()
        }

    # =========================================================================
    # PHASE 3: IMPLEMENTATION
    # =========================================================================
    
    def generate_test_code(self, test_case_id: str = None) -> Dict:
        """
        Phase 3: Generate test code for approved test cases.
        """
        start_time = time()
        self.current_phase = WorkflowPhase.IMPLEMENTATION
        
        # Get test cases to implement
        if test_case_id:
            test_cases = [tc for tc in self.approved_test_cases if tc.id == test_case_id]
        else:
            test_cases = self.approved_test_cases
        
        if not test_cases:
            return {
                'success': False,
                'error': 'No approved test cases to implement. Please approve test cases first.',
                'metrics': self.metrics.to_dict()
            }
        
        generated_tests = []
        
        for tc in test_cases:
            try:
                # Get element locators from ground truth
                locators = self._extract_locators_for_test(tc)
                
                # Generate code
                code_tool = GenerateTestCodeTool(self.code_model, self.browser_controller)
                code = code_tool.forward(
                    test_case=self._test_case_to_dict(tc),
                    url=self.ground_truth.url if self.ground_truth else "",
                    element_locators=locators
                )
                
                # Validate the code
                validate_tool = ValidateTestCodeTool(self.browser_controller)
                validation = validate_tool.forward(code)
                
                self.generated_code[tc.id] = code
                
                generated_tests.append({
                    'id': tc.id,
                    'name': tc.name,
                    'code': code,
                    'validation': validation,
                    'is_valid': validation.get('is_valid', False)
                })
                
            except Exception as e:
                generated_tests.append({
                    'id': tc.id,
                    'name': tc.name,
                    'error': str(e)
                })
        
        response_time = (time() - start_time) * 1000
        self.metrics.record_request(response_time, tokens=2000)
        
        # Format response
        code_blocks = []
        for test in generated_tests:
            if test.get('code'):
                valid_status = "✅ Validated" if test.get('is_valid') else "⚠️ Some selectors may need adjustment"
                code_blocks.append(
                    f"### {test['id']}: {test['name']}\n"
                    f"**Status:** {valid_status}\n\n"
                    f"```python\n{test['code']}\n```\n"
                )
            else:
                code_blocks.append(f"### {test['id']}: {test['name']}\n**Error:** {test.get('error', 'Unknown')}\n")
        
        return {
            'success': True,
            'phase': 'implementation',
            'generated_tests': generated_tests,
            'message': f"## 💻 Phase 3: Generated Test Code\n\n" + '\n'.join(code_blocks) +
                      f"\n\n**Ready for Phase 4!** Say 'run tests' or 'execute tests' to verify the tests work correctly.",
            'metrics': self.metrics.to_dict()
        }
    
    def _extract_locators_for_test(self, test_case: TestCase) -> Dict:
        """Extract relevant locators from ground truth for a test case"""
        locators = {}
        
        if self.ground_truth and self.ground_truth.dom_summary:
            try:
                dom_data = json.loads(self.ground_truth.dom_summary)
                
                # Add button locators
                for btn in dom_data.get('buttons', []):
                    if btn.get('text'):
                        key = btn.get('text', '').lower().replace(' ', '_')[:20]
                        locators[f"button_{key}"] = btn.get('locator_id') or btn.get('locator_text') or btn.get('locator_css')
                
                # Add form input locators
                for form in dom_data.get('forms', []):
                    for inp in form.get('inputs', []):
                        if inp.get('name'):
                            locators[f"input_{inp.get('name')}"] = inp.get('locator_id') or inp.get('locator_name')
                
            except json.JSONDecodeError:
                pass
        
        return locators

    # =========================================================================
    # PHASE 4: VERIFICATION
    # =========================================================================
    
    def execute_tests(self, test_case_id: str = None) -> Dict:
        """
        Phase 4: Execute tests in visible browser and collect evidence.
        """
        start_time = time()
        self.current_phase = WorkflowPhase.VERIFICATION
        
        # Get tests to execute
        if test_case_id:
            tests_to_run = {k: v for k, v in self.generated_code.items() if k == test_case_id}
        else:
            tests_to_run = self.generated_code
        
        if not tests_to_run:
            return {
                'success': False,
                'error': 'No generated tests to execute. Please generate test code first.',
                'metrics': self.metrics.to_dict()
            }
        
        execution_results = []
        
        for test_id, code in tests_to_run.items():
            test_case = next((tc for tc in self.approved_test_cases if tc.id == test_id), None)
            if not test_case:
                continue
            
            # Execute the test steps
            execute_tool = ExecuteTestTool(self.browser_controller)
            result = execute_tool.forward(
                test_steps=test_case.steps,
                test_name=f"{test_id}: {test_case.name}"
            )
            
            execution_results.append(result)
            self.execution_results.append(TestExecutionResult(
                test_name=test_case.name,
                status=result.get('status', 'unknown'),
                duration_ms=(time() - start_time) * 1000,
                steps_executed=result.get('steps', []),
                screenshots=[s.get('screenshot') for s in result.get('screenshots', [])],
                error_message='; '.join(e.get('error', '') for e in result.get('errors', []))
            ))
        
        # Generate report
        report_tool = GenerateReportTool()
        reports = []
        for result in execution_results:
            report = report_tool.forward(result)
            reports.append(report)
        
        response_time = (time() - start_time) * 1000
        self.metrics.record_request(response_time, tokens=300)
        
        # Collect all screenshots
        all_screenshots = []
        for result in execution_results:
            all_screenshots.extend(result.get('screenshots', []))
        
        passed = sum(1 for r in execution_results if r.get('status') == 'passed')
        failed = len(execution_results) - passed
        
        return {
            'success': True,
            'phase': 'verification',
            'execution_results': execution_results,
            'screenshots': all_screenshots,
            'summary': {
                'total': len(execution_results),
                'passed': passed,
                'failed': failed
            },
            'message': f"## 🔍 Phase 4: Verification Results\n\n" +
                      f"**Summary:** {passed}/{len(execution_results)} tests passed\n\n" +
                      '\n---\n'.join(reports) +
                      f"\n\n**Review the results above.** If there are issues, you can:\n"
                      f"- 'refactor TC-001: fix the login selector' to request code changes\n"
                      f"- 'rerun TC-001' to re-execute a specific test\n"
                      f"- 'export tests' to save the test files",
            'metrics': self.metrics.to_dict()
        }
    
    def refactor_test(self, test_case_id: str, feedback: str) -> Dict:
        """Refactor a test based on user feedback after verification"""
        start_time = time()
        
        if test_case_id not in self.generated_code:
            return {
                'success': False,
                'error': f'Test case {test_case_id} not found in generated code.',
                'metrics': self.metrics.to_dict()
            }
        
        original_code = self.generated_code[test_case_id]
        
        # Use code model to refactor
        prompt = f"""Refactor the following Playwright test code based on this feedback:

FEEDBACK: {feedback}

ORIGINAL CODE:
```python
{original_code}
```

Apply the feedback to fix the issues. Generate the complete corrected code:
"""
        
        messages = [{"role": "user", "content": prompt}]
        response = self.code_model(messages)
        
        new_code = response.content if hasattr(response, 'content') else str(response)
        
        # Clean up
        if "```python" in new_code:
            new_code = new_code.split("```python")[1].split("```")[0]
        elif "```" in new_code:
            new_code = new_code.split("```")[1].split("```")[0]
        
        self.generated_code[test_case_id] = new_code.strip()
        
        response_time = (time() - start_time) * 1000
        self.metrics.record_request(response_time, tokens=1500)
        
        return {
            'success': True,
            'phase': 'verification',
            'test_case_id': test_case_id,
            'refactored_code': new_code.strip(),
            'message': f"## 🔧 Refactored Test: {test_case_id}\n\n"
                      f"Applied feedback: *{feedback}*\n\n"
                      f"```python\n{new_code.strip()}\n```\n\n"
                      f"Say 'run tests' to verify the fix works.",
            'metrics': self.metrics.to_dict()
        }
    
    # =========================================================================
    # MAIN MESSAGE PROCESSOR - Routes to appropriate phase
    # =========================================================================
    
    def process_message(self, message: str) -> Dict:
        """
        Process a user message and route to the appropriate workflow phase.
        
        The workflow follows these phases:
        1. Exploration: User provides URL → Agent analyzes page
        2. Collaborative Design: Agent proposes tests → Human reviews
        3. Implementation: Generate code for approved tests
        4. Verification: Execute tests and collect evidence
        """
        clean_msg = message.lower().strip()
        if clean_msg == "reset":
            print("\n--- [SYSTEM] Hard Reset Triggered ---")
            self.current_phase = WorkflowPhase.IDLE
            self.ground_truth = None
            self.proposed_test_cases = []
            self.approved_test_cases = []
            self.generated_code = {}
            self.execution_results = []
            self.chat_history = [] # Optional: clear chat too
            
            return {
                'text': "🔄 **System Reset Successful.** Internal state and phases have been cleared. Send a URL to start a new Phase 1 exploration.",
                'phase': 'idle',
                'success': True,
                'metrics': self.metrics.to_dict()
            }
        
        start_time = time()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Store message in history
        self.chat_history.append({
            'role': 'user',
            'content': message,
            'timestamp': timestamp
        })
        
        response = {
            'text': '',
            'actions': [],
            'phase': self.current_phase.value,
            'code': None,
            'success': True,
            'metrics': self.metrics.to_dict()
        }
        
        try:
            # Initialize if needed
            if not self.is_initialized:
                if self.browser_controller:
                    self.initialize(self.browser_controller)
                else:
                    response['text'] = self._get_welcome_message()
                    response['success'] = False
                    self._store_response(response['text'])
                    return response
            
            lower_message = message.lower().strip()
            
            # Route based on message intent and current phase
            result = self._route_message(message, lower_message)
            
            response['text'] = result.get('message', result.get('text', ''))
            response['phase'] = result.get('phase', self.current_phase.value)
            response['code'] = result.get('code') or result.get('refactored_code')
            response['success'] = result.get('success', True)
            response['actions'] = result.get('actions', [])
            response['metrics'] = result.get('metrics', self.metrics.to_dict())
            
            # Add additional data if present
            if result.get('ground_truth'):
                response['ground_truth'] = result['ground_truth']
            if result.get('test_cases'):
                response['test_cases'] = result['test_cases']
            if result.get('screenshot'):
                response['screenshot'] = result['screenshot']
            if result.get('execution_results'):
                response['execution_results'] = result['execution_results']
            if result.get('generated_tests'):
                response['generated_tests'] = result['generated_tests']
                
        except Exception as e:
            print(f"Error processing message: {e}")
            response['text'] = f"I encountered an error: {str(e)}. Please try again."
            response['success'] = False
        
        # Record metrics
        response_time = (time() - start_time) * 1000
        self.metrics.record_request(response_time)
        response['metrics'] = self.metrics.to_dict()
        
        self._store_response(response['text'])
        return response
    
    def _route_message(self, message: str, lower_message: str) -> Dict:
        """Route message to appropriate handler based on intent"""
        
        # Phase 1: Exploration - detect URL input
        url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-z]{2,}/?[^\s]*)'
        url_match = re.search(url_pattern, message)
        
        if url_match:
            url = url_match.group()
            # Force https if missing
            if not url.startswith('http'):
                url = 'https://' + url
                    
            print(f"--- [DEBUG] Phase 1 Triggered for URL: {url} ---")
            try:
                result = self.start_exploration(url)
                print(f"--- [DEBUG] Exploration Result: {truncate_screenshot(result)} ---")
                
                if result.get('success'):
                    print("--- [DEBUG] Exploration Successful, Proposing Tests... ---")
                    proposal = self.propose_test_cases()
                    result['message'] += "\n\n---\n\n" + proposal.get('message', '')
                    result['test_cases'] = proposal.get('test_cases', [])
                else:
                    # If it failed, ensure there's a message for the UI to show
                    if 'message' not in result:
                        result['message'] = f"❌ Exploration failed: {result.get('error', 'Unknown error')}"
                return result
            
            except Exception as e:
                print(f"--- [DEBUG] CRASH in _route_message: {str(e)} ---")
                return {'success': False, 'message': f"Internal Agent Error: {str(e)}", 'phase': 'idle'}
        
        print(f"--- [DEBUG] No URL found. Checking Phase: {self.current_phase.value} ---")
        # Handle "search" command - help user find correct URL
        if lower_message.startswith('search '):
            return self._search_for_website(message[7:].strip())
            
        if any(k in lower_message for k in ['approve', 'reject', 'revise']):
            return self.handle_test_case_feedback(message)
        
        # Phase 2: Request test case proposals
        if any(keyword in lower_message for keyword in ['propose test', 'suggest test', 'what tests', 'test cases']):
            return self.propose_test_cases()
        
        # Phase 3: Implementation - generate code
        if any(keyword in lower_message for keyword in ['generate code', 'write code', 'implement', 'create code']):
            return self.generate_test_code()
        
        # Phase 4: Verification - execute tests
        if any(k in lower_message for k in ['run test', 'execute', 'verify']):
            return self.execute_tests()
        
        # Phase 4: Refactoring
        if 'refactor' in lower_message:
            tc_match = re.search(r'tc-?(\d+)', lower_message, re.IGNORECASE)
            if tc_match:
                test_id = f"TC-{tc_match.group(1).zfill(3)}"
                feedback = re.sub(r'refactor\s+tc-?\d+[:\s]*', '', message, flags=re.IGNORECASE).strip()
                return self.refactor_test(test_id, feedback)
        
        # Phase 4: Rerun specific test
        if 'rerun' in lower_message:
            tc_match = re.search(r'tc-?(\d+)', lower_message, re.IGNORECASE)
            if tc_match:
                test_id = f"TC-{tc_match.group(1).zfill(3)}"
                return self.execute_tests(test_id)
        
        # Export tests
        if 'export' in lower_message:
            return self._export_tests()
        
        # Status/help
        if any(keyword in lower_message for keyword in ['status', 'where am i', 'help', 'what next']):
            return self._get_status_response()
        
        # Default: use the main agent for general queries
        print("--- [DEBUG] Falling back to Main Agent Chat ---")
        return self._run_main_agent(message)
    
    def _get_welcome_message(self) -> str:
        """Return welcome message explaining the 4-phase workflow"""
        return """# 🤖 O2morni Web Testing Agent

Welcome! I'm your AI-powered web testing assistant using a **Human-in-the-Loop** approach.

## 📋 4-Phase Testing Workflow

**Phase 1: Exploration** 🔍
> Provide me a URL and I'll analyze the page structure, forms, buttons, and interactive elements.

**Phase 2: Collaborative Design** 📝
> I'll propose test cases. You review, approve, reject, or request revisions until we agree on coverage.

**Phase 3: Implementation** 💻
> I generate clean Playwright test code with smart locator strategies (ID > CSS > XPath).

**Phase 4: Verification** ✅
> I execute tests in a visible browser, provide screenshots/reports, and refactor based on your feedback.

---

**To get started, send me a URL to test!**
Example: `Test https://example.com/login`

**Real-time Metrics** are tracked throughout:
- ⏱️ Average Response Time
- 🎯 Token Usage
"""
    
    def _get_status_response(self) -> Dict:
        """Return current workflow status"""
        phase_descriptions = {
            WorkflowPhase.IDLE: "Ready to start. Send me a URL to test!",
            WorkflowPhase.EXPLORATION: "Analyzing page structure...",
            WorkflowPhase.COLLABORATIVE_DESIGN: "Designing test cases. Review and provide feedback.",
            WorkflowPhase.IMPLEMENTATION: "Generating test code.",
            WorkflowPhase.VERIFICATION: "Executing and verifying tests."
        }
        
        status_lines = [
            f"## 📊 Current Status\n",
            f"**Phase:** {self.current_phase.value.title()}",
            f"**Status:** {phase_descriptions.get(self.current_phase, 'Unknown')}",
            f"\n### Progress",
            f"- Ground Truth: {'✅' if self.ground_truth else '❌'}",
            f"- Proposed Tests: {len(self.proposed_test_cases)}",
            f"- Approved Tests: {len(self.approved_test_cases)}",
            f"- Generated Code: {len(self.generated_code)}",
            f"- Executed Tests: {len(self.execution_results)}",
            f"\n### Metrics",
            f"- Avg Response Time: {self.metrics.average_response_time:.2f}ms",
            f"- Total Tokens: {self.metrics.total_tokens_consumed}",
            f"- Requests Made: {self.metrics.total_requests}",
        ]
        
        next_action = {
            WorkflowPhase.IDLE: "Send a URL to begin exploration.",
            WorkflowPhase.EXPLORATION: "Review the page analysis above.",
            WorkflowPhase.COLLABORATIVE_DESIGN: "Approve/reject test cases or say 'generate code'.",
            WorkflowPhase.IMPLEMENTATION: "Say 'run tests' to execute.",
            WorkflowPhase.VERIFICATION: "Review results or 'refactor TC-XXX: feedback'."
        }
        
        status_lines.append(f"\n### Next Step\n{next_action.get(self.current_phase, 'Continue with the workflow.')}")
        
        return {
            'success': True,
            'phase': self.current_phase.value,
            'message': '\n'.join(status_lines),
            'metrics': self.metrics.to_dict()
        }
    
    def _export_tests(self) -> Dict:
        """Export generated tests to files"""
        if not self.generated_code:
            return {
                'success': False,
                'error': 'No tests to export. Generate test code first.',
                'metrics': self.metrics.to_dict()
            }
        
        exported = []
        for test_id, code in self.generated_code.items():
            filename = f"test_{test_id.lower().replace('-', '_')}.py"
            exported.append({
                'filename': filename,
                'code': code
            })
        
        return {
            'success': True,
            'phase': 'verification',
            'exported_tests': exported,
            'message': f"## 📁 Exported {len(exported)} Test Files\n\n" +
                      '\n'.join(f"- `{t['filename']}`" for t in exported) +
                      "\n\nTests are ready to be saved to the `generated_tests/` directory.",
            'metrics': self.metrics.to_dict()
        }
    
    def _run_main_agent(self, message: str) -> Dict:
        """Run the main orchestration agent for general queries"""
        print(f"DEBUG: Starting Agent Loop for task: {message}") # <--- ADD THIS
        try:
            playwright_instructions = self._get_playwright_instructions()
            result = self.agent.run(message + playwright_instructions)
            
            print(f"DEBUG: Agent Loop Finished.")
            return {
                'success': True,
                'phase': self.current_phase.value,
                'message': str(result),
                'actions': self._extract_actions(message),
                'metrics': self.metrics.to_dict()
            }
        except Exception as e:
            return {
                'success': False,
                'phase': self.current_phase.value,
                'message': f"Error: {str(e)}",
                'metrics': self.metrics.to_dict()
            }
    
    def _get_playwright_instructions(self) -> str:
        """Get instructions for the agent on tool usage"""
        return """

Browser Automation Instructions:
- Use explore_page for deep page analysis (Phase 1)
- Use analyze_elements to find best selectors for specific elements
- Use navigate_to_url to visit webpages
- Use click_element with CSS selectors like '#id', '.class', '[data-testid="name"]'
- Use type_text to fill input fields
- Use wait_for_element before interacting with dynamic content
- Use generate_test_code to create Playwright tests (Phase 3)
- Use validate_test_code to verify selectors exist
- Use execute_test to run and verify tests (Phase 4)
- Use generate_report to create execution reports

Always verify results after each action.
"""
    
    def _extract_actions(self, message: str) -> List[str]:
        """Extract action types from message"""
        actions = []
        lower = message.lower()
        
        action_keywords = {
            'navigate': ['navigate', 'go to', 'visit', 'open'],
            'click': ['click', 'press', 'tap'],
            'type': ['type', 'enter', 'fill', 'input'],
            'explore': ['explore', 'analyze', 'scan'],
            'test': ['test', 'generate', 'create'],
            'execute': ['run', 'execute', 'verify'],
            'refactor': ['refactor', 'fix', 'update']
        }
        
        for action, keywords in action_keywords.items():
            if any(kw in lower for kw in keywords):
                actions.append(action)
        
        return actions if actions else ['general']
    
    def _search_for_website(self, query: str) -> Dict:
        """
        Search Google for a website and show results to user.
        This helps when the user enters an incorrect URL.
        """
        try:
            # Navigate to Google
            nav_result = self.browser_controller.navigate_to('https://www.google.com')
            if not nav_result.get('success'):
                return {
                    'success': False,
                    'message': f"❌ Could not access Google to search. Please manually find the correct URL and enter it.",
                    'metrics': self.metrics.to_dict()
                }
            
            sleep(1)
            
            # Type the search query
            search_query = f"{query} official website"
            type_result = self.browser_controller.type_text('textarea[name="q"], input[name="q"]', search_query)
            if not type_result.get('success'):
                return {
                    'success': False,
                    'message': f"❌ Could not type search query. Please try again.",
                    'metrics': self.metrics.to_dict()
                }
            
            # Press Enter to search
            if self.browser_controller.page:
                self.browser_controller.page.keyboard.press('Enter')
                sleep(2)  # Wait for results
            
            # Capture screenshot of search results
            self.browser_controller.capture_screenshot()
            screenshot_for_ui = self.browser_controller.last_screenshot_b64
            # Try to extract search result links
            results_script = """
            (() => {
                const results = [];
                document.querySelectorAll('a h3').forEach((h3, idx) => {
                    if (idx < 5) {
                        const link = h3.closest('a');
                        if (link && link.href && !link.href.includes('google.com')) {
                            results.push({
                                title: h3.textContent,
                                url: link.href
                            });
                        }
                    }
                });
                return results;
            })()
            """
            
            script_result = self.browser_controller.evaluate_script(results_script)
            search_results = script_result.get('result', []) if script_result.get('success') else []
            
            # Format results for user
            results_text = ""
            if search_results:
                results_text = "\n\n**Top Results:**\n"
                for i, result in enumerate(search_results[:5], 1):
                    results_text += f"{i}. **{result.get('title', 'N/A')}**\n   `{result.get('url', 'N/A')}`\n"
            
            return {
                'success': True,
                'phase': 'idle',
                'screenshot': screenshot_for_ui,
                'search_results': search_results,
                'message': f"🔍 **Google Search Results for '{query}'**\n\n"
                          f"I've searched Google for you. Look at the browser screenshot to see the results.{results_text}\n\n"
                          f"**To continue:** Copy the correct URL from the results above and send it to me, like:\n"
                          f"`test https://correct-url.com`",
                'metrics': self.metrics.to_dict()
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ Search failed: {str(e)}\n\nPlease manually find the correct URL and enter it.",
                'metrics': self.metrics.to_dict()
            }
    
    def _store_response(self, text: str):
        """Store agent response in chat history"""
        self.chat_history.append({
            'role': 'agent',
            'content': text,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def set_browser_controller(self, browser_controller):
        """Set the browser controller reference"""
        self.browser_controller = browser_controller
        if self.is_initialized:
            self.initialize(browser_controller)
    
    def get_chat_history(self) -> List[Dict]:
        """Get chat history"""
        return self.chat_history
    
    def clear_chat_history(self):
        """Clear chat history and reset workflow state"""
        self.chat_history.clear()
        self.current_phase = WorkflowPhase.IDLE
        self.ground_truth = None
        self.proposed_test_cases = []
        self.approved_test_cases = []
        self.generated_code = {}
        self.execution_results = []
    
    def get_agent_status(self) -> Dict:
        """Get the current status of the agent"""
        return {
            'initialized': self.is_initialized,
            'has_browser': self.browser_controller is not None,
            'current_phase': self.current_phase.value,
            'workflow_progress': {
                'has_ground_truth': self.ground_truth is not None,
                'proposed_test_cases': len(self.proposed_test_cases),
                'approved_test_cases': len(self.approved_test_cases),
                'generated_tests': len(self.generated_code),
                'executed_tests': len(self.execution_results)
            },
            'models': {
                'orchestration': 'meta-llama/Llama-3.1-8B-Instruct (free tier)',
                'vision': 'Qwen/Qwen2-VL-7B-Instruct (free tier)',
                'code_generation': 'bigcode/starcoder2-15b (free tier)'
            },
            'metrics': self.metrics.to_dict(),
            'tools_count': len(self.tools) if hasattr(self, 'tools') else 0,
            'chat_history_length': len(self.chat_history)
        }
    
    def get_metrics(self) -> Dict:
        """Get current metrics for real-time display"""
        return self.metrics.to_dict()
