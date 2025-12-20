# O2morni Testing Agent

A comprehensive web-based testing solution that combines LLM-powered test generation with human-in-the-loop interaction. This tool enables automated web testing with real-time browser control, test generation, execution, and observability.

**Built in a week** - A rapid prototype demonstrating the power of combining LLM capabilities with web automation for intelligent testing solutions.

## 🎯 Overview

This project provides a complete testing agent system with:

- **Frontend**: React-based UI for interactive testing
- **Backend**: Express server with LLM agent integration
- **Browser Control**: Playwright-powered browser automation
- **Test Generation**: AI-assisted test creation
- **Observability**: Real-time metrics and reporting

## 📁 Project Structure

```
web-testing-agent/
├── frontend/                    # React UI application
│   ├── public/                 # Static assets
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── ChatPanel.jsx   # Chat interface with LLM agent
│   │   │   ├── BrowserView.jsx # Live browser state viewer
│   │   │   ├── MetricsPanel.jsx # Test metrics dashboard
│   │   │   └── Dashboard.jsx   # Main application layout
│   │   ├── api.js             # API client for backend communication
│   │   ├── index.js           # Application entry point
│   │   └── index.css          # Global styles
│   └── package.json           # Frontend dependencies
│
├── backend/                    # Node.js/Express server
│   ├── routes/                # API route handlers
│   │   ├── chat.js           # LLM agent chat endpoints
│   │   ├── browser.js        # Browser control endpoints
│   │   ├── tests.js          # Test generation/execution endpoints
│   │   ├── metrics.js        # Metrics endpoints
│   │   └── reports.js        # Report endpoints
│   ├── agents/               # LLM agent logic
│   │   └── llmAgent.js       # Agent message processing
│   ├── browser/              # Browser automation
│   │   └── browserControl.js # Playwright browser management
│   ├── tests/                # Test management
│   │   ├── testGenerator.js  # Test file generation
│   │   └── testExecutor.js   # Test execution engine
│   ├── observability/        # Monitoring and reporting
│   │   ├── monitoring.js     # Metrics tracking
│   │   └── reporting.js      # Report management
│   ├── app.js                # Main application server
│   └── package.json          # Backend dependencies
│
├── generated_tests/           # AI-generated test files
│   └── README.md             # Test directory documentation
│
├── reports/                   # Test reports and screenshots
│   └── README.md             # Reports directory documentation
│
└── README.md                 # This file
```

## 🚀 Getting Started

### Prerequisites

- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Web-based-Testing-Agent
   ```

2. **Install backend dependencies**

   ```bash
   cd backend
   npm install
   ```

3. **Install frontend dependencies**

   ```bash
   cd ../frontend
   npm install
   ```

4. **Install Playwright browsers**
   ```bash
   cd ../backend
   npx playwright install
   ```

### Running the Application

1. **Start the backend server**

   ```bash
   cd backend
   npm start
   ```

   The backend will run on `http://localhost:3001`

2. **Start the frontend development server**

   ```bash
   cd frontend
   npm start
   ```

   The frontend will run on `http://localhost:3000`

3. **Access the application**
   Open your browser and navigate to `http://localhost:3000`

## 🎨 Features

### Frontend Components

- **ChatPanel**: Interactive chat interface for communicating with the LLM testing agent
- **BrowserView**: Real-time display of browser state with screenshots
- **MetricsPanel**: Live test execution metrics and error tracking
- **Dashboard**: Unified interface orchestrating all panels

### Backend Services

- **API Routes**: RESTful endpoints for all operations
- **LLM Agent**: Intelligent test generation and interaction
- **Browser Control**: Playwright-based browser automation
- **Test Generation**: Dynamic test file creation from specifications
- **Test Execution**: Automated test running and result collection
- **Observability**: Comprehensive metrics tracking and reporting

## 📡 API Endpoints

### Chat

- `POST /api/chat` - Send message to LLM agent
- `GET /api/chat/history` - Get chat history

### Browser

- `GET /api/browser/state` - Get current browser state with screenshot
- `POST /api/browser/navigate` - Navigate to URL
- `POST /api/browser/action` - Perform browser action (click, type, etc.)

### Tests

- `GET /api/tests` - List generated tests
- `POST /api/tests/generate` - Generate new test
- `POST /api/tests/execute` - Execute test

### Metrics & Reports

- `GET /api/metrics` - Get current metrics
- `GET /api/reports` - List test reports
- `GET /api/reports/:id` - Get specific report

## 🔧 Configuration

### Environment Variables

**Backend** (create `backend/.env`):

```env
PORT=3001
NODE_ENV=development
HEADLESS=false
```

**Frontend** (create `frontend/.env`):

```env
REACT_APP_API_URL=http://localhost:3001/api
```

## 🧪 Usage Examples

### Generate a Test

```javascript
// POST /api/tests/generate
{
  "config": {
    "testName": "loginTest",
    "url": "https://example.com/login",
    "actions": [
      { "type": "type", "selector": "#username", "value": "testuser" },
      { "type": "type", "selector": "#password", "value": "password123" },
      { "type": "click", "selector": "#login-button" }
    ],
    "assertions": [
      { "type": "url", "expected": "https://example.com/dashboard" }
    ]
  }
}
```

### Execute a Test

```javascript
// POST /api/tests/execute
{
  "testPath": "loginTest.spec.js",
  "options": {}
}
```

## 🛠️ Development

### Project Goals

- Provide a human-in-the-loop testing assistant
- Enable rapid test creation and execution
- Offer real-time visibility into test execution
- Support iterative test improvement

### Technology Stack

- **Frontend**: React, vanilla CSS
- **Backend**: Node.js, Express
- **Browser Automation**: Playwright
- **Test Framework**: Playwright Test

## 📝 License

MIT

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or feedback, please open an issue in the repository.
