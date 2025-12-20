"""
Flask Backend Server for Web Testing Agent
Implements REST API endpoints with Playwright integration and 4-phase workflow
"""
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import signal
import sys
import logging
from datetime import datetime, UTC

from browser.browser_control import BrowserController
from agents.llm_agent import LLMAgent
from observability.monitoring import setup_monitoring
from routes.chat_routes import create_chat_routes
from routes.browser_routes import create_browser_routes
from routes.test_routes import create_test_routes
from routes.metrics_routes import create_metrics_routes, set_llm_agent
from routes.report_routes import create_report_routes

# Fix for Playwright in some environments
#os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0" 

app = Flask(__name__)

# GLOBAL CORS: Handles OPTIONS requests automatically for all routes
CORS(app, resources={r"/api/*": {"origins": "*"}})

# GLOBAL URL SETTING: Handles trailing slashes (e.g., /api/chat vs /api/chat/)
app.url_map.strict_slashes = False

# Suppress Werkzeug logging for polling endpoints to keep console clean
werkzeug_logger = logging.getLogger('werkzeug')
class IgnorePollingFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        return '/api/metrics' not in msg and '/api/browser/state' not in msg

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
app.register_blueprint(create_test_routes(browser_controller))
app.register_blueprint(create_metrics_routes())
app.register_blueprint(create_report_routes())

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
        'timestamp': datetime.now(UTC).isoformat(),
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
    """Global error handler that won't crash on 404s"""
    app.logger.error(f'Error: {str(error)}')
    status_code = getattr(error, 'code', 500)
    return jsonify({
        'error': str(error),
        'timestamp': datetime.now(UTC).isoformat()
    }), status_code

# Graceful shutdown handler
_shutdown_in_progress = False

def shutdown_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global _shutdown_in_progress
    if _shutdown_in_progress:
        return 
    
    _shutdown_in_progress = True
    print('\n🛑 Shutting down gracefully...')
    
    try:
        browser_controller.close()
        print('✅ Browser closed')
    except Exception:
        pass
    
    print('👋 Goodbye!\n')
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

if __name__ == '__main__':
    print(f'Starting server on port {PORT}')
    
    is_debug = os.environ.get('FLASK_ENV') == 'development'
    # Only init browser in the main process (not the reloader)
    should_init = not is_debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    
    if should_init:
        try:
            browser_controller.initialize()
            llm_agent.initialize(browser_controller)
            print('🚀 System Ready: Browser and Agent initialized.')
        except Exception as e:
            print(f'⚠️ Startup Initialization Failed: {e}')
    
    # CRITICAL: threaded=False and processes=1 ensures Playwright stays on one thread
    app.run(host='0.0.0.0', port=PORT, debug=is_debug, threaded=False, processes=1)