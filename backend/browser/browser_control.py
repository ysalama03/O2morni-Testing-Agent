"""
Browser Control Module
Manages Playwright browser instance for testing and interaction
"""

from datetime import datetime
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
        self._thread_id = None  # Track which thread owns the browser
    
    def is_healthy(self) -> bool:
        """Check if browser session is healthy and usable"""
        try:
            if not self.page or not self.browser:
                return False
            # Try a simple operation to check if browser is responsive
            self.page.url
            return True
        except Exception:
            return False
    
    def restart(self):
        """Restart the browser session"""
        print('Restarting browser session...')
        self.close()
        self.initialize()
        print('Browser restarted successfully')
        
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
                try:
                    self.page.close()
                except:
                    pass  # Suppress errors if already closed
                    
            if self.context:
                try:
                    self.context.close()
                except:
                    pass
                    
            if self.browser:
                try:
                    self.browser.close()
                except:
                    pass
                    
            if self.playwright:
                try:
                    self.playwright.stop()
                except:
                    pass
            
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
        except Exception:
            pass  # Silent cleanup during shutdown
    
    def get_browser_state(self) -> Dict:
        """Get current browser state (WITHOUT screenshot to avoid threading issues from polling)"""
        if not self.page:
            return {
                'screenshot': None,
                'url': None,
                'loading': False,
                'error': 'Browser not initialized'
            }
        
        try:
            # Try to get current URL - this is usually safe
            try:
                url = self.page.url
            except:
                url = None
            
            # Skip screenshot to avoid thread-switching errors during polling
            return {
                'screenshot': None,
                'url': url,
                'loading': False
            }
        except Exception as e:
            # Suppress thread-switching errors from polling endpoints
            if 'cannot switch to a different thread' not in str(e):
                print(f'Error getting browser state: {e}')
            return {
                'screenshot': None,
                'url': None,
                'loading': False
            }
    
    def capture_screenshot(self, name="step") -> str:
        """Saves screenshot to disk and returns a short text description."""
        if not self.page:
            return "Error: No active page."
        
        # Create directory if it doesn't exist
        path = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(path, exist_ok=True)
        
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = os.path.join(path, filename)
        
        # Save the file
        self.page.screenshot(path=filepath)
        
        # Convert to base64 ONLY for the frontend variable, NOT for the LLM return
        with open(filepath, "rb") as f:
            self.last_screenshot_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
            
        return f"Screenshot saved successfully to {filename}. The page is now visible."
    
    def navigate_to(self, url: str) -> Dict:
        """Navigate to a URL"""
        # Auto-recover if browser is unhealthy
        if not self.is_healthy():
            try:
                self.restart()
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Browser session crashed and could not restart: {e}',
                    'needs_restart': True
                }
        
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Capture screenshot after successful navigation
            screenshot = self.capture_screenshot()
            
            return {
                'success': True,
                'url': self.page.url,
                'title': self.page.title(),
                'screenshot': screenshot
            }
        except Exception as e:
            error_str = str(e)
            print(f'Error navigating to {url}: {e}')
            
            # Check for specific error types
            if 'ERR_NAME_NOT_RESOLVED' in error_str:
                return {
                    'success': False,
                    'error': error_str,
                    'error_type': 'dns_error',
                    'message': f"Could not find website '{url}'. The URL may be incorrect.",
                    'suggestions': [
                        'Check if the URL is spelled correctly',
                        'Try adding or removing "www."',
                        'Search on Google to find the correct URL'
                    ]
                }
            elif 'cannot switch to a different thread' in error_str:
                # Browser session corrupted, restart it
                try:
                    self.restart()
                    return {
                        'success': False,
                        'error': 'Browser session was corrupted and has been restarted. Please try again.',
                        'error_type': 'session_recovered'
                    }
                except Exception as restart_error:
                    return {
                        'success': False,
                        'error': f'Browser crashed: {restart_error}',
                        'error_type': 'crash'
                    }
            elif 'Timeout' in error_str:
                return {
                    'success': False,
                    'error': error_str,
                    'error_type': 'timeout',
                    'message': f"The website '{url}' took too long to respond."
                }
            else:
                return {
                    'success': False,
                    'error': error_str
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
