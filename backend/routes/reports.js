const express = require('express');
const router = express.Router();
const { getReportList, getReportById } = require('../observability/reporting');

/**
 * GET /api/reports
 * Get list of test reports
 */
router.get('/', async (req, res, next) => {
  try {
    const reports = await getReportList();
    res.json({ reports });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/reports/:id
 * Get a specific report by ID
 */
router.get('/:id', async (req, res, next) => {
  try {
    const { id } = req.params;
    const report = await getReportById(id);
    
    if (!report) {
      return res.status(404).json({ error: 'Report not found' });
    }

    res.json(report);
  } catch (error) {
    next(error);
  }
});

module.exports = router;
