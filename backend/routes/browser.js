const express = require('express');
const router = express.Router();
const { getBrowserState, navigateTo, performAction } = require('../browser/browserControl');

/**
 * GET /api/browser/state
 * Get current browser state including screenshot
 */
router.get('/state', async (req, res, next) => {
  try {
    const state = await getBrowserState();
    res.json(state);
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/browser/navigate
 * Navigate to a URL
 */
router.post('/navigate', async (req, res, next) => {
  try {
    const { url } = req.body;

    if (!url) {
      return res.status(400).json({ error: 'URL is required' });
    }

    const result = await navigateTo(url);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

/**
 * POST /api/browser/action
 * Perform a browser action (click, type, etc.)
 */
router.post('/action', async (req, res, next) => {
  try {
    const { action, selector, value } = req.body;

    if (!action) {
      return res.status(400).json({ error: 'Action is required' });
    }

    const result = await performAction(action, selector, value);
    res.json(result);
  } catch (error) {
    next(error);
  }
});

module.exports = router;
