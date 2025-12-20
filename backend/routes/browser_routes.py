"""
Browser Routes
Handle browser control endpoints
"""

from flask import Blueprint, request, jsonify
from datetime import datetime


def create_browser_routes(browser_controller):
    """Create browser routes blueprint"""
    blueprint = Blueprint('browser', __name__, url_prefix='/api/browser')
    
    @blueprint.route('/state', methods=['GET'])
    def get_state():
        """Get current browser state"""
        try:
            # Check if screenshot is requested via query parameter
            include_screenshot = request.args.get('screenshot', 'false').lower() == 'true'
            
            state = browser_controller.get_browser_state(include_screenshot=include_screenshot)
            return jsonify(state)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/navigate', methods=['POST'])
    def navigate():
        """Navigate to a URL"""
        try:
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return jsonify({'error': 'URL is required'}), 400
            
            result = browser_controller.navigate_to(url)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/click', methods=['POST'])
    def click():
        """Click an element"""
        try:
            data = request.get_json()
            selector = data.get('selector')
            
            if not selector:
                return jsonify({'error': 'Selector is required'}), 400
            
            result = browser_controller.click_element(selector)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/type', methods=['POST'])
    def type_text():
        """Type text into an input field"""
        try:
            data = request.get_json()
            selector = data.get('selector')
            text = data.get('text')
            
            if not selector or text is None:
                return jsonify({'error': 'Selector and text are required'}), 400
            
            result = browser_controller.type_text(selector, text)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/evaluate', methods=['POST'])
    def evaluate():
        """Execute JavaScript on the page"""
        try:
            data = request.get_json()
            script = data.get('script')
            
            if not script:
                return jsonify({'error': 'Script is required'}), 400
            
            result = browser_controller.evaluate_script(script)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return blueprint
