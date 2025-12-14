/**
 * Browser Control Module
 * Manages Playwright browser instance for testing and interaction
 */

const { chromium } = require('playwright');

let browser = null;
let page = null;
let context = null;

/**
 * Initialize the browser instance
 */
async function initializeBrowser() {
  if (browser) {
    console.log('Browser already initialized');
    return;
  }

  try {
    browser = await chromium.launch({
      headless: process.env.HEADLESS !== 'false',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    });

    page = await context.newPage();
    console.log('Browser initialized successfully');
  } catch (error) {
    console.error('Failed to initialize browser:', error);
    throw error;
  }
}

/**
 * Close the browser instance
 */
async function closeBrowser() {
  if (browser) {
    await browser.close();
    browser = null;
    page = null;
    context = null;
    console.log('Browser closed');
  }
}

/**
 * Get current browser state including screenshot
 * @returns {Promise<Object>} Browser state
 */
async function getBrowserState() {
  if (!page) {
    return {
      screenshot: null,
      url: null,
      loading: false,
      error: 'Browser not initialized'
    };
  }

  try {
    const url = page.url();
    const screenshot = await page.screenshot({ 
      encoding: 'base64',
      fullPage: false 
    });

    return {
      screenshot: `data:image/png;base64,${screenshot}`,
      url,
      loading: false
    };
  } catch (error) {
    console.error('Error getting browser state:', error);
    return {
      screenshot: null,
      url: null,
      loading: false,
      error: error.message
    };
  }
}

/**
 * Navigate to a URL
 * @param {string} url - URL to navigate to
 * @returns {Promise<Object>} Navigation result
 */
async function navigateTo(url) {
  if (!page) {
    await initializeBrowser();
  }

  try {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
    return {
      success: true,
      url: page.url(),
      message: `Navigated to ${url}`
    };
  } catch (error) {
    console.error('Navigation error:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Perform an action on the page
 * @param {string} action - Action type (click, type, etc.)
 * @param {string} selector - Element selector
 * @param {string} value - Value for actions like type
 * @returns {Promise<Object>} Action result
 */
async function performAction(action, selector, value) {
  if (!page) {
    return { success: false, error: 'Browser not initialized' };
  }

  try {
    switch (action) {
      case 'click':
        await page.click(selector);
        break;
      case 'type':
        await page.fill(selector, value);
        break;
      case 'press':
        await page.press(selector, value);
        break;
      case 'select':
        await page.selectOption(selector, value);
        break;
      default:
        return { success: false, error: `Unknown action: ${action}` };
    }

    return {
      success: true,
      message: `Action ${action} performed successfully`
    };
  } catch (error) {
    console.error('Action error:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Get the current page instance
 * @returns {Page} Playwright page instance
 */
function getPage() {
  return page;
}

module.exports = {
  initializeBrowser,
  closeBrowser,
  getBrowserState,
  navigateTo,
  performAction,
  getPage
};
