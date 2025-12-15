"""
Chat Routes
Handle chat/messaging endpoints
"""

from flask import Blueprint, request, jsonify
from datetime import datetime


def create_chat_routes(llm_agent):
    """Create chat routes blueprint"""
    blueprint = Blueprint('chat', __name__, url_prefix='/api/chat')
    
    @blueprint.route('/', methods=['POST'])
    def send_message():
        """Send a message to the LLM agent and receive a response"""
        try:
            data = request.get_json()
            message = data.get('message')
            
            if not message:
                return jsonify({'error': 'Message is required'}), 400
            
            response = llm_agent.process_message(message)
            
            return jsonify({
                'message': response['text'],
                'actions': response['actions'],
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @blueprint.route('/history', methods=['GET'])
    def get_history():
        """Get chat history"""
        try:
            history = llm_agent.get_chat_history()
            return jsonify({
                'history': history,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return blueprint
