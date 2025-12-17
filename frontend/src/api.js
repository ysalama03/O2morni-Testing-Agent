/**
 * API Client for Web-based Testing Agent
 * Handles all communication with the backend server
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

/**
 * Send a message to the LLM agent
 * @param {string} message - User message/command
 * @returns {Promise<Object>} Response from the agent
 */
export const sendMessage = async (message) => {
  const response = await fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Get current browser state including screenshot
 * @returns {Promise<Object>} Browser state data
 */
export const getBrowserState = async () => {
  const response = await fetch(`${API_BASE_URL}/browser/state`);

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Get current test execution metrics
 * @returns {Promise<Object>} Metrics data
 */
export const getMetrics = async () => {
  const response = await fetch(`${API_BASE_URL}/metrics`);

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Trigger test generation
 * @param {Object} config - Test generation configuration
 * @returns {Promise<Object>} Test generation result
 */
export const generateTests = async (config) => {
  const response = await fetch(`${API_BASE_URL}/tests/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Execute tests
 * @param {Object} testConfig - Test execution configuration
 * @returns {Promise<Object>} Test execution result
 */
export const executeTests = async (testConfig) => {
  const response = await fetch(`${API_BASE_URL}/tests/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(testConfig),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Get list of generated tests
 * @returns {Promise<Array>} List of test files
 */
export const getGeneratedTests = async () => {
  const response = await fetch(`${API_BASE_URL}/tests`);

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
};

/**
 * Get test reports
 * @returns {Promise<Array>} List of test reports
 */
export const getReports = async () => {
  const response = await fetch(`${API_BASE_URL}/reports`);

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
};
