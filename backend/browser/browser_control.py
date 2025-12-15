"""
Browser Control Module
Manages Playwright browser instance for testing and interaction
"""

from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
import base64
import os
from typing import Optional, Dict


class BrowserController:
    """Controller for managing Playwright browser instances"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    def initialize(self):
        """Initialize the browser instance"""
        if self.browser:
            print('Browser already initialized')
            return
        
        try:
            self.playwright = sync_playwright().start()
            headless = os.environ.get('HEADLESS', 'true').lower() != 'false'
            
            self.browser = self.playwright.chromium.launch(
                headless=headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            self.context = self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            self.page = self.context.new_page()
            print('Browser initialized successfully')
        except Exception as e:
            print(f'Failed to initialize browser: {e}')
            raise
    
    def close(self):
        """Close the browser instance"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            print('Browser closed')
        except Exception as e:
            print(f'Error closing browser: {e}')
    
    def get_browser_state(self) -> Dict:
        """Get current browser state including screenshot"""
        if not self.page:
            return {
                'screenshot': None,
                'url': None,
                'loading': False,
                'error': 'Browser not initialized'
            }
        
        try:
            url = self.page.url
            screenshot_bytes = self.page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return {
                'screenshot': f'data:image/png;base64,{screenshot_b64}',
                'url': url,
                'loading': False
            }
        except Exception as e:
            print(f'Error getting browser state: {e}')
            return {
                'screenshot': None,
                'url': None,
                'loading': False,
                'error': str(e)
            }
    
    def navigate_to(self, url: str) -> Dict:
        """Navigate to a URL"""
        if not self.page:
            self.initialize()
        
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            return {
                'success': True,
                'url': self.page.url,
                'title': self.page.title()
            }
        except Exception as e:
            print(f'Error navigating to {url}: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def click_element(self, selector: str) -> Dict:
        """Click an element on the page"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            self.page.click(selector, timeout=5000)
            return {'success': True}
        except Exception as e:
            print(f'Error clicking element {selector}: {e}')
            return {'success': False, 'error': str(e)}
    
    def type_text(self, selector: str, text: str) -> Dict:
        """Type text into an input field"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            self.page.fill(selector, text, timeout=5000)
            return {'success': True}
        except Exception as e:
            print(f'Error typing into {selector}: {e}')
            return {'success': False, 'error': str(e)}
    
    def evaluate_script(self, script: str) -> Dict:
        """Execute JavaScript on the page"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            result = self.page.evaluate(script)
            return {'success': True, 'result': result}
        except Exception as e:
            print(f'Error evaluating script: {e}')
            return {'success': False, 'error': str(e)}
    
    def get_element_text(self, selector: str) -> Dict:
        """Get text content of an element"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            text = self.page.text_content(selector, timeout=5000)
            return {'success': True, 'text': text}
        except Exception as e:
            print(f'Error getting text from {selector}: {e}')
            return {'success': False, 'error': str(e)}
    
    def wait_for_selector(self, selector: str, timeout: int = 30000) -> Dict:
        """Wait for a selector to appear"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return {'success': True}
        except Exception as e:
            print(f'Error waiting for selector {selector}: {e}')
            return {'success': False, 'error': str(e)}
