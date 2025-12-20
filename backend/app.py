"""
Flask Backend Server for Web Testing Agent
Implements REST API endpoints with Playwright integration and 4-phase workflow
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import signal
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from browser.browser_control import BrowserController
from agents.llm_agent import LLMAgent
from observability.monitoring import setup_monitoring
from routes.chat_routes import create_chat_routes
from routes.browser_routes import create_browser_routes
from routes.test_routes import create_test_routes
from routes.metrics_routes import create_metrics_routes, set_llm_agent
from routes.report_routes import create_report_routes

app = Flask(__name__)
CORS(app)

# Suppress Werkzeug logging for polling endpoints
import logging
werkzeug_logger = logging.getLogger('werkzeug')

class IgnorePollingFilter(logging.Filter):
    def filter(self, record):
        # Suppress logs for polling endpoints
        return '/api/metrics/' not in record.getMessage() and '/api/browser/state' not in record.getMessage()

werkzeug_logger.addFilter(IgnorePollingFilter())

# Configuration
PORT = int(os.environ.get('PORT', 3001))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize components
browser_controller = BrowserController()
llm_agent = LLMAgent(browser_controller=browser_controller)

# Set agent reference in metrics routes for real-time metrics
set_llm_agent(llm_agent)

# Setup monitoring
setup_monitoring(app)

# Register blueprints
app.register_blueprint(create_chat_routes(llm_agent))
app.register_blueprint(create_browser_routes(browser_controller))
app.register_blueprint(create_test_routes(llm_agent))
app.register_blueprint(create_metrics_routes())
app.register_blueprint(create_report_routes(llm_agent))

# Serve static files
@app.route('/generated-tests/<path:filename>')
def serve_generated_tests(filename):
    """Serve generated test files"""
    tests_dir = os.path.join(os.path.dirname(BASE_DIR), 'generated_tests')
    return send_from_directory(tests_dir, filename)

@app.route('/reports/<path:filename>')
def serve_reports(filename):
    """Serve report files"""
    reports_dir = os.path.join(os.path.dirname(BASE_DIR), 'reports')
    return send_from_directory(reports_dir, filename)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'agent_initialized': llm_agent.is_initialized if llm_agent else False
    })

# Agent status endpoint
@app.route('/api/agent/status', methods=['GET'])
def agent_status():
    """Get LLM agent status including workflow phase"""
    try:
        if llm_agent:
            return jsonify(llm_agent.get_agent_status())
        return jsonify({'initialized': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handling
@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    app.logger.error(f'Error: {str(error)}')
    return jsonify({
        'error': str(error),
        'timestamp': datetime.utcnow().isoformat()
    }), getattr(error, 'status_code', 500)

# Graceful shutdown handler
_shutdown_in_progress = False

def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global _shutdown_in_progress
    
    if _shutdown_in_progress:
        return  # Prevent multiple shutdown attempts
    
    _shutdown_in_progress = True
    print('\n🛑 Shutting down gracefully...')
    
    # Suppress asyncio and playwright errors during shutdown
    logging.getLogger('asyncio').setLevel(logging.CRITICAL)
    logging.getLogger('playwright').setLevel(logging.CRITICAL)
    
    try:
        browser_controller.close()
        print('✅ Browser closed')
    except Exception:
        pass
    
    print('👋 Goodbye!\n')
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

if __name__ == '__main__':
    print(f'Starting server on port {PORT}')
    print(f'Environment: {os.environ.get("FLASK_ENV", "production")}')
    
    # In production mode (no reloader), initialize browser immediately
    # In debug mode, only initialize in the reloader child process (WERKZEUG_RUN_MAIN='true')
    is_debug = os.environ.get('FLASK_ENV') == 'development'
    should_init = not is_debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    
    if should_init:
        # Initialize browser on startup
        try:
            browser_controller.initialize()
            print('Browser initialized successfully')
            
            # Initialize LLM agent with browser controller
            try:
                llm_agent.initialize(browser_controller)
                print('LLM Agent initialized with smolagents')
            except Exception as e:
                print(f'LLM Agent initialization deferred: {e}')
                print('Agent will initialize on first request (requires HF_TOKEN env variable)')
                
        except Exception as e:
            print(f'Failed to initialize browser: {e}')
    else:
        print('Skipping browser initialization (waiting for reloader)')
    
    # Run Flask app
    # Disable threading and reloader to avoid Playwright cross-thread issues
    # Playwright's sync API uses greenlets which are thread-local
    # Flask's reloader runs in a separate thread, causing "cannot switch to a different thread" errors
    is_debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(
        host='0.0.0.0', 
        port=PORT, 
        debug=is_debug,
        use_reloader=False,  # Disable reloader to prevent threading issues with Playwright
        threaded=False  # Disable threading to fix Playwright cross-thread errors
    )
