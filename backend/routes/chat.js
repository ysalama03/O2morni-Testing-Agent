const express = require('express');
const router = express.Router();
const { processMessage } = require('../agents/llmAgent');

/**
 * POST /api/chat
 * Send a message to the LLM agent and receive a response
 */
router.post('/', async (req, res, next) => {
  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const response = await processMessage(message);
    
    res.json({
      message: response.text,
      actions: response.actions,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    next(error);
  }
});

/**
 * GET /api/chat/history
 * Get chat history
 */
router.get('/history', async (req, res, next) => {
  try {
    // This would retrieve chat history from a database or memory store
    res.json({
      history: [],
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;
