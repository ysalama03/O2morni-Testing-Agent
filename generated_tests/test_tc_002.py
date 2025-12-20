# Form 0 Required Field Validation Test
import pytest
from playwright.sync_api import sync_playwright

# Test function
@pytest.mark.asyncio
async def test_form_0_required_field_validation(async_playwright):
    """
    Test that required fields show validation errors when empty
    """
    # Create a new browser instance
    browser = await async_playwright.launch()

    # Create a new page
    page = await browser.new_page()

    # Navigate to the test URL
    await page.goto("https://automationexercise.com/")

    # Wait for the form to load
    await page.wait_for_selector("[data-testid='register-form']")

    # Leave required fields empty and fill in other fields
    # Leave name field empty
    await page.fill("[name='name']", "")

    # Leave last name field empty
    await page.fill("[name='last_name']", "")

    # Leave email field empty
    await page.fill("[name='email']", "")

    # Leave password field empty
    await page.fill("[name='password']", "")

    # Leave confirm password field empty
    await page.fill("[name='confirm_password']", "")

    # Click submit button
    await page.click("[data-testid='submit-button']")

    # Wait for validation errors to display
    await page.wait_for_selector("[data-testid='validation-errors']")

    # Assert validation errors are displayed
    validation_errors = await page.query_selector_all("[data-testid='validation-errors']")
    assert len(validation_errors) > 0, "No validation errors displayed"

    # Take a screenshot of the error message
    await page.screenshot(path="validation_errors.png")

    # Assert form is not submitted
    assert await page.query_selector("[data-testid='submit-button']") is not None, "Form submitted successfully"

    # Take a screenshot of the form
    await page.screenshot(path="form_not_submitted.png")

    # Close the browser
    await browser.close()