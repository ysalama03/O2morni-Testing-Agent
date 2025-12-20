import pytest
from playwright.async_api import async_playwright

# Test the form_0 Required Field Validation
@pytest.mark.asyncio
async def test_form_0_required_field_validation(async_playwright):
    """
    Test that required fields show validation errors when empty.

    Steps:
    1. Leave required fields empty
    2. Click submit button

    Expected Results:
    - Validation errors are displayed
    - Form is not submitted
    """
    # Create a new browser instance
    async with async_playwright() as p:
        # Launch the browser and open the page
        browser = await p.firefox.launch()
        page = await browser.new_page()
        await page.goto("https://automationexercise.com/")

        # Step 1: Leave required fields empty
        # Wait for the form to load
        await page.wait_for_selector("#email_error")

        # Fill the form with empty values
        await page.fill("#email", "")
        await page.fill("input[name='password']", "")

        # Step 2: Click submit button
        # Wait for the submit button to load
        await page.wait_for_selector("button[name='Submit']", state="visible")
        # Click the submit button
        button = page.query_selector("button[name='Submit']")
        await button.click()

        # Step 3: Verify validation errors
        # Wait for the validation errors to load
        await page.wait_for_selector("#email_error", state="visible")

        # Assert validation errors are displayed
        validation_error = await page.query_selector("#email_error")
        assert validation_error.text_content() != "", "Validation error not displayed"

        # Assert form is not submitted
        assert page.url == "https://automationexercise.com/", "Form submitted successfully"

        # Take a screenshot at key verification point
        await page.screenshot(name="form_0_required_field_validation.png")

        # Close the browser
        await browser.close()