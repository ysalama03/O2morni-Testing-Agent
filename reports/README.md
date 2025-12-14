# Test Reports

This directory contains test execution reports and screenshots generated during test runs.

## Structure

- `report-<timestamp>.json` - Test execution reports in JSON format
- `screenshot-<name>-<timestamp>.png` - Screenshots captured during tests

## Report Format

Each report contains:
- `id` - Unique report identifier
- `testPath` - Path to the executed test
- `timestamp` - Execution timestamp
- `executionTime` - Duration in milliseconds
- `success` - Whether the test passed
- `output` - Test output
- `errors` - Any errors encountered

## Cleanup

Old reports are automatically cleaned up after 7 days by default.
