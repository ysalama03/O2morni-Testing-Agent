const express = require('express');
const router = express.Router();
const { generateTest } = require('../tests/testGenerator');
const { executeTest, getTestList } = require('../tests/testExecutor');

/**
 * GET /api/tests
 * Get list of generated tests
 */
router.get('/', async (req, res, next) => {
  try {
    const tests = await getTestList();
    res.json({ tests });
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/tests/generate
 * Generate a new test based on configuration
 */
router.post('/generate', async (req, res, next) => {
  try {
    const { config } = req.body;

    if (!config) {
      return res.status(400).json({ error: 'Configuration is required' });
    }

    const result = await generateTest(config);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/tests/execute
 * Execute a test or test suite
 */
router.post('/execute', async (req, res, next) => {
  try {
    const { testPath, options } = req.body;

    if (!testPath) {
      return res.status(400).json({ error: 'Test path is required' });
    }

    const result = await executeTest(testPath, options);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

module.exports = router;
