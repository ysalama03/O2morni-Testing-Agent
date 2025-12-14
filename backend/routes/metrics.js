const express = require('express');
const router = express.Router();
const { getMetrics } = require('../observability/monitoring');

/**
 * GET /api/metrics
 * Get current test execution metrics
 */
router.get('/', async (req, res, next) => {
  try {
    const metrics = await getMetrics();
    res.json(metrics);
  } catch (error) {
    next(error);
  }
});

module.exports = router;
