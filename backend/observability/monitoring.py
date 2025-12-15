"""
Monitoring Module
Setup monitoring and logging for the application
"""

import logging
from datetime import datetime


def setup_monitoring(app):
    """Setup monitoring and logging"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add request logging
    @app.before_request
    def log_request():
        """Log incoming requests"""
        from flask import request
        app.logger.info(f'{request.method} {request.path}')
    
    @app.after_request
    def log_response(response):
        """Log outgoing responses"""
        from flask import request
        app.logger.info(f'{request.method} {request.path} - {response.status_code}')
        return response
    
    app.logger.info('Monitoring setup complete')
