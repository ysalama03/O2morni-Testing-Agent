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
  const code = `// Generated test: ${testName}
// Generated at: ${new Date().toISOString()}

const { test, expect } = require('@playwright/test');

test.describe('${testName}', () => {
  test('should execute test scenario', async ({ page }) => {
    // Navigate to the target URL
    await page.goto('${url || 'about:blank'}');
    
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
 * Generate code for a single action
 * @param {Object} action - Action configuration
 * @param {number} index - Action index
 * @returns {string} Action code
 */
function generateActionCode(action, index) {
  const { type, selector, value, options } = action;
  
  switch (type) {
    case 'click':
      return `    await page.click('${selector}');`;
    case 'type':
      return `    await page.fill('${selector}', '${value}');`;
    case 'press':
      return `    await page.press('${selector}', '${value}');`;
    case 'select':
      return `    await page.selectOption('${selector}', '${value}');`;
    case 'wait':
      return `    await page.waitForTimeout(${value || 1000});`;
    case 'waitForSelector':
      return `    await page.waitForSelector('${selector}');`;
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
  
  switch (type) {
    case 'visible':
      return `    await expect(page.locator('${selector}')).toBeVisible();`;
    case 'text':
      return `    await expect(page.locator('${selector}')).toHaveText('${expected}');`;
    case 'value':
      return `    await expect(page.locator('${selector}')).toHaveValue('${expected}');`;
    case 'url':
      return `    expect(page.url()).toBe('${expected}');`;
    case 'title':
      return `    await expect(page).toHaveTitle('${expected}');`;
    default:
      return `    // Unknown assertion type: ${type}`;
  }
}

module.exports = {
  generateTest,
  generateTestCode
};
