/**
 * Monitoring Module
 * Provides observability and metrics tracking
 */

let metrics = {
  testsRun: 0,
  testsPassed: 0,
  testsFailed: 0,
  executionTime: 0,
  coverage: 0,
  errors: [],
  startTime: Date.now()
};

/**
 * Initialize observability middleware
 * @param {Express} app - Express application instance
 */
function initializeObservability(app) {
  // Request logging middleware
  app.use((req, res, next) => {
    const start = Date.now();
    
    res.on('finish', () => {
      const duration = Date.now() - start;
      console.log(`${req.method} ${req.path} ${res.statusCode} - ${duration}ms`);
    });
    
    next();
  });

  console.log('Observability initialized');
}

/**
 * Get current metrics
 * @returns {Promise<Object>} Current metrics
 */
async function getMetrics() {
  const uptime = Date.now() - metrics.startTime;
  
  return {
    ...metrics,
    uptime,
    timestamp: new Date().toISOString()
  };
}

/**
 * Update metrics after test execution
 * @param {Object} testResult - Test execution result
 */
function updateMetrics(testResult) {
  metrics.testsRun++;
  
  if (testResult.success) {
    metrics.testsPassed++;
  } else {
    metrics.testsFailed++;
  }
  
  metrics.executionTime += testResult.executionTime || 0;
  
  if (testResult.error) {
    metrics.errors.push({
      message: testResult.error,
      timestamp: new Date().toISOString()
    });
    
    // Keep only last 10 errors
    if (metrics.errors.length > 10) {
      metrics.errors = metrics.errors.slice(-10);
    }
  }
}

/**
 * Reset metrics
 */
function resetMetrics() {
  metrics = {
    testsRun: 0,
    testsPassed: 0,
    testsFailed: 0,
    executionTime: 0,
    coverage: 0,
    errors: [],
    startTime: Date.now()
  };
}

/**
 * Log error
 * @param {string} message - Error message
 * @param {Error} error - Error object
 */
function logError(message, error) {
  console.error(message, error);
  
  metrics.errors.push({
    message: `${message}: ${error.message}`,
    timestamp: new Date().toISOString()
  });
  
  // Keep only last 10 errors
  if (metrics.errors.length > 10) {
    metrics.errors = metrics.errors.slice(-10);
  }
}

module.exports = {
  initializeObservability,
  getMetrics,
  updateMetrics,
  resetMetrics,
  logError
};
