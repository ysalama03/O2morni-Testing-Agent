"""
Browser Control Module
Manages Playwright browser instance for testing and interaction
"""

from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
import base64
import os
import threading
from typing import Optional, Dict
from time import sleep


class BrowserController:
    """Controller for managing Playwright browser instances"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._thread_id = threading.get_ident()  # Track which thread owns the browser
        self._lock = threading.RLock()  # Reentrant lock to serialize browser access across threads
        self._initialized_thread = None  # Track which thread initialized the browser
        self._latest_screenshot = None  # Store latest screenshot for real-time frontend updates
        self._latest_screenshot_timestamp = None  # Track when screenshot was taken
    
    def is_healthy(self) -> bool:
        """Check if browser session is healthy and usable"""
        with self._lock:
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
        """Initialize the browser instance in the current thread"""
        if self.browser:
            # Check if we're in the same thread that initialized the browser
            current_thread = threading.get_ident()
            if self._initialized_thread == current_thread:
                print('Browser already initialized in this thread')
                return
            else:
                # Browser was initialized in a different thread, need to restart
                print(f'Browser was initialized in thread {self._initialized_thread}, current thread is {current_thread}. Restarting...')
                self.close()
        
        try:
            # Store the thread ID that initializes the browser
            self._initialized_thread = threading.get_ident()
            self._thread_id = self._initialized_thread
            
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
            print(f'Browser initialized successfully in thread {self._initialized_thread}')
        except Exception as e:
            print(f'Failed to initialize browser: {e}')
            self._initialized_thread = None
            raise
    
    def close(self):
        """Close the browser instance"""
        try:
            # Reset thread tracking
            self._initialized_thread = None
            self._thread_id = None
            
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
    
    def get_browser_state(self, include_screenshot: bool = False) -> Dict:
        """Get current browser state with optional screenshot"""
        if not self.page:
            return {
                'screenshot': None,
                'url': None,
                'loading': False,
                'error': 'Browser not initialized'
            }
        
        # Use lock to prevent threading issues
        with self._lock:
            try:
                # Try to get current URL - this is usually safe
                try:
                    url = self.page.url
                except:
                    url = None
                
                # Include screenshot if requested (but not too frequently to avoid threading issues)
                # Always return latest screenshot if available (for real-time updates during agent execution)
                screenshot = None
                if include_screenshot:
                    try:
                        screenshot = self.capture_screenshot(update_latest=False)  # Don't update during polling
                    except Exception as e:
                        # Suppress errors but don't fail the whole request
                        print(f'Error capturing screenshot: {e}')
                
                # If no new screenshot captured, return the latest one (from agent actions)
                if not screenshot and self._latest_screenshot:
                    screenshot = self._latest_screenshot
                
                return {
                    'screenshot': screenshot,
                    'url': url,
                    'loading': False
                }
            except Exception as e:
                # Suppress thread-switching errors from polling endpoints
                print(f'Error getting browser state: {e}')
                return {
                    'screenshot': None,
                    'url': None,
                    'loading': False
                }
    
    def capture_screenshot(self, full_page: bool = False, update_latest: bool = True) -> Optional[str]:
        """
        Capture a screenshot and return as base64 data URL
        This method acquires its own lock to be thread-safe
        
        Args:
            full_page: Whether to capture full page or just viewport
            update_latest: Whether to update the latest screenshot cache (for real-time frontend updates)
        """
        if not self.page:
            return None
        
        # Acquire lock to ensure thread safety
        with self._lock:
            try:
                screenshot_bytes = self.page.screenshot(full_page=full_page)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                screenshot_data_url = f'data:image/png;base64,{screenshot_b64}'
                
                # Update latest screenshot cache for real-time frontend updates
                if update_latest:
                    from datetime import datetime
                    self._latest_screenshot = screenshot_data_url
                    self._latest_screenshot_timestamp = datetime.now()
                
                return screenshot_data_url
            except Exception as e:
                print(f'Error capturing screenshot: {e}')
                return None
    
    def navigate_to(self, url: str) -> Dict:
        """Navigate to a URL"""
        # Use lock to prevent threading issues
        with self._lock:
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
                
                # Capture screenshot after successful navigation (update latest for real-time frontend updates)
                screenshot = self.capture_screenshot(update_latest=True)
                
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
        
        with self._lock:
            try:
                self.page.click(selector, timeout=5000)
                # Capture screenshot after click for real-time frontend updates
                sleep(0.3)  # Small delay to let page update
                screenshot = self.capture_screenshot(update_latest=True)
                return {
                    'success': True,
                    'screenshot': screenshot  # Include screenshot in response
                }
            except Exception as e:
                print(f'Error clicking element {selector}: {e}')
                return {'success': False, 'error': str(e)}
    
    def type_text(self, selector: str, text: str) -> Dict:
        """Type text into an input field"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        with self._lock:
            try:
                self.page.fill(selector, text, timeout=5000)
                # Capture screenshot after typing for real-time frontend updates
                sleep(0.2)  # Small delay to let input update
                screenshot = self.capture_screenshot(update_latest=True)
                return {
                    'success': True,
                    'screenshot': screenshot  # Include screenshot in response
                }
            except Exception as e:
                print(f'Error typing into {selector}: {e}')
                return {'success': False, 'error': str(e)}
    
    def evaluate_script(self, script: str) -> Dict:
        """Execute JavaScript on the page"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        with self._lock:
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
        
        with self._lock:
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
        
        with self._lock:
            try:
                self.page.wait_for_selector(selector, timeout=timeout)
                return {'success': True}
            except Exception as e:
                print(f'Error waiting for selector {selector}: {e}')
                return {'success': False, 'error': str(e)}
    
    def get_current_url(self) -> Optional[str]:
        """Safely get the current page URL"""
        if not self.page:
            return None
        
        with self._lock:
            try:
                return self.page.url
            except Exception as e:
                print(f'Error getting URL: {e}')
                return None
    
    def press_key(self, key: str) -> Dict:
        """Press a key on the keyboard"""
        if not self.page:
            return {'success': False, 'error': 'Browser not initialized'}
        
        with self._lock:
            try:
                self.page.keyboard.press(key)
                return {'success': True}
            except Exception as e:
                print(f'Error pressing key {key}: {e}')
                return {'success': False, 'error': str(e)}
