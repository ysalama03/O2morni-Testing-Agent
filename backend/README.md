# Python Backend for Web Testing Agent

This is a Python implementation of the backend server using Flask, Playwright, and **smolagents** for AI-powered web testing.

## Architecture

The agent uses a **multi-model architecture** with smolagents:

| Model | Purpose | Provider |
|-------|---------|----------|
| **Llama-3.1-70B-Instruct** | Main orchestration and reasoning | Meta (via HuggingFace) |
| **Qwen2-VL-72B-Instruct** | Visual web reasoning with screenshots | Alibaba (via HuggingFace) |
| **DeepSeek-Coder-V2-Instruct** | Test code generation | DeepSeek (via HuggingFace) |

### Tools Available

The agent has access to these Playwright-based tools:
- `navigate_to_url` - Navigate to webpages
- `click_element` - Click on elements using CSS selectors
- `type_text` - Type text into input fields
- `get_element_text` - Extract text from elements
- `wait_for_element` - Wait for elements to appear
- `evaluate_javascript` - Execute JavaScript on the page
- `get_browser_state` - Get current page URL and state
- `scroll_page` - Scroll the page up/down
- `search_in_page` - Find text on the page
- `generate_test_code` - Generate Playwright test scripts

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
python -m playwright install chromium
```

5. Configure environment variables:
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your HuggingFace token
# Get your token from: https://huggingface.co/settings/tokens
```

## Running the Server

```bash
python app.py
```

The server will start on port 3001 by default.

## Environment Variables

- `HF_TOKEN`: HuggingFace API token (required for LLM models)
- `PORT`: Server port (default: 3001)
- `FLASK_ENV`: Environment mode (development/production)
- `HEADLESS`: Run browser in headless mode (default: true)

## API Endpoints

### Chat
- `POST /api/chat/` - Send a message to the agent
- `GET /api/chat/history` - Get chat history
- `GET /api/chat/status` - Get agent status and model info
- `POST /api/chat/initialize` - Initialize/reinitialize the agent
- `POST /api/chat/clear` - Clear chat history

### Browser
- `GET /api/browser/state` - Get current browser state
- `POST /api/browser/navigate` - Navigate to a URL
- `POST /api/browser/click` - Click an element
- `POST /api/browser/type` - Type text into an input
- `POST /api/browser/evaluate` - Execute JavaScript

### Tests
- `POST /api/tests/generate` - Generate a test
- `POST /api/tests/execute` - Execute a test
- `GET /api/tests/list` - List all tests

### Metrics
- `GET /api/metrics/` - Get current metrics
- `POST /api/metrics/reset` - Reset metrics

### Reports
- `GET /api/reports/list` - List all reports
- `POST /api/reports/generate` - Generate a report

### Health
- `GET /health` - Health check endpoint

## Project Structure

```
backend-python/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── browser/
│   ├── __init__.py
│   └── browser_control.py # Playwright browser controller
├── agents/
│   ├── __init__.py
│   └── llm_agent.py       # LLM agent for chat
├── routes/
│   ├── __init__.py
│   ├── chat_routes.py     # Chat endpoints
│   ├── browser_routes.py  # Browser control endpoints
│   ├── test_routes.py     # Test management endpoints
│   ├── metrics_routes.py  # Metrics endpoints
│   └── report_routes.py   # Report endpoints
└── observability/
    ├── __init__.py
    └── monitoring.py      # Logging and monitoring
```

## Features

- ✅ Flask REST API
- ✅ Playwright browser automation
- ✅ CORS support
- ✅ Error handling
- ✅ Logging and monitoring
- ✅ Graceful shutdown
- ✅ Browser screenshot capture
- ✅ Element interaction (click, type)
- ✅ JavaScript execution
- ✅ Chat history management
- ✅ Test generation (placeholder)
- ✅ Metrics tracking

## Notes

- The LLM agent currently uses rule-based responses. Integrate with OpenAI/Anthropic API for production use.
- Test generation and execution are placeholders and need full implementation.
- Browser runs in headless mode by default for better performance.
