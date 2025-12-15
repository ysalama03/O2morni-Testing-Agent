"""
Flask Backend Server for Web Testing Agent
Implements REST API endpoints with Playwright integration
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import signal
import sys
from datetime import datetime

from browser.browser_control import BrowserController
from agents.llm_agent import LLMAgent
from observability.monitoring import setup_monitoring
from routes.chat_routes import create_chat_routes
from routes.browser_routes import create_browser_routes
from routes.test_routes import create_test_routes
from routes.metrics_routes import create_metrics_routes
from routes.report_routes import create_report_routes

app = Flask(__name__)
CORS(app)

# Configuration
PORT = int(os.environ.get('PORT', 3001))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize components
browser_controller = BrowserController()
llm_agent = LLMAgent()

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
        'timestamp': datetime.utcnow().isoformat()
    })

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
def shutdown_handler(signum, frame):
    """Handle shutdown signals"""
    print(f'Signal {signum} received: closing browser and shutting down')
    browser_controller.close()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

if __name__ == '__main__':
    print(f'Starting server on port {PORT}')
    print(f'Environment: {os.environ.get("FLASK_ENV", "production")}')
    
    # Initialize browser on startup
    try:
        browser_controller.initialize()
        print('Browser initialized successfully')
    except Exception as e:
        print(f'Failed to initialize browser: {e}')
    
    # Run Flask app
    app.run(host='0.0.0.0', port=PORT, debug=os.environ.get('FLASK_ENV') == 'development')
