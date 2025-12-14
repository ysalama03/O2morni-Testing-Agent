/**
 * Test Executor Module
 * Executes generated tests and collects results
 */

const fs = require('fs').promises;
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

const GENERATED_TESTS_DIR = path.join(__dirname, '../../generated_tests');
const REPORTS_DIR = path.join(__dirname, '../../reports');

/**
 * Execute a test file
 * @param {string} testPath - Path to test file
 * @param {Object} options - Execution options
 * @returns {Promise<Object>} Execution result
 */
async function executeTest(testPath, options = {}) {
  try {
    // Ensure reports directory exists
    await fs.mkdir(REPORTS_DIR, { recursive: true });

    const fullPath = path.join(GENERATED_TESTS_DIR, testPath);
    
    // Check if test file exists
    try {
      await fs.access(fullPath);
    } catch (error) {
      return {
        success: false,
        error: `Test file not found: ${testPath}`
      };
    }

    const startTime = Date.now();
    
    // Execute the test using Playwright
    // In production, this would use proper test runner integration
    const command = `npx playwright test ${fullPath} --reporter=json`;
    
    let result;
    try {
      const { stdout, stderr } = await execAsync(command, {
        cwd: path.join(__dirname, '../..'),
        timeout: 60000
      });
      
      result = {
        success: true,
        output: stdout,
        errors: stderr
      };
    } catch (error) {
      result = {
        success: false,
        output: error.stdout || '',
        errors: error.stderr || error.message
      };
    }

    const executionTime = Date.now() - startTime;

    // Save report
    const reportId = `report-${Date.now()}`;
    const report = {
      id: reportId,
      testPath,
      timestamp: new Date().toISOString(),
      executionTime,
      ...result
    };

    await saveReport(report);

    return {
      ...result,
      executionTime,
      reportId
    };
  } catch (error) {
    console.error('Test execution error:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Save test report
 * @param {Object} report - Test report data
 */
async function saveReport(report) {
  const reportPath = path.join(REPORTS_DIR, `${report.id}.json`);
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2), 'utf8');
}

/**
 * Get list of generated tests
 * @returns {Promise<Array>} List of test files
 */
async function getTestList() {
  try {
    await fs.mkdir(GENERATED_TESTS_DIR, { recursive: true });
    const files = await fs.readdir(GENERATED_TESTS_DIR);
    
    const tests = files
      .filter(file => file.endsWith('.spec.js') || file.endsWith('.test.js'))
      .map(file => ({
        name: file,
        path: file
      }));

    return tests;
  } catch (error) {
    console.error('Error getting test list:', error);
    return [];
  }
}

module.exports = {
  executeTest,
  getTestList,
  saveReport
};
