/**
 * Test Generator Module
 * Generates automated tests based on user requirements
 */

const fs = require('fs').promises;
const path = require('path');

const GENERATED_TESTS_DIR = path.join(__dirname, '../../generated_tests');

/**
 * Generate a test file based on configuration
 * @param {Object} config - Test generation configuration
 * @returns {Promise<Object>} Generation result
 */
async function generateTest(config) {
  try {
    const {
      testName = 'generatedTest',
      url,
      actions = [],
      assertions = []
    } = config;

    // Ensure generated_tests directory exists
    await fs.mkdir(GENERATED_TESTS_DIR, { recursive: true });

    // Generate test code
    const testCode = generateTestCode(testName, url, actions, assertions);

    // Write test file
    const fileName = `${testName}.spec.js`;
    const filePath = path.join(GENERATED_TESTS_DIR, fileName);
    await fs.writeFile(filePath, testCode, 'utf8');

    return {
      success: true,
      fileName,
      filePath,
      message: `Test ${fileName} generated successfully`
    };
  } catch (error) {
    console.error('Test generation error:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Generate test code as a string
 * @param {string} testName - Name of the test
 * @param {string} url - URL to test
 * @param {Array} actions - List of actions to perform
 * @param {Array} assertions - List of assertions to check
 * @returns {string} Generated test code
 */
function generateTestCode(testName, url, actions, assertions) {
  // Sanitize inputs to prevent code injection
  const sanitizedTestName = sanitizeString(testName);
  const sanitizedUrl = sanitizeUrl(url);
  
  const code = `// Generated test: ${sanitizedTestName}
// Generated at: ${new Date().toISOString()}

const { test, expect } = require('@playwright/test');

test.describe('${sanitizedTestName}', () => {
  test('should execute test scenario', async ({ page }) => {
    // Navigate to the target URL
    await page.goto('${sanitizedUrl}');
    
    // Perform actions
${actions.map((action, index) => generateActionCode(action, index)).join('\n')}
    
    // Assertions
${assertions.map((assertion, index) => generateAssertionCode(assertion, index)).join('\n')}
  });
});
`;

  return code;
}

/**
 * Sanitize string to prevent code injection
 * @param {string} str - String to sanitize
 * @returns {string} Sanitized string
 */
function sanitizeString(str) {
  if (!str) return '';
  return str.replace(/['"\\]/g, '\\$&').replace(/\n/g, '\\n');
}

/**
 * Validate and sanitize URL
 * @param {string} url - URL to sanitize
 * @returns {string} Sanitized URL
 */
function sanitizeUrl(url) {
  if (!url) return 'about:blank';
  
  // Basic URL validation
  try {
    new URL(url);
    return url.replace(/['"\\]/g, '\\$&');
  } catch {
    return 'about:blank';
  }
}

/**
 * Generate code for a single action
 * @param {Object} action - Action configuration
 * @param {number} index - Action index
 * @returns {string} Action code
 */
function generateActionCode(action, index) {
  const { type, selector, value, options } = action;
  const sanitizedSelector = sanitizeString(selector || '');
  const sanitizedValue = sanitizeString(value || '');
  
  switch (type) {
    case 'click':
      return `    await page.click('${sanitizedSelector}');`;
    case 'type':
      return `    await page.fill('${sanitizedSelector}', '${sanitizedValue}');`;
    case 'press':
      return `    await page.press('${sanitizedSelector}', '${sanitizedValue}');`;
    case 'select':
      return `    await page.selectOption('${sanitizedSelector}', '${sanitizedValue}');`;
    case 'wait':
      return `    await page.waitForTimeout(${parseInt(value) || 1000});`;
    case 'waitForSelector':
      return `    await page.waitForSelector('${sanitizedSelector}');`;
    default:
      return `    // Unknown action type: ${type}`;
  }
}

/**
 * Generate code for a single assertion
 * @param {Object} assertion - Assertion configuration
 * @param {number} index - Assertion index
 * @returns {string} Assertion code
 */
function generateAssertionCode(assertion, index) {
  const { type, selector, expected } = assertion;
  const sanitizedSelector = sanitizeString(selector || '');
  const sanitizedExpected = sanitizeString(expected || '');
  
  switch (type) {
    case 'visible':
      return `    await expect(page.locator('${sanitizedSelector}')).toBeVisible();`;
    case 'text':
      return `    await expect(page.locator('${sanitizedSelector}')).toHaveText('${sanitizedExpected}');`;
    case 'value':
      return `    await expect(page.locator('${sanitizedSelector}')).toHaveValue('${sanitizedExpected}');`;
    case 'url':
      return `    expect(page.url()).toBe('${sanitizedExpected}');`;
    case 'title':
      return `    await expect(page).toHaveTitle('${sanitizedExpected}');`;
    default:
      return `    // Unknown assertion type: ${type}`;
  }
}

module.exports = {
  generateTest,
  generateTestCode
};
